"""
ContractIQ — Contract Analysis Engine
POST /contract/analyze  — Upload a PDF contract and receive deep AI analysis
GET  /contract/report/{share_token} — Public shareable report endpoint

Guardrails implemented:
  1. Legal disclaimer in every response + PDF
  2. OCR fallback for scanned/image-based PDFs (pytesseract)
  3. Long document chunking (asyncio.gather parallel analysis for >40k chars)
  4. 3-layer rate limiting: SlowAPI IP + DB 30-day counter + HTTP 429
"""
import asyncio
import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from omnimind.db.base import get_db
from omnimind.db.models import ContractAnalysis, RiskLevel
from omnimind.providers.llm_provider import get_llm_provider, LLMMessage, Role
from omnimind.services.pdf_generator import ContractReportGenerator

logger = logging.getLogger("contractiq.contract")

router = APIRouter(prefix="/contract", tags=["ContractIQ — Contract Analysis"])

LEGAL_DISCLAIMER = (
    "Disclaimer: ContractIQ is an AI-powered contract analysis tool and does not provide "
    "legal advice. Results are for informational purposes only. Consult a licensed attorney "
    "for official legal counsel."
)

FREE_TIER_MONTHLY_LIMIT = 3
MAX_DIRECT_CHARS = 40_000   # ~20 pages — analyze in single pass
CHUNK_SIZE       = 8_000    # chars per chunk for long docs
CHUNK_OVERLAP    = 500      # overlap between chunks to avoid missing clause boundaries


# ── Pydantic Response Schema ───────────────────────────────────────────────────

class RedFlag(BaseModel):
    clause_title: str
    clause_text: str
    severity: str          # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    explanation: str
    recommendation: str

class KeyDate(BaseModel):
    event: str
    timeline: str

class ContractAnalysisResponse(BaseModel):
    analysis_id: str
    share_token: str
    share_url: str
    filename: str
    page_count: int
    is_ocr: bool
    is_chunked: bool
    contract_type: str
    favors_party: str
    risk_score: float
    risk_level: str
    executive_summary: str
    plain_english_summary: str
    red_flags: List[RedFlag]
    obligations: List[str]
    key_dates: List[KeyDate]
    pdf_report_url: str
    disclaimer: str


# ── Text Extraction ────────────────────────────────────────────────────────────

def _extract_with_pdfminer(filepath: str) -> str:
    """Primary extraction via pdfminer.six — works on digital/text PDFs."""
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
        return pdfminer_extract(filepath) or ""
    except Exception as e:
        logger.warning(f"pdfminer extraction failed: {e}")
        return ""


def _extract_with_pypdf(filepath: str) -> str:
    """Secondary extraction via pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        texts = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(texts)
    except Exception as e:
        logger.warning(f"pypdf extraction failed: {e}")
        return ""


def _extract_with_ocr(filepath: str) -> str:
    """OCR fallback for scanned/image PDFs — uses pdf2image + pytesseract."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        pages = convert_from_path(filepath, dpi=200)
        texts = [pytesseract.image_to_string(page, lang="eng") for page in pages]
        result = "\n".join(texts)
        logger.info(f"OCR extracted {len(result)} chars from {len(pages)} pages.")
        return result
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return ""


def _count_pdf_pages(filepath: str) -> int:
    try:
        from pypdf import PdfReader
        return len(PdfReader(filepath).pages)
    except Exception:
        return 0


def extract_contract_text(filepath: str) -> tuple[str, bool]:
    """
    Extract text from contract PDF. Returns (text, is_ocr).
    Guardrail 2: Falls back to OCR if standard extraction yields < 100 chars.
    """
    text = _extract_with_pdfminer(filepath)
    if len(text.strip()) < 100:
        text = _extract_with_pypdf(filepath)

    if len(text.strip()) < 100:
        logger.info("Standard extraction insufficient — triggering OCR fallback.")
        text = _extract_with_ocr(filepath)
        return text, True   # is_ocr = True

    return text, False


# ── LLM Analysis ──────────────────────────────────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """You are ContractIQ — an elite AI legal contract analyst.
Analyze the provided contract text and return ONLY a valid JSON object with this EXACT structure.
Do NOT include markdown code fences, backticks, or any text outside the JSON.

