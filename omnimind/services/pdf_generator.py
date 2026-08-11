"""
OmniMind AI — ReportLab Executive PDF Report Generator (Human-Readable Format)
"""
import os
import ast
import html
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger("omnimind.services.pdf_generator")

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("ReportLab package not found. Using text fallback for PDF generation.")


def _clean_output_to_readable_html(action: str, output: Any) -> str:
    """Transform raw Python dict strings or dict objects into clean executive HTML text."""
    parsed = output
    if isinstance(output, str):
        stripped = output.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
            try:
                parsed = ast.literal_eval(stripped)
            except Exception:
                parsed = output

    if isinstance(parsed, dict):
        lines = []

        # 1. Plan Output
        if "plan" in parsed and isinstance(parsed["plan"], list):
            lines.append("<b>Executive Plan Decomposed:</b>")
            for idx, item in enumerate(parsed["plan"], 1):
                if isinstance(item, dict):
                    desc = html.escape(item.get("description", str(item)))
                    agent = html.escape(item.get("agent_type", "worker")).upper()
                    lines.append(f"&nbsp;&nbsp;• <b>Step {idx} ({agent})</b>: {desc}")
                else:
                    lines.append(f"&nbsp;&nbsp;• <b>Step {idx}</b>: {html.escape(str(item))}")
            return "<br/>".join(lines)

        # 2. RAG Document Retrieval Output
        if "documents" in parsed and isinstance(parsed["documents"], list):
            lines.append("<b>Retrieved Enterprise Knowledge Base Excerpt:</b>")
            for doc in parsed["documents"]:
                if isinstance(doc, dict):
                    doc_id = html.escape(str(doc.get("id", "Document")))
                    content = html.escape(str(doc.get("content", "")).replace("\n", " "))
                    lines.append(f"&nbsp;&nbsp;• <b>Source ({doc_id})</b>: \"{content[:260]}...\"")
                else:
                    lines.append(f"&nbsp;&nbsp;• <b>Excerpt</b>: \"{html.escape(str(doc))[:260]}...\"")
            return "<br/>".join(lines)

        # 3. Reviewer Verification Output
        if "quality_score" in parsed or "is_approved" in parsed:
            score = parsed.get("quality_score", 1.0)
            approved = parsed.get("is_approved", True)
            feedback = html.escape(str(parsed.get("feedback", "Approved")))
            badge = "✅ <b>APPROVED</b> (High Confidence)" if approved else "⚠️ <b>REVISION NEEDED</b>"
            lines.append(f"<b>Verification Status:</b> {badge}")
            lines.append(f"<b>Quality Score:</b> {int(float(score) * 100)}%")
            lines.append(f"<b>Reviewer Feedback:</b> {feedback}")
            return "<br/>".join(lines)

        # 4. General dictionary keys
        for k, v in parsed.items():
            if k not in ("analysis", "raw") and v:
                val_str = html.escape(str(v))
                key_str = html.escape(k.replace("_", " ").title())
                lines.append(f"<b>{key_str}:</b> {val_str}")
        return "<br/>".join(lines) if lines else html.escape(str(output))

    elif isinstance(parsed, list):
        return "<br/>".join([f"• {html.escape(str(x))}" for x in parsed])

    return html.escape(str(output))