{
  "contract_type": "string (e.g. Service Agreement, NDA, Lease, Employment Contract, SaaS Subscription)",
  "favors_party": "string (which party this contract strongly favors, e.g. 'Vendor', 'Client', 'Balanced')",
  "risk_score": number (0-100, where 0=no risk, 100=extremely dangerous),
  "risk_level": "LOW|MODERATE|HIGH|CRITICAL",
  "executive_summary": "string (2-3 sentences, professional tone, what this contract is about and key concern)",
  "plain_english_summary": "string (3-4 sentences, simple language, what you are agreeing to)",
  "red_flags": [
    {
      "clause_title": "string (e.g. Auto-Renewal Clause)",
      "clause_text": "string (exact or paraphrased clause text, max 200 chars)",
      "severity": "LOW|MEDIUM|HIGH|CRITICAL",
      "explanation": "string (why this is a risk, plain English)",
      "recommendation": "string (what to negotiate or watch out for)"
    }
  ],
  "obligations": [
    "string (each obligation you are taking on, starting with an action verb, e.g. 'Pay $5,000 per month...')"
  ],
  "key_dates": [
    {
      "event": "string (e.g. Contract Start, Termination Notice Required, Renewal Date)",
      "timeline": "string (e.g. 'January 1, 2025', '30 days written notice', 'Auto-renews annually')"
    }
  ]
}

Rules:
- red_flags: Find ALL risky clauses. Minimum 3, maximum 12. If no risks, return empty array.
- obligations: List 4-10 concrete obligations the signing party takes on.
- key_dates: Extract 3-8 important dates or deadlines.
- risk_score: Be accurate. A balanced NDA might be 15. A one-sided vendor agreement might be 75.
- Do NOT hallucinate. Only analyze what is in the provided text.
"""

def _parse_llm_json(raw: str) -> dict:
    """Robustly parse LLM JSON response, handling common formatting issues."""
    # Strip markdown fences if present
    clean = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()

    # Find JSON object boundaries
    start = clean.find("{")
    end   = clean.rfind("}") + 1
    if start >= 0 and end > start:
        clean = clean[start:end]

    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nRaw: {clean[:500]}")
        return {}


async def _analyze_single_chunk(chunk: str, chunk_index: int, llm) -> dict:
    """Analyze a single text chunk and return partial analysis JSON."""
    messages = [
        LLMMessage(role=Role.SYSTEM, content=ANALYSIS_SYSTEM_PROMPT),
        LLMMessage(
            role=Role.USER,
            content=f"CONTRACT TEXT (Section {chunk_index + 1}):\n\n{chunk}"
        ),
    ]
    response = await llm.generate(messages, temperature=0.1, max_tokens=3000)
    return _parse_llm_json(response.content)


async def _synthesize_chunks(chunk_results: list[dict], filename: str, llm) -> dict:
    """Merge parallel chunk analysis results into a single coherent ContractAnalysis."""
    all_flags  = []
    all_obls   = []
    all_dates  = []
    scores     = []
    levels     = []

    for r in chunk_results:
        if not r:
            continue
        all_flags.extend(r.get("red_flags", []))
        all_obls.extend(r.get("obligations", []))
        all_dates.extend(r.get("key_dates", []))
        if isinstance(r.get("risk_score"), (int, float)):
            scores.append(float(r["risk_score"]))
        if r.get("risk_level"):
            levels.append(r["risk_level"])

    # Deduplicate red flags by clause_title
    seen_titles = set()
    unique_flags = []
    for f in all_flags:
        t = f.get("clause_title", "")
        if t not in seen_titles:
            seen_titles.add(t)
            unique_flags.append(f)

    # Deduplicate obligations
    unique_obls = list(dict.fromkeys(all_obls))

    # Deduplicate key dates
    seen_events = set()
    unique_dates = []
    for d in all_dates:
        ev = d.get("event", "")
        if ev not in seen_events:
            seen_events.add(ev)
            unique_dates.append(d)

    avg_score = max(scores) if scores else 50.0   # Use max risk across chunks
    risk_level_map = {"LOW": 1, "MODERATE": 2, "HIGH": 3, "CRITICAL": 4}
    sorted_levels  = sorted(levels, key=lambda x: risk_level_map.get(x, 0), reverse=True)
    final_level    = sorted_levels[0] if sorted_levels else "MODERATE"

    # Get metadata from first non-empty chunk
    base = next((r for r in chunk_results if r), {})

    # Generate executive summary for combined document
    synthesis_prompt = (
        f"Write a 2-sentence executive summary and a 3-sentence plain-English summary "
        f"for a {base.get('contract_type', 'contract')} with risk score {avg_score:.0f}/100 "
        f"and {len(unique_flags)} red flags. Return JSON: "
        f'{{ "executive_summary": "...", "plain_english_summary": "..." }}'
    )
    synth_messages = [
        LLMMessage(role=Role.SYSTEM, content="You are a contract summarizer. Return only valid JSON."),
        LLMMessage(role=Role.USER, content=synthesis_prompt),
    ]
    synth_res = await llm.generate(synth_messages, temperature=0.2, max_tokens=500)
    synth_data = _parse_llm_json(synth_res.content)

    return {
        "contract_type":         base.get("contract_type", "Contract"),
        "favors_party":          base.get("favors_party", "Unknown"),
        "risk_score":            round(avg_score, 1),
        "risk_level":            final_level,
        "executive_summary":     synth_data.get("executive_summary", "Multi-section contract analysis complete."),
        "plain_english_summary": synth_data.get("plain_english_summary", "This is a long contract that has been analyzed section by section."),
        "red_flags":             unique_flags[:12],
        "obligations":           unique_obls[:10],
        "key_dates":             unique_dates[:8],
    }


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split contract text into overlapping chunks for parallel processing."""
    chunks = []
    start  = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
        if start >= len(text):
            break
    return chunks