class WorkflowPdfReportGenerator:
    """Generates styled executive PDF reports from agent workflow execution outputs."""

    def __init__(self, output_dir: str = "./uploads"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_workflow_pdf(
        self,
        workflow_id: str,
        workflow_name: str,
        goal: str,
        execution_results: Dict[str, Any],
        user_name: str = "OmniMind User",
    ) -> str:
        """Build a formatted executive PDF report for a workflow run and save to disk."""
        filename = f"report_wf_{workflow_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        if not HAS_REPORTLAB:
            with open(filepath, "wb") as f:
                content = f"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n{goal}\n"
                f.write(content.encode("utf-8"))
            return filepath

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Custom Executive Typography & Palette
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=4,
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=12,
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )
        agent_header = ParagraphStyle(
            "AgentHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#0284c7"),
        )
        goal_box_style = ParagraphStyle(
            "GoalBox",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
        )

        story = []

        # ── 1. Document Header Banner ───────────────────────────────────────────────
        escaped_name = html.escape(workflow_name)
        escaped_goal = html.escape(goal)
        escaped_user = html.escape(user_name)
        generated_at = datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')

        story.append(Paragraph("OmniMind AI — Multi-Agent Executive Report", title_style))
        story.append(Paragraph(f"Workflow: <b>{escaped_name}</b> | ID: <font color='#0284c7'>{workflow_id[:8]}</font> | Generated: {generated_at}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0284c7"), spaceAfter=12))

        # ── 2. Objective & Goal Section ─────────────────────────────────────────────
        story.append(Paragraph("🎯 Workflow Objective & Goal", h2_style))
        
        goal_table = Table(
            [[Paragraph(f"\"{escaped_goal}\"", goal_box_style)]],
            colWidths=[540],
        )
        goal_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(goal_table)
        story.append(Spacer(1, 10))

        # ── 3. Executive Summary Briefing ───────────────────────────────────────────
        story.append(Paragraph("📋 Executive Summary & Key Findings", h2_style))
        summary_text = (
            f"This executive report details the automated execution results for goal <i>\"{escaped_goal[:120]}...\"</i>. "
            f"The OmniMind Autonomous Multi-Agent engine assigned tasks across specialized roles (Orchestrator, RAG Specialist, "
            f"Worker, and Reviewer), retrieved relevant enterprise documents from ChromaDB, executed reasoning steps, and verified "
            f"all compliance criteria with high confidence."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 8))

        # ── 4. Agent Step Results Table ─────────────────────────────────────────────
        story.append(Paragraph("🤖 Agent Task Breakdown & Outputs", h2_style))

        step_results = execution_results.get("step_results", {})
        table_data = [
            [
                Paragraph("<b>Task Node</b>", agent_header),
                Paragraph("<b>Assigned Agent</b>", agent_header),
                Paragraph("<b>Output & Human-Readable Action Summary</b>", agent_header),
            ]
        ]

        for task_key, details in step_results.items():
            agent_name = html.escape(str(details.get("agent", "Agent")))
            action_raw = str(details.get("action", "executed_task")).replace("_", " ").title()
            action = html.escape(action_raw)
            raw_output = details.get("output", details)
            
            clean_output_html = _clean_output_to_readable_html(action, raw_output)

            table_data.append([
                Paragraph(f"<b>{html.escape(task_key)}</b>", body_style),
                Paragraph(f"<b>{agent_name}</b>", body_style),
                Paragraph(f"<b>Action Executed:</b> {action}<br/><br/>{clean_output_html}", body_style),
            ])

        table = Table(table_data, colWidths=[110, 110, 320])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        story.append(Spacer(1, 14))

        # ── 5. Footer Sign-off ──────────────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
        story.append(Paragraph(f"Report generated by OmniMind Autonomous Multi-Agent SaaS Engine for <b>{escaped_user}</b>.", subtitle_style))

        # Build Document
        doc.build(story)
        logger.info(f"Generated executive PDF report: {filepath}")
        return filepath


# ──────────────────────────────────────────────────────────────────────────────
# ContractIQ — Branded Contract Analysis PDF Report Generator
# ──────────────────────────────────────────────────────────────────────────────

LEGAL_DISCLAIMER_TEXT = (
    "Disclaimer: ContractIQ is an AI-powered contract analysis tool and does not provide legal advice. "
    "Results are for informational purposes only. Consult a licensed attorney for official legal counsel."
)

_SEVERITY_COLORS = {
    "CRITICAL": "#dc2626",
    "HIGH":     "#ea580c",
    "MEDIUM":   "#d97706",
    "LOW":      "#16a34a",
}

_RISK_COLORS = {
    "CRITICAL": "#dc2626",
    "HIGH":     "#ea580c",
    "MODERATE": "#d97706",
    "LOW":      "#16a34a",
}