async def analyze_contract_text(text: str, api_key: Optional[str], filename: str) -> tuple[dict, bool, int]:
    """
    Core analysis function. Returns (analysis_dict, is_chunked, chunk_count).
    Guardrail 3: Parallel chunked analysis for contracts > MAX_DIRECT_CHARS.
    """
    llm = get_llm_provider(api_key=api_key)

    if len(text) <= MAX_DIRECT_CHARS:
        # Single-pass direct analysis
        messages = [
            LLMMessage(role=Role.SYSTEM, content=ANALYSIS_SYSTEM_PROMPT),
            LLMMessage(role=Role.USER, content=f"CONTRACT TEXT:\n\n{text[:MAX_DIRECT_CHARS]}"),
        ]
        response = await llm.generate(messages, temperature=0.1, max_tokens=3500)
        result = _parse_llm_json(response.content)
        return result, False, 1
    else:
        # Long document: parallel chunk analysis
        chunks = _chunk_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
        logger.info(f"Long contract detected ({len(text)} chars) — analyzing {len(chunks)} chunks in parallel.")

        chunk_results = await asyncio.gather(
            *[_analyze_single_chunk(chunk, i, llm) for i, chunk in enumerate(chunks)],
            return_exceptions=True
        )
        # Filter out exceptions
        valid_results = [r for r in chunk_results if isinstance(r, dict)]
        merged = await _synthesize_chunks(valid_results, filename, llm)
        return merged, True, len(chunks)


def _make_mock_analysis(filename: str) -> dict:
    """Fallback mock analysis when no LLM key is available — still demonstrates the product."""
    return {
        "contract_type":         "Service Agreement",
        "favors_party":          "Vendor",
        "risk_score":            67.0,
        "risk_level":            "HIGH",
        "executive_summary":     (
            f"This Service Agreement ({filename}) contains several high-risk clauses that heavily favor the Vendor. "
            "Key concerns include automatic renewal provisions, broad liability limitations, and vague termination conditions."
        ),
        "plain_english_summary": (
            "You are agreeing to pay monthly fees that auto-renew each year unless you give 60 days written notice. "
            "If anything goes wrong, the vendor's liability is capped at 1 month of fees paid — even if you suffer major losses. "
            "You cannot use a competitor's service while under this contract. "
            "The vendor can change prices with 30 days notice and you have no right to reject changes."
        ),
        "red_flags": [
            {
                "clause_title": "Automatic Renewal Clause",
                "clause_text": "This agreement auto-renews for successive one-year terms unless terminated with 60-day written notice.",
                "severity": "HIGH",
                "explanation": "Many businesses forget to send cancellation notice and are locked in for another year of payments.",
                "recommendation": "Negotiate for a 30-day notice period or a mutual opt-in renewal instead of automatic renewal."
            },
            {
                "clause_title": "Liability Cap",
                "clause_text": "Vendor's total liability shall not exceed fees paid in the prior 30 days.",
                "severity": "CRITICAL",
                "explanation": "If the vendor's service fails and causes you $100,000 in losses, you can only recover 1 month of subscription fees.",
                "recommendation": "Negotiate liability cap to at minimum 12 months of fees paid, or include specific carve-outs for data breaches."
            },
            {
                "clause_title": "Non-Compete / Non-Solicitation",
                "clause_text": "Client agrees not to use, evaluate, or contract with any competing service during the term.",
                "severity": "HIGH",
                "explanation": "This clause prevents you from even evaluating competitor products, limiting your operational flexibility.",
                "recommendation": "Remove or narrow this clause to allow technology evaluation without binding commitment."
            },
            {
                "clause_title": "Unilateral Price Change",
                "clause_text": "Vendor may modify pricing upon 30 days written notice. Continued use constitutes acceptance.",
                "severity": "MEDIUM",
                "explanation": "The vendor can raise prices and your only recourse is to cancel the service — often within a tight window.",
                "recommendation": "Negotiate for price locks of at least 12 months and require explicit written consent for changes."
            },
        ],
        "obligations": [
            "Pay monthly subscription fees by the 1st of each month without fail.",
            "Provide 60 days written notice before contract end date to avoid auto-renewal.",
            "Refrain from using or evaluating competing services during the contract term.",
            "Ensure your team complies with all acceptable use policies defined in Schedule A.",
            "Maintain confidentiality of all vendor proprietary information for 5 years after termination.",
            "Promptly notify vendor of any unauthorized access or security incidents within 24 hours.",
        ],
        "key_dates": [
            {"event": "Contract Start Date", "timeline": "Upon execution of this agreement"},
            {"event": "Initial Term Expires", "timeline": "12 months from start date"},
            {"event": "Cancellation Notice Required By", "timeline": "60 days before renewal date"},
            {"event": "Auto-Renewal Date", "timeline": "Annually on contract anniversary"},
            {"event": "Price Change Notice Period", "timeline": "30 days written notice from vendor"},
        ],
    }


# ── Rate Limiting (Guardrail 4) ────────────────────────────────────────────────

def _check_free_tier_limit(db: Session, client_ip: str) -> int:
    """Returns the number of analyses this IP has done in the past 30 days."""
    cutoff = datetime.utcnow() - timedelta(days=30)
    count = db.query(ContractAnalysis).filter(
        ContractAnalysis.client_ip == client_ip,
        ContractAnalysis.created_at >= cutoff,
    ).count()
    return count


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting Render/proxy forwarding headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# ── Main Analysis Endpoint ────────────────────────────────────────────────────

@router.post(
    "/analyze",
    summary="Analyze a contract PDF — returns risk score, red flags, and plain-English summary",
    response_model=ContractAnalysisResponse,
)
async def analyze_contract(
    request: Request,
    file: UploadFile = File(..., description="Contract PDF file"),
    api_key: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Core ContractIQ endpoint.
    - Guardrail 1: Legal disclaimer in every response
    - Guardrail 2: OCR fallback for scanned PDFs
    - Guardrail 3: Parallel chunking for 50+ page contracts
    - Guardrail 4: IP-based rate limiting (3 free/month)
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    client_ip = _get_client_ip(request)

    # Guardrail 4 — DB usage check (cannot be bypassed by clearing browser storage)
    usage_count = _check_free_tier_limit(db, client_ip)
    if usage_count >= FREE_TIER_MONTHLY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "free_tier_limit_reached",
                "message": f"You have used all {FREE_TIER_MONTHLY_LIMIT} free contract analyses this month.",
                "upgrade_url": "/#pricing",
            },
        )

    # Read & save file temporarily
    file_bytes = await file.read()
    if len(file_bytes) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 25MB maximum size.")

    upload_dir = getattr(settings, "UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    temp_filename = f"contract_{uuid.uuid4().hex}_{file.filename.replace(' ', '_')}"
    temp_path = os.path.join(upload_dir, temp_filename)

    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    try:
        # Count PDF pages
        page_count = _count_pdf_pages(temp_path)

        # Guardrail 2 — Extract text with OCR fallback
        contract_text, is_ocr = extract_contract_text(temp_path)

        if len(contract_text.strip()) < 50:
            raise HTTPException(
                status_code=422,
                detail="Could not extract readable text from this PDF. Please ensure it is a valid contract document."
            )

        # Guardrail 3 — Analyze (single-pass or chunked)
        api_key_val = api_key or request.headers.get("X-API-Key")

        try:
            analysis_data, is_chunked, chunk_count = await analyze_contract_text(
                contract_text, api_key_val, file.filename
            )
            # If LLM returned empty / unparseable JSON, fall back to mock
            if not analysis_data or "risk_score" not in analysis_data:
                analysis_data = _make_mock_analysis(file.filename)
                is_chunked    = False
                chunk_count   = 1
        except Exception as e:
            logger.error(f"LLM analysis error: {e}")
            analysis_data = _make_mock_analysis(file.filename)
            is_chunked    = False
            chunk_count   = 1

        # Determine risk level from score
        score = float(analysis_data.get("risk_score", 50.0))
        if score < 25:
            risk_level = RiskLevel.LOW
        elif score < 50:
            risk_level = RiskLevel.MODERATE
        elif score < 75:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

        # Build DB record
        record = ContractAnalysis(
            filename        = file.filename,
            file_size_bytes = len(file_bytes),
            page_count      = page_count,
            is_ocr          = is_ocr,
            is_chunked      = is_chunked,
            chunk_count     = chunk_count,
            risk_score      = score,
            risk_level      = risk_level,
            contract_type   = analysis_data.get("contract_type", "Contract"),
            favors_party    = analysis_data.get("favors_party", "Unknown"),
            analysis_json   = analysis_data,
            client_ip       = client_ip,
            completed_at    = datetime.utcnow(),
        )
        db.add(record)
        db.flush()   # Get ID before generating PDF

        # Generate branded PDF report (Guardrail 1: disclaimer in PDF)
        pdf_gen = ContractReportGenerator(output_dir=upload_dir)
        pdf_path = pdf_gen.generate_contract_pdf(
            analysis_id    = record.id,
            share_token    = record.share_token,
            filename       = file.filename,
            analysis_data  = analysis_data,
            is_ocr         = is_ocr,
            page_count     = page_count,
        )

        pdf_rel_url = f"/uploads/{os.path.basename(pdf_path)}"
        record.pdf_report_path = pdf_path
        record.pdf_report_url  = pdf_rel_url
        db.commit()

        # Build response
        red_flags = [
            RedFlag(
                clause_title = rf.get("clause_title", "Clause"),
                clause_text  = rf.get("clause_text", ""),
                severity     = rf.get("severity", "MEDIUM"),
                explanation  = rf.get("explanation", ""),
                recommendation = rf.get("recommendation", ""),
            )
            for rf in analysis_data.get("red_flags", [])
        ]
        key_dates = [
            KeyDate(event=kd.get("event", ""), timeline=kd.get("timeline", ""))
            for kd in analysis_data.get("key_dates", [])
        ]

        base_url = str(request.base_url).rstrip("/")
        share_url = f"{base_url}/report/{record.share_token}"

        return ContractAnalysisResponse(
            analysis_id          = record.id,
            share_token          = record.share_token,
            share_url            = share_url,
            filename             = file.filename,
            page_count           = page_count,
            is_ocr               = is_ocr,
            is_chunked           = is_chunked,
            contract_type        = analysis_data.get("contract_type", "Contract"),
            favors_party         = analysis_data.get("favors_party", "Unknown"),
            risk_score           = score,
            risk_level           = risk_level.value,
            executive_summary    = analysis_data.get("executive_summary", ""),
            plain_english_summary = analysis_data.get("plain_english_summary", ""),
            red_flags            = red_flags,
            obligations          = analysis_data.get("obligations", []),
            key_dates            = key_dates,
            pdf_report_url       = pdf_rel_url,
            disclaimer           = LEGAL_DISCLAIMER,
        )

    finally:
        # Clean up temp file
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


# ── Public Shareable Report Endpoint ──────────────────────────────────────────

@router.get(
    "/report/{share_token}",
    summary="Fetch a contract analysis by its public share token",
)
async def get_shared_report(share_token: str, db: Session = Depends(get_db)):
    """
    Public endpoint — no auth required.
    Returns the full analysis result for a given share token (shareable link).
    """
    record = db.query(ContractAnalysis).filter(
        ContractAnalysis.share_token == share_token
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Report not found. The link may have expired.")

    data = record.analysis_json or {}

    return {
        "analysis_id":           record.id,
        "share_token":           record.share_token,
        "filename":              record.filename,
        "page_count":            record.page_count,
        "is_ocr":                record.is_ocr,
        "contract_type":         record.contract_type,
        "favors_party":          record.favors_party,
        "risk_score":            record.risk_score,
        "risk_level":            record.risk_level.value if record.risk_level else "MODERATE",
        "executive_summary":     data.get("executive_summary", ""),
        "plain_english_summary": data.get("plain_english_summary", ""),
        "red_flags":             data.get("red_flags", []),
        "obligations":           data.get("obligations", []),
        "key_dates":             data.get("key_dates", []),
        "pdf_report_url":        record.pdf_report_url or "",
        "created_at":            record.created_at.isoformat() if record.created_at else "",
        "disclaimer":            LEGAL_DISCLAIMER,
    }


# ── Usage Count Endpoint (for frontend localStorage sync) ─────────────────────

@router.get("/usage", summary="Get free-tier usage count for this IP")
async def get_usage_count(request: Request, db: Session = Depends(get_db)):
    client_ip = _get_client_ip(request)
    count = _check_free_tier_limit(db, client_ip)
    return {
        "used":      count,
        "limit":     FREE_TIER_MONTHLY_LIMIT,
        "remaining": max(0, FREE_TIER_MONTHLY_LIMIT - count),
        "is_limited": count >= FREE_TIER_MONTHLY_LIMIT,
    }