class ContractReportGenerator:
    """Generates branded ContractIQ PDF reports with risk gauge, red flags, and obligations."""

    def __init__(self, output_dir: str = "./uploads"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_contract_pdf(
        self,
        analysis_id: str,
        share_token: str,
        filename: str,
        analysis_data: dict,
        is_ocr: bool = False,
        page_count: int = 0,
    ) -> str:
        """Build and save a ContractIQ branded analysis PDF. Returns filepath."""
        safe_name  = f"contractiq_{analysis_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath   = os.path.join(self.output_dir, safe_name)

        if not HAS_REPORTLAB:
            with open(filepath, "wb") as f:
                f.write(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n")
            return filepath

        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=40, leftMargin=40,
            topMargin=40,   bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        # ── Typography Styles ──────────────────────────────────────────────────
        brand_title = ParagraphStyle("BrandTitle", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=22, textColor=colors.HexColor("#0f172a"),
            leading=26, spaceAfter=2)

        brand_sub = ParagraphStyle("BrandSub", parent=styles["Normal"],
            fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#64748b"),
            leading=12, spaceAfter=10)

        h2 = ParagraphStyle("H2", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=12, textColor=colors.HexColor("#1e293b"),
            leading=15, spaceBefore=14, spaceAfter=6)

        body = ParagraphStyle("Body", parent=styles["BodyText"],
            fontName="Helvetica", fontSize=9, textColor=colors.HexColor("#334155"),
            leading=13, spaceAfter=4)

        small = ParagraphStyle("Small", parent=styles["Normal"],
            fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#64748b"),
            leading=11)

        disclaimer_style = ParagraphStyle("Disclaimer", parent=styles["Normal"],
            fontName="Helvetica-Oblique", fontSize=7.5, textColor=colors.HexColor("#94a3b8"),
            leading=11)

        flag_body = ParagraphStyle("FlagBody", parent=styles["Normal"],
            fontName="Helvetica", fontSize=8.5, textColor=colors.HexColor("#1e293b"),
            leading=12)

        story = []

        # ── 1. Header Banner ───────────────────────────────────────────────────
        risk_level  = analysis_data.get("risk_level", "MODERATE")
        risk_score  = float(analysis_data.get("risk_score", 50))
        risk_color  = _RISK_COLORS.get(risk_level, "#d97706")
        contract_type = html.escape(analysis_data.get("contract_type", "Contract"))
        favors_party  = html.escape(analysis_data.get("favors_party", "Unknown"))
        generated_at  = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")

        story.append(Paragraph("ContractIQ", brand_title))
        story.append(Paragraph(
            f"AI-Powered Contract Analysis Report &nbsp;|&nbsp; Generated: {generated_at}",
            brand_sub
        ))
        story.append(HRFlowable(width="100%", thickness=3,
            color=colors.HexColor("#1e3a8a"), spaceAfter=12))

        # ── 2. Document Info Table ─────────────────────────────────────────────
        ocr_badge   = " &nbsp;<b>[OCR]</b>" if is_ocr else ""
        info_data   = [
            [Paragraph("<b>File</b>", flag_body),          Paragraph(html.escape(filename) + ocr_badge, flag_body)],
            [Paragraph("<b>Type</b>", flag_body),          Paragraph(contract_type, flag_body)],
            [Paragraph("<b>Favors</b>", flag_body),        Paragraph(favors_party, flag_body)],
            [Paragraph("<b>Pages</b>", flag_body),         Paragraph(str(page_count) if page_count else "N/A", flag_body)],
            [Paragraph("<b>Share Token</b>", flag_body),   Paragraph(share_token[:18] + "...", small)],
        ]
        info_table = Table(info_data, colWidths=[90, 280])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#ffffff")),
            ("BOX",        (0, 0), (-1, -1), 0.75, colors.HexColor("#e2e8f0")),
            ("INNERGRID",  (0, 0), (-1, -1), 0.5,  colors.HexColor("#e2e8f0")),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ]))

        # ── 3. Risk Score Gauge Box ────────────────────────────────────────────
        gauge_label = f"<font color='{risk_color}'><b>{risk_level} RISK</b></font>"
        gauge_score = f"<font color='{risk_color}'><b>{risk_score:.0f}</b></font>/100"

        gauge_style = ParagraphStyle("Gauge", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=28,
            textColor=colors.HexColor(risk_color), alignment=1)
        gauge_label_style = ParagraphStyle("GaugeLabel", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=11,
            textColor=colors.HexColor(risk_color), alignment=1)

        gauge_data = [[
            info_table,
            Table([
                [Paragraph(f"{risk_score:.0f}", gauge_style)],
                [Paragraph("RISK SCORE", gauge_label_style)],
                [Paragraph(f"● {risk_level} RISK", ParagraphStyle(
                    "RL", parent=styles["Normal"],
                    fontName="Helvetica-Bold", fontSize=9,
                    textColor=colors.HexColor(risk_color), alignment=1
                ))],
            ], colWidths=[150]),
        ]]
        gauge_table = Table(gauge_data, colWidths=[390, 150])
        gauge_table.setStyle(TableStyle([
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",   (1, 0), (1, -1),  "CENTER"),
            ("BOX",     (1, 0), (1, -1),  1.5, colors.HexColor(risk_color)),
            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#fafafa")),
            ("TOPPADDING",    (1, 0), (1, -1), 18),
            ("BOTTOMPADDING", (1, 0), (1, -1), 18),
        ]))
        story.append(gauge_table)
        story.append(Spacer(1, 12))

        # ── 4. Executive Summary ───────────────────────────────────────────────
        story.append(Paragraph("📋 Executive Summary", h2))
        exec_text = html.escape(analysis_data.get("executive_summary", "Analysis complete."))
        story.append(Paragraph(exec_text, body))
        story.append(Spacer(1, 6))

        # ── 5. Plain English Summary ───────────────────────────────────────────
        story.append(Paragraph("💬 What You're Agreeing To (Plain English)", h2))
        plain_text = html.escape(analysis_data.get("plain_english_summary", ""))
        story.append(Paragraph(plain_text, body))
        story.append(Spacer(1, 8))

        # ── 6. Red Flags Table ─────────────────────────────────────────────────
        red_flags = analysis_data.get("red_flags", [])
        if red_flags:
            story.append(Paragraph(f"🚩 Red Flag Clauses ({len(red_flags)} Found)", h2))

            flag_header = ParagraphStyle("FH", parent=styles["Normal"],
                fontName="Helvetica-Bold", fontSize=8.5, textColor=colors.HexColor("#1e293b"))

            flag_rows = [[
                Paragraph("<b>Severity</b>", flag_header),
                Paragraph("<b>Clause</b>", flag_header),
                Paragraph("<b>Why It's a Risk & What To Do</b>", flag_header),
            ]]

            for rf in red_flags:
                sev  = rf.get("severity", "MEDIUM").upper()
                sev_color = _SEVERITY_COLORS.get(sev, "#d97706")
                sev_text  = f"<font color='{sev_color}'><b>{sev}</b></font>"

                clause_title = html.escape(rf.get("clause_title", "Clause"))
                clause_text  = html.escape(rf.get("clause_text", "")[:180])
                explanation  = html.escape(rf.get("explanation", ""))
                recommend    = html.escape(rf.get("recommendation", ""))

                flag_rows.append([
                    Paragraph(sev_text, flag_body),
                    Paragraph(f"<b>{clause_title}</b><br/><i>{clause_text}...</i>", flag_body),
                    Paragraph(f"<b>Risk:</b> {explanation}<br/><b>Action:</b> {recommend}", flag_body),
                ])

            flag_table = Table(flag_rows, colWidths=[65, 180, 295])
            flag_table.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#fef2f2")),
                ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("BOX",           (0, 0), (-1, -1), 1, colors.HexColor("#fca5a5")),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
            ]))
            story.append(flag_table)
            story.append(Spacer(1, 10))

        # ── 7. Your Obligations ────────────────────────────────────────────────
        obligations = analysis_data.get("obligations", [])
        if obligations:
            story.append(Paragraph("📌 Your Obligations Under This Contract", h2))
            for i, obl in enumerate(obligations, 1):
                story.append(Paragraph(f"&nbsp;&nbsp;{i}. {html.escape(str(obl))}", body))
            story.append(Spacer(1, 10))

        # ── 8. Key Dates Table ─────────────────────────────────────────────────
        key_dates = analysis_data.get("key_dates", [])
        if key_dates:
            story.append(Paragraph("📅 Key Dates & Deadlines", h2))
            date_rows = [[
                Paragraph("<b>Event</b>", flag_body),
                Paragraph("<b>Timeline / Deadline</b>", flag_body),
            ]]
            for kd in key_dates:
                date_rows.append([
                    Paragraph(html.escape(kd.get("event", "")), flag_body),
                    Paragraph(html.escape(kd.get("timeline", "")), flag_body),
                ])
            date_table = Table(date_rows, colWidths=[240, 300])
            date_table.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#f0fdf4")),
                ("INNERGRID",     (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("BOX",           (0, 0), (-1, -1), 0.75, colors.HexColor("#bbf7d0")),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ]))
            story.append(date_table)
            story.append(Spacer(1, 14))

        # ── 9. Footer — Mandatory Legal Disclaimer (Guardrail 1) ──────────────
        story.append(HRFlowable(width="100%", thickness=0.5,
            color=colors.HexColor("#cbd5e1"), spaceAfter=6))
        story.append(Paragraph(
            f"<b>ContractIQ</b> &nbsp;|&nbsp; Powered by OmniMind AI &nbsp;|&nbsp; "
            f"Share Token: {share_token[:12]}...",
            small
        ))
        story.append(Spacer(1, 4))
        story.append(Paragraph(LEGAL_DISCLAIMER_TEXT, disclaimer_style))

        doc.build(story)
        logger.info(f"Generated ContractIQ PDF report: {filepath}")
        return filepath

