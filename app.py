# ==============================================================================
#  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
#  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
#  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
#  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
#  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
#  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
#
#  SENTINEL: SABS Digital Dominance Platform
#  Pakistan Art School War Room + Deep SEO Audit + Prescription Engine
#
#  PAGE 1 — THE WAR ROOM     : SABS vs NCA vs IVS vs BNU — live comparison
#  PAGE 2 — DEEP AUDIT       : SABS-specific technical SEO diagnostics
#  PAGE 3 — PRESCRIPTION ENGINE : Prioritised action plan with impact/effort matrix
#
#  Author  : Software Engineering Student, SABS University
#  Version : 1.0.0 — Assessment Build
# ==============================================================================

# ── Standard Library ──────────────────────────────────────────────────────────
import re
import time
import json
import textwrap
import warnings
from collections import Counter
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Third-Party ───────────────────────────────────────────────────────────────
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from bs4 import BeautifulSoup
import textstat
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.util import ngrams

warnings.filterwarnings("ignore")

# ── NLTK Bootstrap ────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _bootstrap_nltk():
    for corpus in ["stopwords", "punkt", "punkt_tab"]:
        try:
            if corpus == "stopwords":
                nltk.data.find("corpora/stopwords")
            elif corpus == "punkt":
                nltk.data.find("tokenizers/punkt")
            elif corpus == "punkt_tab":
                nltk.data.find("tokenizers/punkt_tab")
        except LookupError:
            try:
                nltk.download(corpus, quiet=True)
            except Exception:
                pass

_bootstrap_nltk()

# ==============================================================================
#  SECTION 1: PAGE CONFIG
# ==============================================================================
st.set_page_config(
    page_title="SENTINEL · SABS Digital Intelligence",
    page_icon="⚔",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==============================================================================
#  SECTION 2: UNIVERSITY ROSTER & COLOR SYSTEM
# ==============================================================================
# SEO RATIONALE: These are the four most prominent Art/Design universities
# in Pakistan. Benchmarking against direct competitors reveals where SABS
# gains or loses organic market share in search results.
UNIVERSITIES = {
    "SABS University":    "https://sabsu.edu.pk",
    "NCA Lahore":         "https://nca.edu.pk",
    "Indus Valley (IVS)": "https://ivs.edu.pk",
    "Beaconhouse (BNU)":  "https://bnu.edu.pk",
}

# Each university gets a distinct neon color for all charts
UNI_COLORS = {
    "SABS University":    "#00d4ff",   # Cyan  — the protagonist
    "NCA Lahore":         "#f97316",   # Orange
    "Indus Valley (IVS)": "#a855f7",   # Purple
    "Beaconhouse (BNU)":  "#22c55e",   # Green
}

UNI_SHORT = {
    "SABS University":    "SABS",
    "NCA Lahore":         "NCA",
    "Indus Valley (IVS)": "IVS",
    "Beaconhouse (BNU)":  "BNU",
}

RANK_MEDALS = ["🥇", "🥈", "🥉", "〔4〕"]

# ── Dynamic Naming & Styling Helpers ──────────────────────────────────────────
from urllib.parse import urlparse

def extract_uni_name(url: str, default_name: str) -> str:
    url_stripped = url.strip().rstrip("/")
    if not url_stripped:
        return default_name
    # Check if matches the default URL of the default_name
    if url_stripped == UNIVERSITIES.get(default_name, "").strip().rstrip("/"):
        return default_name
    # Check if matches any other default URL
    for name, def_url in UNIVERSITIES.items():
        if url_stripped == def_url.strip().rstrip("/"):
            return name
    # Otherwise extract cleanly from domain
    try:
        parsed = urlparse(url_stripped)
        netloc = parsed.netloc or parsed.path
        if netloc.startswith("www."):
            netloc = netloc[4:]
        # Remove common domain extensions
        for ext in [".edu.pk", ".org.pk", ".gov.pk", ".com.pk", ".edu", ".org", ".com", ".pk"]:
            if netloc.endswith(ext):
                netloc = netloc[:-len(ext)]
        # Split by dots or hyphens and capitalize
        parts = re.split(r"[\.\-]", netloc)
        return " ".join(p.upper() for p in parts if p)
    except Exception:
        return default_name

def get_uni_short(name: str) -> str:
    if name in UNI_SHORT:
        return UNI_SHORT[name]
    # Fallback: clean up display name to a short word
    parts = name.split()
    if len(parts) == 1:
        return parts[0][:10]
    return "".join(p[0] for p in parts if p)[:6].upper()

def get_uni_color(name: str) -> str:
    if name in UNI_COLORS:
        return UNI_COLORS[name]
    # Generate a consistent color based on hash of the name
    colors = ["#22c55e", "#06b6d4", "#a855f7", "#ec4899", "#f59e0b", "#3b82f6"]
    return colors[hash(name) % len(colors)]

# Shared Plotly layout theme
_PLY = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Share Tech Mono, monospace", color="#7a9bb5", size=11),
    margin=dict(l=20, r=20, t=40, b=20),
)

# ==============================================================================
#  SECTION 3: CUSTOM CSS INJECTION (Cyberpunk / Glassmorphism Aesthetic)
# ==============================================================================
CYBER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --bg-abyss:       #020509;
    --bg-deep:        #060d14;
    --bg-surface:     #0a1628;
    --bg-glass:       rgba(10,22,40,0.75);
    --border-neon:    rgba(0,212,255,0.35);
    --border-subtle:  rgba(0,212,255,0.12);
    --accent-cyan:    #00d4ff;
    --accent-green:   #00ff88;
    --accent-amber:   #ffb800;
    --accent-red:     #ff2d55;
    --accent-orange:  #f97316;
    --accent-purple:  #a855f7;
    --text-primary:   #e8f4f8;
    --text-secondary: #7a9bb5;
    --text-dim:       #3d5a73;
    --glow-cyan: 0 0 8px rgba(0,212,255,0.6), 0 0 20px rgba(0,212,255,0.25);
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: var(--bg-abyss) !important;
    color: var(--text-primary) !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed; inset: 0;
    background-image:
        linear-gradient(rgba(0,212,255,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.025) 1px, transparent 1px);
    background-size: 45px 45px;
    pointer-events: none; z-index: 0;
}
#MainMenu, footer,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stHeader"] { background: transparent !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#030810 0%,#050e1a 100%) !important;
    border-right: 1px solid var(--border-neon) !important;
    box-shadow: 4px 0 30px rgba(0,212,255,0.06) !important;
}
[data-testid="collapsedControl"] {
    background: rgba(3,8,16,0.85) !important;
    border: 1px solid var(--border-neon) !important;
    box-shadow: var(--glow-cyan) !important;
    border-radius: 8px !important;
    left: 15px !important;
    top: 15px !important;
    z-index: 999999 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 4px !important;
}
[data-testid="collapsedControl"] button {
    color: var(--accent-cyan) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: rgba(0,212,255,0.06) !important;
    border: 1px solid var(--border-neon) !important;
    border-radius: 6px !important;
    color: var(--accent-cyan) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
}
.stButton > button {
    background: linear-gradient(135deg,rgba(0,102,255,0.15),rgba(0,212,255,0.15)) !important;
    border: 1px solid var(--accent-cyan) !important;
    border-radius: 6px !important;
    color: var(--accent-cyan) !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    width: 100% !important;
    padding: 0.6rem 1rem !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg,rgba(0,102,255,0.35),rgba(0,212,255,0.35)) !important;
    box-shadow: var(--glow-cyan) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stMetric"] {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-neon) !important;
    border-radius: 10px !important;
    padding: 1.1rem 1.3rem !important;
    position: relative !important;
    backdrop-filter: blur(12px) !important;
    transition: all 0.3s ease !important;
    overflow: hidden !important;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg,transparent,var(--accent-cyan),transparent);
}
[data-testid="stMetric"]:hover {
    border-color: var(--accent-cyan) !important;
    box-shadow: var(--glow-cyan) !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.68rem !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Orbitron', monospace !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: var(--accent-cyan) !important;
    text-shadow: var(--glow-cyan) !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-neon) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
hr { border-color: var(--border-neon) !important; opacity:0.4 !important; }
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.25); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }
</style>
"""
st.markdown(CYBER_CSS, unsafe_allow_html=True)

# ==============================================================================
#  SECTION 4: HTML RENDER HELPER
#  CRITICAL FIX: textwrap.dedent() + strip() ensures the HTML tag always
#  starts at column 0, which Streamlit's CommonMark parser requires for
#  HTML block recognition. Multi-line f-strings inside Python functions
#  inherit indentation that would otherwise trigger code-block rendering.
# ==============================================================================
def _md(html: str) -> None:
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)

def _section_header(title: str):
    _md(f'<div style="font-family:\'Orbitron\',monospace;font-size:0.72rem;font-weight:700;color:#00d4ff;letter-spacing:0.25em;text-transform:uppercase;border-bottom:1px solid rgba(0,212,255,0.3);padding-bottom:0.4rem;margin-bottom:1rem;margin-top:0.5rem;">◈ {title}</div>')

def _page_header(title: str, subtitle: str):
    _md(f'<div style="font-family:\'Orbitron\',monospace;font-size:1.55rem;font-weight:900;color:#00d4ff;text-shadow:0 0 10px rgba(0,212,255,0.5);letter-spacing:0.08em;">{title}</div>')
    _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.76rem;color:#7a9bb5;letter-spacing:0.08em;margin-top:-0.4rem;margin-bottom:1.5rem;">{subtitle}</div>')


# ==============================================================================
#  SECTION 5: SCRAPING ENGINE
# ==============================================================================

def _scrape_url(url: str) -> dict:
    """
    Core scraper — NOT cached directly (called by cached wrappers).
    Fetches and parses a URL, returning a flat signal dictionary.
    All network errors produce {"error": <message>} for graceful degradation.
    """
    result = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html) SentinelBot/1.0",
        "Accept-Language": "en-US,en;q=0.9",
    }

    # ── TTFB Measurement ──────────────────────────────────────────────────────
    # SEO RATIONALE: Time to First Byte is a direct Core Web Vitals signal.
    # Google confirmed TTFB > 600ms reduces crawl budget allocation.
    try:
        t0 = time.perf_counter()
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True, verify=True)
        ttfb = (time.perf_counter() - t0) * 1000
        r.raise_for_status()
    except requests.exceptions.SSLError:
        try:
            t0 = time.perf_counter()
            r = requests.get(url, headers=headers, timeout=8, allow_redirects=True, verify=False)
            ttfb = (time.perf_counter() - t0) * 1000
            r.raise_for_status()
        except Exception as e:
            return {"error": f"SSL failure: {e}"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection refused / DNS failure: {e}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out (8s). Server may be offline."}
    except Exception as e:
        return {"error": f"Network error: {e}"}

    result["ttfb_ms"] = round(ttfb, 1)
    result["status_code"] = r.status_code
    result["content_size_kb"] = round(len(r.content) / 1024, 1)
    result["final_url"] = r.url

    # ── HTML Parsing ──────────────────────────────────────────────────────────
    try:
        soup = BeautifulSoup(r.text, "lxml")
    except Exception:
        soup = BeautifulSoup(r.text, "html.parser")

    # ── Meta Tags ─────────────────────────────────────────────────────────────
    # SEO RATIONALE: <title> is Google's #1 on-page ranking signal.
    # Meta description drives SERP click-through rate (indirect ranking factor).
    title_tag = soup.find("title")
    result["title"] = title_tag.get_text(strip=True) if title_tag else ""
    result["title_len"] = len(result["title"])

    desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    result["description"] = desc_tag.get("content", "").strip() if desc_tag else ""
    result["desc_len"] = len(result["description"])

    canonical_tag = soup.find("link", rel=lambda x: x and "canonical" in x)
    result["canonical"] = canonical_tag.get("href", "") if canonical_tag else ""

    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    result["robots_meta"] = robots_tag.get("content", "") if robots_tag else ""

    # ── Heading Hierarchy ─────────────────────────────────────────────────────
    # SEO RATIONALE: Single H1 = clear topical declaration to Googlebot.
    # H2/H3 build semantic sub-topic authority for long-tail keyword coverage.
    headings = []
    for lvl in ["h1","h2","h3"]:
        for tag in soup.find_all(lvl):
            txt = tag.get_text(strip=True)
            if txt:
                headings.append({"level": lvl.upper(), "text": txt})
    result["headings"] = headings
    result["h1_count"] = sum(1 for h in headings if h["level"]=="H1")
    result["h2_count"] = sum(1 for h in headings if h["level"]=="H2")
    result["h3_count"] = sum(1 for h in headings if h["level"]=="H3")

    # ── Images & Alt Text ─────────────────────────────────────────────────────
    # SEO RATIONALE: For an ART school, image alt text is critical.
    # Missing alt = invisible to Google Image Search (major traffic channel).
    imgs = soup.find_all("img")
    miss_alt = []
    for img in imgs:
        alt = img.get("alt")
        if alt is None or alt.strip() == "":
            src = img.get("src", img.get("data-src",""))
            miss_alt.append(urljoin(url, src) if src else "[no-src]")
    result["total_images"] = len(imgs)
    result["missing_alt_count"] = len(miss_alt)
    result["missing_alt_urls"] = miss_alt

    # ── Link Architecture ─────────────────────────────────────────────────────
    parsed_base = urlparse(url)
    il, el = 0, 0
    for a in soup.find_all("a", href=True):
        ph = urlparse(a["href"])
        if ph.netloc=="" or ph.netloc==parsed_base.netloc:
            il += 1
        elif ph.scheme in ("http","https"):
            el += 1
    result["internal_links"] = il
    result["external_links"] = el

    # ── OpenGraph & JSON-LD ───────────────────────────────────────────────────
    # SEO RATIONALE: JSON-LD unlocks Rich Results (+20-30% CTR).
    # OG tags control social preview quality — critical for Pakistani
    # institutions that rely heavily on WhatsApp/LinkedIn sharing.
    og = {}
    for m in soup.find_all("meta"):
        p = m.get("property","")
        if p.startswith("og:"):
            og[p] = m.get("content","")
    jld = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            jld.append(json.loads(s.string or "{}"))
        except Exception:
            pass
    result["og_tags"] = og
    result["has_og_title"]       = "og:title" in og
    result["has_og_description"] = "og:description" in og
    result["has_og_image"]       = "og:image" in og
    result["has_json_ld"]        = len(jld) > 0
    result["json_ld_types"]      = [b.get("@type","?") for b in jld if isinstance(b, dict)]

    # ── HTML5 Semantic Landmarks ──────────────────────────────────────────────
    # SEO RATIONALE: Landmarks help Googlebot identify content regions and
    # improve WCAG accessibility — both factor into Google's Page Experience.
    sem_check = ["header","main","nav","footer","article","section","aside"]
    sem_present = {t: bool(soup.find(t)) for t in sem_check}
    result["semantic_tags"]  = sem_present
    result["semantic_score"] = sum(sem_present.values())

    # ── Body Text ─────────────────────────────────────────────────────────────
    for noise in soup(["script","style","noscript","iframe","template"]):
        noise.decompose()
    raw = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True))
    result["raw_text"]   = raw
    result["word_count"] = len(re.findall(r"\w+", raw))

    # ── Readability ───────────────────────────────────────────────────────────
    # SEO RATIONALE: Flesch-Kincaid (target 60-70) correlates with lower
    # bounce rates — a key behavioural signal in Google's ranking algorithm.
    result["fk_reading_ease"] = None
    result["fk_grade_level"]  = None
    result["gunning_fog"]     = None
    if result["word_count"] > 30:
        try:
            result["fk_reading_ease"] = round(textstat.flesch_reading_ease(raw), 1)
            result["fk_grade_level"]  = round(textstat.flesch_kincaid_grade(raw), 1)
            result["gunning_fog"]     = round(textstat.gunning_fog(raw), 1)
        except Exception:
            pass

    # ── Sentiment ─────────────────────────────────────────────────────────────
    try:
        blob = TextBlob(raw[:5000])
        result["sentiment_polarity"]     = round(blob.sentiment.polarity, 4)
        result["sentiment_subjectivity"] = round(blob.sentiment.subjectivity, 4)
    except Exception:
        result["sentiment_polarity"]     = 0.0
        result["sentiment_subjectivity"] = 0.0

    # ── Keywords ──────────────────────────────────────────────────────────────
    result["keywords_df"] = _extract_keywords(raw)

    # ── Health Scores ─────────────────────────────────────────────────────────
    result["scores"]       = _compute_scores(result)
    result["global_score"] = min(100, round(
        sum(result["scores"].values()) / len(result["scores"]) * 100 / 25, 1))

    return result


@st.cache_data(ttl=300, show_spinner=False)
def fetch_single(url: str) -> dict:
    """Cached wrapper for single-URL scraping."""
    return _scrape_url(url)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_all_universities(urls_tuple: tuple) -> dict:
    """
    Parallel scrape of all 4 universities using ThreadPoolExecutor.
    Takes a tuple of (name, url) pairs (tuples are hashable for st.cache_data).
    Returns {name: parsed_data_dict}.

    SEO RATIONALE: Parallel fetching mirrors how Google's crawler dispatches
    multiple simultaneous requests. Results are cached for 5 minutes to avoid
    repeated server hits during the demo session.
    """
    results = {}

    def _fetch(name_url):
        name, url = name_url
        return name, _scrape_url(url)

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(_fetch, nu): nu[0] for nu in urls_tuple}
        for future in as_completed(futures, timeout=40):
            name = futures[future]
            try:
                n, data = future.result()
                results[n] = data
            except Exception as e:
                results[name] = {"error": str(e)}

    return results


def _extract_keywords(text: str, top_n: int = 15) -> pd.DataFrame:
    """Bigram/trigram frequency after stopword removal."""
    try:
        sw = set(stopwords.words("english"))
    except LookupError:
        sw = {"the","a","an","and","or","but","in","on","at","to","for","of","with",
              "is","are","was","were","be","been","have","has","had","do","does","did",
              "will","would","could","should","it","its","this","that","we","our","you"}
    tokens = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", text) if w.lower() not in sw]
    combined = (Counter(" ".join(g) for g in ngrams(tokens,2)) +
                Counter(" ".join(g) for g in ngrams(tokens,3)))
    top = combined.most_common(top_n)
    if not top:
        return pd.DataFrame(columns=["Keyword","Frequency"])
    df = pd.DataFrame(top, columns=["Keyword","Frequency"])
    df["Keyword"] = df["Keyword"].str.title()
    return df


def _compute_scores(r: dict) -> dict:
    """
    Four-pillar score system (0–25 each), used for the radar chart and
    global health KPI. Each pillar maps to a concrete Google ranking factor.
    """
    s = {"Meta Health":0, "DOM Structure":0, "Accessibility":0, "Content Quality":0}

    # Meta Health — title + description length compliance
    mp = 0
    if r.get("title"):
        mp += 8
        mp += 5 if 50 <= r["title_len"] <= 60 else 2
    if r.get("description"):
        mp += 7
        mp += 5 if 150 <= r["desc_len"] <= 160 else 2
    s["Meta Health"] = min(25, mp)

    # DOM Structure — heading hierarchy + semantic HTML
    dp = 0
    h1c = r.get("h1_count", 0)
    if h1c == 1: dp += 10
    elif h1c > 1: dp += 2
    if r.get("h2_count",0) >= 2: dp += 6
    if r.get("h3_count",0) >= 1: dp += 3
    dp += min(6, r.get("semantic_score",0))
    s["DOM Structure"] = min(25, dp)

    # Accessibility — alt text coverage + internal links
    ap = 0
    ti = r.get("total_images",0)
    ma = r.get("missing_alt_count",0)
    ap += 15 if ti == 0 else round((1 - ma/ti) * 15)
    il = r.get("internal_links",0)
    ap += 10 if il >= 10 else (5 if il >= 3 else 0)
    s["Accessibility"] = min(25, ap)

    # Content Quality — word count + readability + schema + OG
    cp = 0
    wc = r.get("word_count",0)
    cp += 8 if wc >= 800 else (4 if wc >= 300 else (2 if wc >= 100 else 0))
    fk = r.get("fk_reading_ease")
    if fk is not None:
        cp += 7 if 50 <= fk <= 70 else (4 if fk > 70 else 2)
    if r.get("has_json_ld"): cp += 5
    if r.get("has_og_title") and r.get("has_og_description"): cp += 5
    s["Content Quality"] = min(25, cp)

    return s


# ==============================================================================
#  SECTION 6: PRESCRIPTION ENGINE — ACTION PLAN GENERATOR
# ==============================================================================

def generate_prescriptions(d: dict, name: str = "SABS University") -> list:
    """
    Analyse SABS audit data and generate a prioritised list of action items.
    Each item has impact (1-10) and effort (1-10) scores used to plot the
    Impact/Effort matrix and the 30-day action plan.

    QUADRANT LOGIC:
    ┌──────────────────┬──────────────────┐
    │  QUICK WINS      │  MAJOR PROJECTS  │  ← High Impact
    │ (effort ≤ 4)     │ (effort > 4)     │
    ├──────────────────┼──────────────────┤
    │  FILL-INS        │  AVOID           │  ← Low Impact
    │ (effort ≤ 4)     │ (effort > 4)     │
    └──────────────────┴──────────────────┘
    """
    items = []

    def _add(title, desc, action, rationale, impact, effort, category, fix_time, gain):
        items.append({
            "title": title, "description": desc, "action": action,
            "rationale": rationale, "impact": impact, "effort": effort,
            "category": category, "fix_time": fix_time, "gain": gain,
            "quadrant": (
                "⚡ Quick Win"       if impact >= 6 and effort <= 4 else
                "🏗️ Major Project"  if impact >= 6 and effort > 4  else
                "📋 Fill-In"        if impact < 6  and effort <= 4 else
                "❌ Deprioritise"
            )
        })

    # Retrieve dynamic URL
    uni_url = d.get("final_url") or UNIVERSITIES.get(name, "https://www.example.com")
    short_name = get_uni_short(name)

    # ── CRITICAL ──────────────────────────────────────────────────────────────
    if "noindex" in d.get("robots_meta","").lower():
        _add("Remove NOINDEX Directive",
             "A noindex tag is blocking Google from indexing the site entirely. Zero organic visibility.",
             "Remove or replace <meta name='robots' content='noindex'> with 'index,follow'.",
             "noindex = 0 organic traffic regardless of all other optimisations. Highest priority fix in SEO.",
             10, 1, "🚨 Critical", "10 min", "Restores 100% of lost organic traffic")

    # ── META TAGS ─────────────────────────────────────────────────────────────
    tl = d.get("title_len", 0)
    title_val = d.get("title", "")
    if tl == 0:
        _add("Add Missing <title> Tag",
             "No title tag found. Google auto-generates a poor replacement. This is the #1 on-page ranking factor.",
             f"Add <title>{name} — Official Homepage</title> (50–60 chars).",
             "The <title> tag directly determines which keywords a page ranks for in Google.",
             10, 1, "📋 Meta Tags", "20 min", "Estimated +25–40% organic visibility")
    elif tl < 50:
        _add(f"Expand Title Tag ({tl} → 50–60 chars)",
             f"Current title '{title_val[:45]}' is only {tl} chars. Short titles waste SERP real estate.",
             "Expand the title to include your primary keyword naturally within 50–60 characters.",
             "Google allocates 580px of SERP space for titles. Short titles leave keyword potential unused.",
             7, 1, "📋 Meta Tags", "15 min", "Estimated +8–15% CTR improvement")
    elif tl > 60:
        _add(f"Shorten Title Tag ({tl} → 50–60 chars)",
             f"Title is {tl} chars — Google truncates at ~60, showing '...' in SERPs and cutting your message.",
             "Rewrite title to fit within 50–60 characters. Move the primary keyword to the start.",
             "Truncated titles reduce CTR as users cannot read the full proposition.",
             6, 1, "📋 Meta Tags", "15 min", "Cleaner SERP display, estimated +5% CTR")

    dl = d.get("desc_len", 0)
    desc_val = d.get("description", "")
    if dl == 0:
        _add("Write Meta Description",
             "No meta description found. Google generates its own snippet — usually irrelevant to search intent.",
             f"Add <meta name='description' content='...'> with a compelling 150–160 char summary for {short_name} including a call-to-action.",
             "Meta descriptions are the 'free ad copy' in Google SERPs. They directly drive click-through rate.",
             9, 1, "📋 Meta Tags", "20 min", "Estimated +15–25% CTR improvement")
    elif dl < 150:
        _add(f"Expand Meta Description ({dl} → 150–160 chars)",
             f"Description is only {dl} chars — leaving SERP preview space empty and reducing appeal.",
             f"Expand to 150–160 chars with: what {short_name} offers, why choose {short_name}, and a call-to-action.",
             "A well-crafted 155-char description acts as free ad copy, increasing qualified click-throughs.",
             7, 1, "📋 Meta Tags", "15 min", "Estimated +8–12% CTR improvement")
    elif dl > 160:
        _add(f"Shorten Meta Description ({dl} → 150–160 chars)",
             f"At {dl} chars, the description is truncated in SERPs with '...' cutting the message.",
             "Trim to under 160 chars. Keep the most compelling content and CTA within the first 155 chars.",
             "Truncated descriptions waste the limited persuasion space Google provides in search results.",
             5, 1, "📋 Meta Tags", "10 min", "Cleaner SERP snippet")

    # ── CANONICAL ─────────────────────────────────────────────────────────────
    if not d.get("canonical"):
        _add("Add Canonical URL Tag",
             "No canonical tag found. Google may split PageRank between www vs non-www and http vs https versions.",
             f"Add <link rel='canonical' href='{uni_url}'> inside <head> on every page.",
             "Canonical tags consolidate duplicate content signals and prevent PageRank dilution across URL variants.",
             8, 2, "🔧 Technical SEO", "30 min", "Consolidates split link equity")

    # ── HEADINGS ──────────────────────────────────────────────────────────────
    h1c = d.get("h1_count", 0)
    if h1c == 0:
        _add("Add Single H1 Tag",
             "No H1 found. Googlebot cannot identify the page's primary topic without it.",
             f"Add exactly ONE H1 containing your primary keyword: e.g., <h1>{name} — Official Portal</h1>.",
             "The H1 is the page's topical declaration. It directly tells Google's ranking algorithm the primary subject.",
             10, 1, "🏗️ DOM Structure", "20 min", "Estimated +20–35% keyword relevancy signal")
    elif h1c > 1:
        _add(f"Remove {h1c-1} Duplicate H1(s)",
             f"{h1c} H1 tags found. Multiple H1s dilute topical focus and confuse Google's content model.",
             f"Keep only the most important H1. Convert the remaining {h1c-1} to H2 or H3 tags.",
             "Google treats the H1 as the page's primary entity. Multiple H1s prevent clear topical authority.",
             8, 2, "🏗️ DOM Structure", "1 hour", "Clearer topical signal to Googlebot")

    if d.get("h2_count", 0) < 2:
        _add(f"Add H2 Subheadings (found: {d.get('h2_count',0)})",
             "Fewer than 2 H2 tags. H2s create the document outline and build sub-topic keyword signals.",
             "Add H2 headings for primary sections — with target keywords.",
             "H2/H3 tags expand topical coverage, helping the page rank for long-tail queries beyond the primary keyword.",
             6, 3, "🏗️ DOM Structure", "2 hours", "Estimated +10–20% long-tail keyword visibility")

    # ── SCHEMA ────────────────────────────────────────────────────────────────
    if not d.get("has_json_ld"):
        _add("Implement JSON-LD Schema Markup",
             f"No structured data found. {short_name} is ineligible for Rich Results (programme cards, FAQ boxes) in Google.",
             "Add JSON-LD for: EducationalOrganization, CollegeOrUniversity, Course, and FAQPage (admissions questions).",
             "JSON-LD enables Rich Results in Google SERPs, increasing SERP real estate by 3× and driving 20–30% higher CTR.",
             8, 5, "⚙️ Schema Markup", "1 day", "Rich Results eligibility (+20–30% CTR)")

    # ── SOCIAL ────────────────────────────────────────────────────────────────
    if not d.get("has_og_title"):
        _add("Add OpenGraph Meta Tags (og:title, og:description, og:image)",
             f"No OG tags found. {short_name} page shares on WhatsApp, LinkedIn, and social networks show blank previews.",
             f"Add og:title, og:description (155 chars), og:image (campus photo), and og:url to every page.",
             "Visual sharing is highly critical for branding. Every blank preview share is a lost referral visit.",
             7, 2, "📱 Social Media", "2 hours", "Professional social previews — 3× higher share engagement")
    elif not d.get("has_og_image"):
        _add("Add og:image Tag",
             "og:title and description present but no preview image. Social shares appear blank.",
             f"Add <meta property='og:image' content='{uni_url}/campus-hero.jpg'> inside <head>.",
             "A visual preview image is especially critical for campus branding and social sharing appeal.",
             6, 1, "📱 Social Media", "30 min", "3× higher social share engagement")

    # ── ACCESSIBILITY ─────────────────────────────────────────────────────────
    miss = d.get("missing_alt_count", 0)
    total_i = max(d.get("total_images",1), 1)
    if miss > 0:
        pct = round(miss / total_i * 100)
        imp = min(9, 5 + miss // 5)
        eff = min(7, 2 + miss // 15)
        _add(f"Add Alt Text to {miss} Image(s) ({pct}% uncovered)",
             f"{miss} of {total_i} images lack alt attributes, making them invisible to search crawlers.",
             f"Add descriptive alt text to all {miss} flagged images. Include keywords: e.g., alt='{short_name} student portfolio work'.",
             "Alt text is how Google indexes images. Missing alt = invisible in Google Image Search, which is a major organic traffic channel.",
             imp, eff, "♿ Accessibility", f"{'4 hrs' if miss<20 else '1–2 days'}", "Unlocks Google Image Search traffic for media content")

    # ── CONTENT ───────────────────────────────────────────────────────────────
    wc = d.get("word_count", 0)
    if wc < 300:
        _add(f"Dramatically Expand Content ({wc:,} → 800+ words)",
             f"Only {wc:,} words found. Thin content is a primary cause of poor rankings. Google's Helpful Content System penalises this.",
             "Add comprehensive pages about: Programs offered, Faculty profiles, Achievements, Admissions, and Campus life.",
             "Pages with 800+ words rank 2–3 positions higher than thin pages. Comprehensive content signals topical authority to Google.",
             9, 8, "📝 Content", "1 week", "Estimated +30–50% ranking positions")
    elif wc < 800:
        _add(f"Expand Content Depth ({wc:,} → 800+ words)",
             f"At {wc:,} words, content is below the threshold associated with strong competitive rankings.",
             "Expand with: campus details, course outcomes, faculty expertise, and student life information.",
             "Long-form content (800+ words) ranks for 2× more keywords than short pages, expanding organic visibility.",
             7, 6, "📝 Content", "3 days", "Estimated +15–25% keyword coverage")

    fk = d.get("fk_reading_ease")
    if fk is not None and fk < 50:
        _add(f"Simplify Writing Style (FK Ease: {fk} → 60+)",
             f"Content scores {fk}/100 on Flesch-Kincaid — expert/academic difficulty. General visitors disengage.",
             "Use shorter sentences (15-20 words), simpler vocabulary, active voice. Target Grade 8–9 reading level.",
             "High readability correlates with lower bounce rates and higher dwell time — indirect ranking signals.",
             6, 7, "📝 Content", "3–5 days", "Estimated 15–25% bounce rate reduction")

    # ── PERFORMANCE ───────────────────────────────────────────────────────────
    ttfb = d.get("ttfb_ms", 0)
    if ttfb > 600:
        _add(f"Optimise Server TTFB ({ttfb:.0f}ms → <200ms)",
             f"TTFB of {ttfb:.0f}ms is classified 'Poor' by Google Core Web Vitals — 3× above the acceptable threshold.",
             "Upgrade hosting, enable server caching, implement CDN (Cloudflare free tier), enable GZIP compression.",
             "TTFB is a direct Core Web Vitals signal. Poor TTFB reduces Googlebot crawl budget.",
             9, 9, "⚡ Performance", "1–2 weeks", "Estimated +2–3 ranking positions")
    elif ttfb > 200:
        _add(f"Improve Server TTFB ({ttfb:.0f}ms → <200ms)",
             f"TTFB of {ttfb:.0f}ms is in 'Needs Improvement' range. Faster server = better UX = better rankings.",
             "Enable server-side caching, compress images, enable Gzip, consider Cloudflare CDN.",
             "Even 100ms TTFB improvement correlates with measurable user engagement gains.",
             7, 7, "⚡ Performance", "3–5 days", "Improved Core Web Vitals score")

    # ── HTML5 SEMANTICS ───────────────────────────────────────────────────────
    sem = d.get("semantic_score", 0)
    sem_tags = d.get("semantic_tags", {})
    if sem < 5:
        miss_sem = [f"<{t}>" for t, p in sem_tags.items() if not p]
        _add(f"Add HTML5 Semantic Landmarks ({sem}/7 present)",
             f"Missing: {', '.join(miss_sem)}. These help Googlebot identify page regions and improve accessibility.",
             f"Wrap page regions with missing semantic elements. No design changes required — HTML structure only.",
             "HTML5 landmarks improve crawler comprehension and accessibility.",
             5, 3, "🏗️ DOM Structure", "2 hours", "Better Googlebot page comprehension")

    # ── LINK ARCHITECTURE ─────────────────────────────────────────────────────
    il = d.get("internal_links", 0)
    if il < 10:
        _add(f"Build Internal Link Structure ({il} → 10+ links)",
             f"Only {il} internal links found. PageRank cannot flow through the site — important pages receive no link equity.",
             "Add contextual links from homepage to other primary site sections.",
             "Internal links distribute PageRank and help Googlebot discover all pages.",
             7, 5, "🔗 Link Architecture", "1 day", "Better PageRank distribution across all pages")

    # Sort: highest impact first, then lowest effort (quick wins bubble up)
    items.sort(key=lambda x: (-x["impact"], x["effort"]))
    return items


# ==============================================================================
#  SECTION 6.5: PDF REPORT GENERATION
# ==============================================================================

def generate_pdf_report(all_data: dict, url_map: dict) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return b""

    class SentinelPDF(FPDF):
        def header(self):
            # Cyberpunk Sentinel page background/header
            self.set_fill_color(2, 5, 9) # var(--bg-abyss)
            self.rect(0, 0, 210, 297, "F")
            
            # Header text
            self.set_font("Courier", "B", 10)
            self.set_text_color(0, 212, 255) # #00d4ff
            self.cell(0, 10, "⚔ SENTINEL DIGITAL DOMINANCE REPORT", border=0, ln=1, align="L")
            self.set_draw_color(0, 212, 255)
            self.line(10, 18, 200, 18)
            self.ln(5)
            
        def footer(self):
            self.set_y(-15)
            self.set_font("Courier", "I", 8)
            self.set_text_color(122, 155, 181)
            self.cell(0, 10, f"SENTINEL v1.0 | Page {self.page_no()}/{{nb}}", align="C")

    pdf = SentinelPDF()
    pdf.alias_nb_pages()
    pdf.set_margins(15, 25, 15)
    pdf.add_page()
    
    # Cover / Header Details
    pdf.set_font("Courier", "B", 20)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 15, "SEO TELEMETRY REPORT", ln=1, align="L")
    
    pdf.set_font("Courier", "", 10)
    pdf.set_text_color(232, 244, 248) # text-primary
    
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(0, 8, f"CRAWL DATE/TIME: {timestamp} (PKT)", ln=1)
    
    # Target URLs
    pdf.ln(5)
    pdf.set_font("Courier", "B", 12)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 8, "TARGET ROSTER:", ln=1)
    pdf.set_font("Courier", "", 10)
    pdf.set_text_color(232, 244, 248)
    for name, url in url_map.items():
        pdf.cell(0, 6, f"- {name}: {url}", ln=1)
        
    pdf.ln(10)
    
    # Competitor League Table
    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 8, "1. DIGITAL DOMINANCE LEAGUE TABLE", ln=1)
    pdf.line(15, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Table headers
    pdf.set_font("Courier", "B", 9)
    pdf.set_text_color(122, 155, 181)
    pdf.cell(15, 6, "RANK", 1, 0, "C")
    pdf.cell(60, 6, "UNIVERSITY", 1, 0, "L")
    pdf.cell(20, 6, "SCORE", 1, 0, "C")
    pdf.cell(20, 6, "TTFB", 1, 0, "C")
    pdf.cell(60, 6, "PILLAR SCORES (META/STR/ACC/CON)", 1, 1, "C")
    
    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(232, 244, 248)
    
    # Build dataframe for rank
    rows = []
    for name, d in all_data.items():
        if "error" in d:
            rows.append((name, 0, "OFFLINE", 0, 0, 0, 0))
        else:
            sc = d.get("scores", {})
            rows.append((
                name,
                d.get("global_score", 0),
                f"{d.get('ttfb_ms', 0):.0f}ms",
                sc.get("Meta Health", 0),
                sc.get("DOM Structure", 0),
                sc.get("Accessibility", 0),
                sc.get("Content Quality", 0)
            ))
            
    # Sort by score descending
    rows.sort(key=lambda x: -x[1])
    for rank, (name, score, ttfb, meta, struct, access, content) in enumerate(rows, 1):
        pdf.cell(15, 6, f"#{rank}", 1, 0, "C")
        pdf.cell(60, 6, name[:30], 1, 0, "L")
        pdf.cell(20, 6, f"{score}/100", 1, 0, "C")
        pdf.cell(20, 6, ttfb, 1, 0, "C")
        pdf.cell(60, 6, f"{meta}/25 | {struct}/25 | {access}/25 | {content}/25", 1, 1, "C")
        
    pdf.ln(10)
    
    # Audit details for primary protagonist
    primary_name = list(url_map.keys())[0] if url_map else "SABS University"
    primary_data = all_data.get(primary_name, {})
    
    pdf.set_font("Courier", "B", 14)
    pdf.set_text_color(0, 212, 255)
    pdf.cell(0, 8, f"2. DEEP AUDIT: {primary_name.upper()}", ln=1)
    pdf.line(15, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    if "error" in primary_data:
        pdf.set_font("Courier", "", 10)
        pdf.set_text_color(255, 45, 85)
        pdf.cell(0, 8, f"Crawl Error: {primary_data['error']}", ln=1)
    else:
        pdf.set_font("Courier", "B", 10)
        pdf.set_text_color(122, 155, 181)
        pdf.cell(80, 6, "METRIC", 1, 0, "L")
        pdf.cell(100, 6, "VALUE / STAT", 1, 1, "L")
        
        pdf.set_font("Courier", "", 10)
        pdf.set_text_color(232, 244, 248)
        
        kpis = [
            ("Global Health Score", f"{primary_data.get('global_score', 0)}/100"),
            ("Response TTFB", f"{primary_data.get('ttfb_ms', 0)} ms"),
            ("Document Title", primary_data.get("title", "NOT FOUND")[:65]),
            ("Meta Description", primary_data.get("description", "NOT FOUND")[:65] + ("..." if len(primary_data.get("description", "")) > 65 else "")),
            ("Word Count", f"{primary_data.get('word_count', 0):,} words"),
            ("Heading Counts", f"H1: {primary_data.get('h1_count', 0)} | H2: {primary_data.get('h2_count', 0)} | H3: {primary_data.get('h3_count', 0)}"),
            ("Images (Alt Missing)", f"Total: {primary_data.get('total_images', 0)} (Missing: {primary_data.get('missing_alt_count', 0)})"),
            ("Internal Links", f"{primary_data.get('internal_links', 0)} links"),
            ("JSON-LD Structured Data", "PRESENT" if primary_data.get("has_json_ld") else "MISSING"),
            ("OpenGraph Social Graph", "OPTIMAL" if primary_data.get("has_og_title") and primary_data.get("has_og_description") else "INCOMPLETE")
        ]
        
        for k, v in kpis:
            pdf.cell(80, 6, k, 1, 0, "L")
            pdf.cell(100, 6, str(v), 1, 1, "L")
            
        pdf.ln(10)
        
        # Prescriptions
        pdf.set_font("Courier", "B", 14)
        pdf.set_text_color(0, 212, 255)
        pdf.cell(0, 8, "3. RECOMMENDATION ACTION ROADMAP", ln=1)
        pdf.line(15, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        prescriptions = generate_prescriptions(primary_data, primary_name)
        if not prescriptions:
            pdf.set_font("Courier", "", 10)
            pdf.set_text_color(0, 255, 136)
            pdf.cell(0, 8, "No outstanding high-priority issues found. Site is healthy!", ln=1)
        else:
            pdf.set_font("Courier", "B", 9)
            pdf.set_text_color(122, 155, 181)
            pdf.cell(10, 6, "ID", 1, 0, "C")
            pdf.cell(85, 6, "RECOMMENDED FIX", 1, 0, "L")
            pdf.cell(15, 6, "IMPACT", 1, 0, "C")
            pdf.cell(15, 6, "EFFORT", 1, 0, "C")
            pdf.cell(30, 6, "CATEGORY", 1, 0, "C")
            pdf.cell(25, 6, "FIX TIME", 1, 1, "C")
            
            pdf.set_font("Courier", "", 8.5)
            pdf.set_text_color(232, 244, 248)
            for i, p in enumerate(prescriptions[:15], 1): # limit to top 15 fixes
                pdf.cell(10, 6, f"#{i}", 1, 0, "C")
                pdf.cell(85, 6, p["title"][:48], 1, 0, "L")
                pdf.cell(15, 6, f"{p['impact']}/10", 1, 0, "C")
                pdf.cell(15, 6, f"{p['effort']}/10", 1, 0, "C")
                pdf.cell(30, 6, p["category"][-12:], 1, 0, "C")
                pdf.cell(25, 6, p["fix_time"], 1, 1, "C")

    # Output to bytes
    return bytes(pdf.output())


# ==============================================================================
#  SECTION 7: LAUNCHER PANEL (MAIN PAGE CONTROL CENTER)
# ==============================================================================

def render_launcher_ui(is_re_run=False):
    # Retrieve current session state values if they exist, else default values
    saved_url_map = st.session_state.get("url_map", {})
    saved_urls = list(saved_url_map.values()) if saved_url_map else []
    sabs_val = saved_urls[0] if len(saved_urls) > 0 else UNIVERSITIES["SABS University"]
    nca_val  = saved_urls[1] if len(saved_urls) > 1 else UNIVERSITIES["NCA Lahore"]
    ivs_val  = saved_urls[2] if len(saved_urls) > 2 else UNIVERSITIES["Indus Valley (IVS)"]
    bnu_val  = saved_urls[3] if len(saved_urls) > 3 else UNIVERSITIES["Beaconhouse (BNU)"]

    if not is_re_run:
        # Show full giant Cyberpunk-style Hero Header
        _md("""
        <div style="text-align:center;padding:1.5rem 0 2rem 0;margin-bottom:1.5rem;border-bottom:1px solid rgba(0,212,255,0.15);">
            <div style="font-family:'Orbitron',monospace;font-size:3.5rem;font-weight:900;
            color:#00d4ff;text-shadow:0 0 15px rgba(0,212,255,0.7);letter-spacing:0.18em;margin-bottom:0.5rem;">⚔ SENTINEL</div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:1.1rem;color:#7a9bb5;
            letter-spacing:0.25em;">SABS DIGITAL DOMINANCE & TECHNICAL SEO WAR ROOM</div>
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:#3d5a73;
            letter-spacing:0.12em;margin-top:0.6rem;text-transform:uppercase;">
                Competitive Intelligence Probe for Pakistani Art & Design Institutions
            </div>
        </div>
        """)
        
        # Introduction / Rationale Card
        _md("""
        <div style="background:rgba(10,22,40,0.45);border:1px solid rgba(0,212,255,0.12);
        border-radius:8px;padding:1.2rem;margin-bottom:2rem;line-height:1.7;">
            <div style="font-family:'Orbitron',monospace;font-size:0.85rem;color:#00d4ff;letter-spacing:0.1em;margin-bottom:0.6rem;">⚡ COMMAND BRIEFING</div>
            <div style="font-family:'Inter',sans-serif;font-size:0.85rem;color:#e8f4f8;">
                This intelligence platform scrapes, parses, and evaluates the live performance metrics of <b>SABS University</b> against its direct rivals: <b>NCA</b>, <b>Indus Valley (IVS)</b>, and <b>Beaconhouse (BNU)</b>. 
                By launching the scan, the engine performs parallel HTTP telemetry, parses DOM structures, audits HTML5 landmarks, computes readability scores, and checks meta structures to produce a real-time, prioritised technical prescription matrix.
            </div>
        </div>
        """)
    else:
        _md("""
        <div style="font-family:'Orbitron',monospace;font-size:0.95rem;color:#00d4ff;letter-spacing:0.1em;margin-bottom:0.8rem;margin-top:0.5rem;">
            ⚙️ ADJUST SCAN TARGETS
        </div>
        """)

    # Grid of inputs
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.8rem;color:#00d4ff;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.4rem;">■ PRIMARY TARGET (THE PROTAGONIST)</div>')
        sabs_url = st.text_input("SABS University URL", value=sabs_val, label_visibility="collapsed")
        
        _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.8rem;color:#f97316;letter-spacing:0.12em;text-transform:uppercase;margin-top:1.2rem;margin-bottom:0.4rem;">■ COMPETITOR TARGET: NCA LAHORE</div>')
        nca_url = st.text_input("NCA URL", value=nca_val, label_visibility="collapsed")
        
    with col2:
        _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.8rem;color:#a855f7;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.4rem;">■ COMPETITOR TARGET: INDUS VALLEY (IVS)</div>')
        ivs_url = st.text_input("IVS URL", value=ivs_val, label_visibility="collapsed")
        
        _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.8rem;color:#22c55e;letter-spacing:0.12em;text-transform:uppercase;margin-top:1.2rem;margin-bottom:0.4rem;">■ COMPETITOR TARGET: BEACONHOUSE (BNU)</div>')
        bnu_url = st.text_input("BNU URL", value=bnu_val, label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Large launching button
    btn_label = "⚔  RE-LAUNCH COMPETITIVE SCAN" if is_re_run else "⚔  LAUNCH COMPETITIVE SCAN"
    launch_btn = st.button(btn_label, use_container_width=True)

    if launch_btn:
        sabs_name = extract_uni_name(sabs_url, "SABS University")
        nca_name  = extract_uni_name(nca_url, "NCA Lahore")
        ivs_name  = extract_uni_name(ivs_url, "Indus Valley (IVS)")
        bnu_name  = extract_uni_name(bnu_url, "Beaconhouse (BNU)")

        url_map = {
            sabs_name: sabs_url.strip(),
            nca_name:  nca_url.strip(),
            ivs_name:  ivs_url.strip(),
            bnu_name:  bnu_url.strip(),
        }
        urls_tuple = tuple(url_map.items())

        prog = st.progress(0, text="⚔  Dispatching parallel telemetry probes to 4 universities …")
        with st.spinner(""):
            all_data = fetch_all_universities(urls_tuple)
        prog.progress(100, text="✦  All university scans complete.")
        time.sleep(0.8)
        prog.empty()

        st.session_state["all_data"] = all_data
        st.session_state["url_map"]  = url_map

        errors = [n for n, d in all_data.items() if "error" in d]
        if errors:
            st.warning(f"⚠  Could not reach: {', '.join(errors)}. These will show as OFFLINE in comparisons.")
            
        # Rerun to switch from Launcher UI to Results tabs
        st.rerun()

    # Footer inside launcher
    if not is_re_run:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        _md("""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:#1e3a4a;text-align:center;line-height:1.7;">
        SENTINEL v1.0 · SABS ASSESSMENT 2026 · DEVELOPED BY SOFTWARE ENGINEERING DIVISION<br>
        PAKISTAN ART SCHOOL INTELLIGENCE SERVICE · ALL PROBES ACTIVE
        </div>
        """)


# ==============================================================================
#  SECTION 9: PAGE RENDERERS
# ==============================================================================

def _no_data():
    _md("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
    height:62vh;gap:1.2rem;text-align:center;">
    <div style="font-family:'Orbitron',monospace;font-size:2.8rem;
    color:rgba(0,212,255,0.12);letter-spacing:0.2em;">⚔</div>
    <div style="font-family:'Orbitron',monospace;font-size:0.95rem;
    color:rgba(0,212,255,0.45);letter-spacing:0.2em;text-transform:uppercase;">AWAITING WAR ROOM LAUNCH</div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.78rem;
    color:#3d5a73;max-width:420px;line-height:1.8;">
    Enter university URLs in the sidebar panel<br>and click
    <span style="color:#00d4ff;">⚔ LAUNCH WAR ROOM SCAN</span><br>
    to initiate the competitive intelligence sequence.
    </div>
    </div>
    """)


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 1: THE WAR ROOM
# ──────────────────────────────────────────────────────────────────────────────

def render_war_room(all_data: dict):
    url_map = st.session_state.get("url_map", {})
    primary_name = list(url_map.keys())[0] if url_map else "SABS University"

    _page_header("⚔  THE WAR ROOM",
                 f"LIVE COMPETITIVE INTELLIGENCE · {get_uni_short(primary_name).upper()} DIGITAL RANKINGS")

    # Build comparison dataframe
    rows = []
    for name, d in all_data.items():
        if "error" in d:
            rows.append({
                "University": name, "Short": get_uni_short(name),
                "Score": 0, "TTFB": 9999,
                "Meta": 0, "Structure": 0, "Access": 0, "Content": 0,
                "Schema": False, "OG": False, "H1_ok": False,
                "Words": 0, "Imgs_miss": 0, "Canonical": False,
                "Color": get_uni_color(name), "Status": "OFFLINE",
            })
        else:
            sc = d.get("scores", {})
            rows.append({
                "University": name, "Short": get_uni_short(name),
                "Score": d.get("global_score", 0),
                "TTFB": d.get("ttfb_ms", 0),
                "Meta": sc.get("Meta Health", 0),
                "Structure": sc.get("DOM Structure", 0),
                "Access": sc.get("Accessibility", 0),
                "Content": sc.get("Content Quality", 0),
                "Schema": d.get("has_json_ld", False),
                "OG": d.get("has_og_title", False),
                "H1_ok": d.get("h1_count", 0) == 1,
                "Words": d.get("word_count", 0),
                "Imgs_miss": d.get("missing_alt_count", 0),
                "Canonical": bool(d.get("canonical")),
                "Color": get_uni_color(name), "Status": "ONLINE",
            })

    df = pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)
    df["Rank"] = df.index + 1

    # ── League Table ──────────────────────────────────────────────────────────
    _section_header("LIVE DIGITAL DOMINANCE LEAGUE TABLE")

    # Build styled HTML table
    table_rows = ""
    for _, row in df.iterrows():
        rank_i = int(row["Rank"]) - 1
        medal = RANK_MEDALS[rank_i] if rank_i < 4 else str(int(row["Rank"]))
        color = row["Color"]
        is_sabs = row["University"] == primary_name
        row_bg = f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)" if is_sabs else "rgba(0,0,0,0)"
        border_left = f"border-left:3px solid {color};" if is_sabs else ""
        score = int(row["Score"])
        bar_w = score
        ttfb = row["TTFB"]
        ttfb_c = "#00ff88" if ttfb < 200 else ("#ffb800" if ttfb < 600 else "#ff2d55")
        ttfb_txt = f"{ttfb:.0f}ms" if row["Status"]=="ONLINE" else "OFFLINE"
        schema_ic = '<span style="color:#00ff88;">✦</span>' if row["Schema"] else '<span style="color:#ff2d55;">✗</span>'
        og_ic     = '<span style="color:#00ff88;">✦</span>' if row["OG"]     else '<span style="color:#ff2d55;">✗</span>'
        h1_ic     = '<span style="color:#00ff88;">✦</span>' if row["H1_ok"] else '<span style="color:#ff2d55;">✗</span>'
        can_ic    = '<span style="color:#00ff88;">✦</span>' if row["Canonical"] else '<span style="color:#ff2d55;">✗</span>'
        status_badge = (f'<span style="background:rgba(0,255,136,0.12);border:1px solid #00ff88;color:#00ff88;'
                        f'font-size:0.6rem;padding:0.1rem 0.4rem;border-radius:3px;font-weight:700;">ONLINE</span>'
                        if row["Status"]=="ONLINE" else
                        f'<span style="background:rgba(255,45,85,0.12);border:1px solid #ff2d55;color:#ff2d55;'
                        f'font-size:0.6rem;padding:0.1rem 0.4rem;border-radius:3px;font-weight:700;">OFFLINE</span>')

        table_rows += f"""
<tr style="background:{row_bg};{border_left}">
  <td style="padding:0.7rem 0.8rem;font-family:'Orbitron',monospace;font-size:1rem;color:{color};text-align:center;">{medal}</td>
  <td style="padding:0.7rem 0.8rem;">
    <div style="font-family:'Orbitron',monospace;font-size:0.78rem;color:{color};font-weight:700;">{row['University']}</div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;margin-top:0.1rem;">{status_badge}</div>
  </td>
  <td style="padding:0.7rem 0.8rem;">
    <div style="font-family:'Orbitron',monospace;font-size:0.85rem;color:{color};font-weight:700;">{score}/100</div>
    <div style="background:rgba(255,255,255,0.05);border-radius:3px;height:4px;margin-top:0.3rem;width:90px;">
      <div style="height:100%;width:{bar_w}%;background:{color};border-radius:3px;"></div>
    </div>
  </td>
  <td style="padding:0.7rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.78rem;color:{ttfb_c};text-align:center;">{ttfb_txt}</td>
  <td style="padding:0.7rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.78rem;color:#7a9bb5;text-align:center;">{int(row['Meta'])}/25</td>
  <td style="padding:0.7rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.78rem;color:#7a9bb5;text-align:center;">{int(row['Structure'])}/25</td>
  <td style="padding:0.7rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.78rem;color:#7a9bb5;text-align:center;">{int(row['Access'])}/25</td>
  <td style="padding:0.7rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.78rem;color:#7a9bb5;text-align:center;">{int(row['Content'])}/25</td>
  <td style="padding:0.7rem 0.8rem;text-align:center;">{schema_ic}</td>
  <td style="padding:0.7rem 0.8rem;text-align:center;">{og_ic}</td>
  <td style="padding:0.7rem 0.8rem;text-align:center;">{h1_ic}</td>
  <td style="padding:0.7rem 0.8rem;text-align:center;">{can_ic}</td>
  <td style="padding:0.7rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#7a9bb5;text-align:center;">{int(row['Words']):,}</td>
</tr>"""

    _md(f"""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;background:rgba(6,13,20,0.85);
border:1px solid rgba(0,212,255,0.2);border-radius:8px;overflow:hidden;">
<thead>
<tr style="border-bottom:1px solid rgba(0,212,255,0.2);">
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">RANK</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;">UNIVERSITY</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;">SCORE</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">TTFB</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">META</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">STRUCT</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">ACCESS</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">CONTENT</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">SCHEMA</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">OG</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">H1</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">CAN.</th>
  <th style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;text-align:center;">WORDS</th>
</tr>
</thead>
<tbody>{table_rows}</tbody>
</table>
</div>
""")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Radar Comparison Chart ────────────────────────────────────────────────
    _section_header("MULTI-UNIVERSITY RADAR — PILLAR-BY-PILLAR ANALYSIS")
    pillars = ["Meta Health","DOM Structure","Accessibility","Content Quality"]

    fig_radar = go.Figure()
    cats_loop = pillars + [pillars[0]]

    for _, row in df.iterrows():
        name = row["University"]
        d_uni = all_data.get(name, {})
        sc = d_uni.get("scores", {}) if "error" not in d_uni else {}
        vals = [sc.get(p, 0) for p in pillars]
        vals_loop = vals + [vals[0]]
        color = row["Color"]
        r_int = int(color[1:3],16)
        g_int = int(color[3:5],16)
        b_int = int(color[5:7],16)
        is_sabs = name == primary_name

        fig_radar.add_trace(go.Scatterpolar(
            r=vals_loop, theta=cats_loop,
            fill="toself",
            fillcolor=f"rgba({r_int},{g_int},{b_int},{'0.18' if is_sabs else '0.06'})",
            line=dict(color=color, width=3 if is_sabs else 1.5,
                      dash="solid" if is_sabs else "dot"),
            name=get_uni_short(name),
            hovertemplate=f"<b>{name}</b><br>%{{theta}}: %{{r}}/25<extra></extra>",
        ))

    fig_radar.update_layout(
        **_PLY,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            angularaxis=dict(linecolor="rgba(0,212,255,0.15)", gridcolor="rgba(0,212,255,0.08)",
                             tickfont=dict(family="Share Tech Mono", color="#7a9bb5", size=11)),
            radialaxis=dict(visible=True, range=[0,25],
                            gridcolor="rgba(0,212,255,0.08)", linecolor="rgba(0,212,255,0.1)",
                            tickfont=dict(family="Share Tech Mono", color="#3d5a73", size=9),
                            tickvals=[5,10,15,20,25]),
        ),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center",
                    font=dict(family="Share Tech Mono", color="#7a9bb5", size=10),
                    bgcolor="rgba(0,0,0,0)"),
        height=440,
    )
    st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

    # ── Grouped Bar Chart — Pillar Scores ─────────────────────────────────────
    _section_header("PILLAR-BY-PILLAR SCORE BREAKDOWN")

    fig_bar = go.Figure()
    for _, row in df.iterrows():
        name = row["University"]
        d_uni = all_data.get(name, {})
        sc = d_uni.get("scores", {}) if "error" not in d_uni else {}
        fig_bar.add_trace(go.Bar(
            name=get_uni_short(name),
            x=pillars,
            y=[sc.get(p,0) for p in pillars],
            marker_color=row["Color"],
            marker_line_color="rgba(0,0,0,0.3)",
            marker_line_width=1,
            opacity=0.85,
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y}}/25<extra></extra>",
        ))

    fig_bar.update_layout(
        **_PLY,
        barmode="group",
        height=350,
        bargap=0.2, bargroupgap=0.05,
        xaxis=dict(gridcolor="rgba(0,212,255,0.06)", linecolor="rgba(0,212,255,0.1)"),
        yaxis=dict(range=[0,25], gridcolor="rgba(0,212,255,0.06)", tickvals=[0,5,10,15,20,25]),
        legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center",
                    font=dict(family="Share Tech Mono", color="#7a9bb5", size=10),
                    bgcolor="rgba(0,0,0,0)"),
        shapes=[dict(type="line", x0=-0.5, x1=3.5, y0=25, y1=25,
                     line=dict(color="rgba(0,212,255,0.2)", width=1, dash="dot"))],
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    # ── SABS Competitive Gap Summary ──────────────────────────────────────────
    _section_header(f"{get_uni_short(primary_name).upper()} COMPETITIVE GAP ANALYSIS")
    sabs_d = all_data.get(primary_name, {})
    if "error" not in sabs_d:
        sabs_score = sabs_d.get("global_score", 0)
        competitors = [(n, d) for n, d in all_data.items()
                       if n != primary_name and "error" not in d]
        if competitors:
            best_name, best_d = max(competitors, key=lambda x: x[1].get("global_score",0))
            best_score = best_d.get("global_score", 0)
            gap = round(best_score - sabs_score, 1)
            gap_color = "#ff2d55" if gap > 10 else ("#ffb800" if gap > 0 else "#00ff88")
            sabs_rank = int(df[df["University"]==primary_name]["Rank"].values[0])

            g1, g2, g3, g4 = st.columns(4)
            g1.metric(f"{get_uni_short(primary_name).upper()} CURRENT RANK",     f"#{sabs_rank} of 4",
                      "Beating all" if sabs_rank==1 else f"Behind {sabs_rank-1} rival(s)")
            g2.metric(f"{get_uni_short(primary_name).upper()} GLOBAL SCORE",     f"{sabs_score}/100", "")
            g3.metric("LEADER SCORE",           f"{best_score}/100",
                      get_uni_short(best_name))
            g4.metric("POINTS GAP TO LEADER",   f"{abs(gap)} pts",
                      f"{get_uni_short(primary_name).upper()} IS LEADING 🏆" if gap <= 0 else f"Must close {gap} pts gap")

            if gap > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                # Show which pillars SABS is losing most
                sabs_sc = sabs_d.get("scores",{})
                best_sc = best_d.get("scores",{})
                gap_data = []
                for p in pillars:
                    diff = sabs_sc.get(p,0) - best_sc.get(p,0)
                    gap_data.append({"Pillar": p, get_uni_short(primary_name): sabs_sc.get(p,0),
                                     "Leader": best_sc.get(p,0), "Gap": diff})
                gap_df = pd.DataFrame(gap_data).sort_values("Gap")

                fig_gap = go.Figure()
                fig_gap.add_trace(go.Bar(
                    x=gap_df["Gap"], y=gap_df["Pillar"], orientation="h",
                    marker_color=["#ff2d55" if x < 0 else "#00ff88" for x in gap_df["Gap"]],
                    text=[f"{'▼' if x<0 else '▲'} {abs(x):.0f} pts" for x in gap_df["Gap"]],
                    textposition="outside",
                    textfont=dict(family="Share Tech Mono", size=10, color="#7a9bb5"),
                    hovertemplate="<b>%{y}</b><br>Gap vs leader: %{x:+.0f} pts<extra></extra>",
                ))
                fig_gap.update_layout(
                    **_PLY, height=220,
                    title=dict(text=f"{get_uni_short(primary_name)} vs {get_uni_short(best_name)} — Score Gap Per Pillar",
                               font=dict(family="Share Tech Mono",color="#7a9bb5",size=11)),
                    xaxis=dict(gridcolor="rgba(0,212,255,0.06)",
                               title=dict(text="Points Behind (negative) / Ahead (positive)",
                                          font=dict(family="Share Tech Mono",color="#3d5a73",size=9))),
                    yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                    shapes=[dict(type="line",x0=0,x1=0,y0=-0.5,y1=3.5,
                                 line=dict(color="rgba(0,212,255,0.3)",width=1))],
                )
                st.plotly_chart(fig_gap, use_container_width=True, config={"displayModeBar": False})

    # Call SERP Share of Voice Simulator
    st.markdown("<br>", unsafe_allow_html=True)
    render_sov_simulator(all_data)


# ──────────────────────────────────────────────────────────────────────────────
#  SERP SHARE-OF-VOICE SIMULATOR
# ──────────────────────────────────────────────────────────────────────────────

def render_sov_simulator(all_data: dict):
    _section_header("🔮 SERP SHARE-OF-VOICE (SOV) SIMULATOR")
    
    _md("""
    <div style="background:rgba(10,22,40,0.45);border:1px solid rgba(0,212,255,0.12);
    border-radius:8px;padding:1rem;margin-bottom:1.5rem;line-height:1.6;font-size:0.82rem;color:#7a9bb5;">
        Simulate Google Search results for the university keyword category. 
        Adjust the organic rank position sliders below for each university. The engine will dynamically compute the click-through rates (CTR) based on their ranking and visualize their relative traffic share of voice.
    </div>
    """)
    
    # Sliders for each university
    col1, col2 = st.columns(2, gap="large")
    
    unis = list(all_data.keys())
    ranks = {}
    
    with col1:
        st.markdown("<div style='font-family:Share Tech Mono;font-size:0.8rem;color:#00d4ff;margin-bottom:0.6rem;text-transform:uppercase;'>■ Rank Inputs (1 = Top Rank, 30 = Invisible)</div>", unsafe_allow_html=True)
        for i, name in enumerate(unis):
            default_rank = min(30, (i * 3) + 1)
            ranks[name] = st.slider(
                f"Google Rank for {get_uni_short(name)}",
                min_value=1,
                max_value=30,
                value=default_rank,
                key=f"sov_rank_{name.lower().replace(' ', '_')}"
            )
            
    # Calculate CTR based on ranks
    def get_ctr(rank: int) -> float:
        if rank == 1: return 31.2
        if rank == 2: return 15.6
        if rank == 3: return 9.8
        if rank == 4: return 6.2
        if rank == 5: return 4.3
        if rank == 6: return 3.1
        if rank == 7: return 2.3
        if rank == 8: return 1.7
        if rank == 9: return 1.3
        if rank == 10: return 1.0
        if 11 <= rank <= 15: return 0.7
        if 16 <= rank <= 20: return 0.4
        return 0.1
        
    ctrs = {name: get_ctr(rank) for name, rank in ranks.items()}
    total_ctr = sum(ctrs.values())
    
    with col2:
        st.markdown("<div style='font-family:Share Tech Mono;font-size:0.8rem;color:#00d4ff;margin-bottom:0.6rem;text-transform:uppercase;'>■ Simulated Traffic Share</div>", unsafe_allow_html=True)
        if total_ctr > 0:
            shares = {name: (ctr / total_ctr) * 100 for name, ctr in ctrs.items()}
            
            # Render Plotly donut chart
            labels = [get_uni_short(n) for n in shares.keys()]
            values = list(shares.values())
            colors = [get_uni_color(n) for n in shares.keys()]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.45,
                marker=dict(colors=colors, line=dict(color="rgba(2, 5, 9, 0.8)", width=2)),
                hoverinfo="label+percent",
                textinfo="label+percent",
                textfont=dict(family="Share Tech Mono", size=11, color="#e8f4f8")
            )])
            
            fig.update_layout(
                **_PLY,
                showlegend=False,
                height=260,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.warning("All ranks are out of visible range.")


# ──────────────────────────────────────────────────────────────────────────────
#  SITEMAP AUDITOR
# ──────────────────────────────────────────────────────────────────────────────

def render_sitemap_scanner(name: str, url: str):
    _page_header(f"🔗  {get_uni_short(name).upper()} SITEMAP AUDITOR",
                 "DOMAIN-LEVEL CRAWL COVERAGE · XML ARCHITECTURE TELEMETRY")
                 
    _md("""
    <div style="background:rgba(10,22,40,0.45);border:1px solid rgba(0,212,255,0.12);
    border-radius:8px;padding:1.1rem;margin-bottom:1.5rem;line-height:1.6;font-size:0.82rem;color:#7a9bb5;">
        Specify the XML sitemap index or sitemap file URL to inspect structural indexes, last modifications, and check canonical/SSL routing health across all listed pages.
    </div>
    """)
    
    # Calculate default sitemap URL
    default_sitemap = url.rstrip("/") + "/sitemap.xml" if url else "https://sabsu.edu.pk/sitemap.xml"
    
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        sitemap_url = st.text_input("Sitemap XML URL", value=default_sitemap, label_visibility="collapsed")
    with col_btn:
        run_scan = st.button("🔎  RUN SITEMAP SCAN", use_container_width=True)
        
    if run_scan:
        if not sitemap_url.strip():
            st.error("Please enter a valid sitemap URL.")
            return
            
        prog = st.progress(0, text="📡  Requesting sitemap file...")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html) SentinelBot/1.0"}
            r = requests.get(sitemap_url.strip(), headers=headers, timeout=8, verify=False)
            prog.progress(35, text="📦  Parsing XML sitemap payload...")
            
            if r.status_code != 200:
                st.error(f"⛔  HTTP Fail: Server returned status code {r.status_code}")
                return
                
            soup = BeautifulSoup(r.text, "xml")
            urls = soup.find_all("url")
            sitemaps = soup.find_all("sitemap")
            
            prog.progress(70, text="🧬  Analyzing sitemap hierarchy...")
            
            if sitemaps:
                # Sitemap Index File
                st.info(f"📁  **Detected Sitemap Index File** containing {len(sitemaps)} nested sitemaps.")
                index_data = []
                for s in sitemaps:
                    loc = s.find("loc")
                    lastmod = s.find("lastmod")
                    index_data.append({
                        "Nested Sitemap URL": loc.get_text() if loc else "N/A",
                        "Last Modified": lastmod.get_text() if lastmod else "N/A"
                    })
                st.dataframe(pd.DataFrame(index_data), use_container_width=True)
                
            elif urls:
                # Standard Sitemap
                prog.progress(100, text="✦  Analysis complete.")
                time.sleep(0.4)
                prog.empty()
                
                st.success(f"✦  **Standard XML Sitemap Scanner Complete.** Found **{len(urls)}** URLs registered.")
                
                url_data = []
                https_count = 0
                domain_mismatch = 0
                base_domain = urlparse(url).netloc if url else ""
                
                for u in urls:
                    loc = u.find("loc")
                    loc_text = loc.get_text().strip() if loc else ""
                    lastmod = u.find("lastmod")
                    changefreq = u.find("changefreq")
                    priority = u.find("priority")
                    
                    if loc_text.startswith("https://"):
                        https_count += 1
                    if base_domain and urlparse(loc_text).netloc != base_domain:
                        domain_mismatch += 1
                        
                    url_data.append({
                        "Page URL": loc_text,
                        "Last Modified": lastmod.get_text() if lastmod else "—",
                        "Change Freq": changefreq.get_text() if changefreq else "—",
                        "Priority": priority.get_text() if priority else "—"
                    })
                    
                df_urls = pd.DataFrame(url_data)
                
                # KPIs Columns
                k1, k2, k3 = st.columns(3)
                k1.metric("TOTAL CRAWLABLE PAGES", f"{len(urls)}")
                k2.metric("SSL SECURE (HTTPS)", f"{https_count}", f"{len(urls) - https_count} insecure")
                k3.metric("DOMAIN CONSISTENCY", "100%" if domain_mismatch == 0 else f"{round((1 - domain_mismatch/len(urls))*100)}%", f"{domain_mismatch} external domain links")
                
                st.markdown("<br>", unsafe_allow_html=True)
                _section_header("SITEMAP PAGES DATABASE")
                st.dataframe(df_urls, use_container_width=True, hide_index=True)
                
            else:
                st.warning("⚠️  The file loaded successfully, but it does not appear to contain standard sitemap XML tags (<url> or <sitemap>).")
                
        except Exception as e:
            st.error(f"⛔  Could not fetch sitemap: {e}")


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 2: SABS DEEP AUDIT
# ──────────────────────────────────────────────────────────────────────────────

def render_deep_audit(d: dict, name: str = "SABS University"):
    _page_header(f"🔬  {get_uni_short(name).upper()} DEEP AUDIT", f"TECHNICAL SEO DIAGNOSTICS · DOM · SCHEMA · ACCESSIBILITY")

    # ── Top KPIs ──────────────────────────────────────────────────────────────
    c1,c2,c3,c4,c5 = st.columns(5)
    gs = d.get("global_score",0)
    c1.metric("HEALTH SCORE",       f"{gs}/100",
              "EXCELLENT" if gs>=80 else ("MODERATE" if gs>=55 else "CRITICAL"))
    c2.metric("SERVER TTFB",        f"{d.get('ttfb_ms',0)} ms",
              "FAST" if d.get('ttfb_ms',0)<200 else ("OK" if d.get('ttfb_ms',0)<600 else "SLOW"))
    c3.metric("WORD COUNT",         f"{d.get('word_count',0):,}",
              "LONG-FORM" if d.get('word_count',0)>=800 else ("MEDIUM" if d.get('word_count',0)>=300 else "THIN"))
    c4.metric("IMAGES MISSING ALT", str(d.get("missing_alt_count",0)),
              f"of {d.get('total_images',0)} images")
    c5.metric("HTTP STATUS",        str(d.get("status_code","—")),
              "OK" if d.get("status_code")==200 else "CHECK")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Radar ─────────────────────────────────────────────────────────────────
    _section_header(f"{get_uni_short(name).upper()} SEO HEALTH RADAR")
    scores = d.get("scores",{})
    cats = list(scores.keys())
    vals = list(scores.values())
    cl = cats + [cats[0]]; vl = vals + [vals[0]]
    fig_r = go.Figure()
    fig_r.add_trace(go.Scatterpolar(r=vl,theta=cl,fill="toself",
        fillcolor="rgba(0,212,255,0.12)",
        line=dict(color="#00d4ff",width=2.5),name=get_uni_short(name),
        hovertemplate="<b>%{theta}</b><br>%{r}/25<extra></extra>"))
    fig_r.add_trace(go.Scatterpolar(r=[25]*len(cl),theta=cl,fill="toself",
        fillcolor="rgba(0,102,255,0.04)",
        line=dict(color="rgba(0,102,255,0.2)",width=1,dash="dot"),name="Target",hoverinfo="skip"))
    fig_r.update_layout(**_PLY,height=340,
        polar=dict(bgcolor="rgba(0,0,0,0)",
            angularaxis=dict(gridcolor="rgba(0,212,255,0.08)",
                             tickfont=dict(family="Share Tech Mono",color="#7a9bb5",size=11)),
            radialaxis=dict(visible=True,range=[0,25],gridcolor="rgba(0,212,255,0.08)",
                            tickfont=dict(family="Share Tech Mono",color="#3d5a73",size=9),
                            tickvals=[5,10,15,20,25])),
        legend=dict(font=dict(family="Share Tech Mono",color="#7a9bb5",size=9),bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})

    # ── Meta Matrix ───────────────────────────────────────────────────────────
    _section_header("META ARCHITECTURE MATRIX")
    ma1, ma2 = st.columns(2, gap="large")
    with ma1:
        tl = d.get("title_len",0); title = d.get("title","")
        tc = "#00ff88" if 50<=tl<=60 else ("#ffb800" if 0<tl<50 or tl>60 else "#ff2d55")
        tv = f"OPTIMAL ({tl}/50–60 ch)" if 50<=tl<=60 else (f"TOO SHORT ({tl} ch)" if 0<tl<50 else (f"TOO LONG ({tl} ch)" if tl>60 else "MISSING"))
        fp = min(100,(tl/60)*100)
        _md(f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);border-radius:8px;padding:1.1rem;"><div style="font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">▸ &lt;TITLE&gt; TAG</div><div style="font-family:\'Inter\',sans-serif;font-size:0.85rem;color:#e8f4f8;margin-bottom:0.7rem;word-break:break-all;">"{title if title else "NOT FOUND"}"</div><div style="background:rgba(0,212,255,0.06);border-radius:4px;height:5px;overflow:hidden;margin-bottom:0.4rem;"><div style="height:100%;width:{fp:.0f}%;background:{tc};border-radius:4px;"></div></div><div style="display:flex;justify-content:space-between;font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;color:#3d5a73;"><span>0</span><span style="color:{tc};">{tv}</span><span>60</span></div></div>')
    with ma2:
        dl = d.get("desc_len",0); desc = d.get("description","")
        dc = "#00ff88" if 150<=dl<=160 else ("#ffb800" if 0<dl<150 or dl>160 else "#ff2d55")
        dv = f"OPTIMAL ({dl}/150–160 ch)" if 150<=dl<=160 else (f"TOO SHORT ({dl} ch)" if 0<dl<150 else (f"TOO LONG ({dl} ch)" if dl>160 else "MISSING"))
        fpd = min(100,(dl/160)*100)
        _md(f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);border-radius:8px;padding:1.1rem;"><div style="font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">▸ META DESCRIPTION</div><div style="font-family:\'Inter\',sans-serif;font-size:0.85rem;color:#e8f4f8;margin-bottom:0.7rem;word-break:break-all;">"{desc if desc else "NOT FOUND"}"</div><div style="background:rgba(0,212,255,0.06);border-radius:4px;height:5px;overflow:hidden;margin-bottom:0.4rem;"><div style="height:100%;width:{fpd:.0f}%;background:{dc};border-radius:4px;"></div></div><div style="display:flex;justify-content:space-between;font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;color:#3d5a73;"><span>0</span><span style="color:{dc};">{dv}</span><span>160</span></div></div>')

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Heading Hierarchy ─────────────────────────────────────────────────────
    _section_header("HEADING HIERARCHY TREE — DOCUMENT OUTLINE")
    h1c = d.get("h1_count",0); headings = d.get("headings",[])
    if h1c == 0:
        st.error("⚠  CRITICAL — H1 TAG ABSENT: Googlebot cannot identify the page's primary topic.")
    elif h1c > 1:
        st.warning(f"⚠  WARNING — {h1c} H1 TAGS: Topic dilution. Exactly ONE H1 is required per page.")
    else:
        st.success("✦  PASS — SINGULAR H1 DETECTED: Heading hierarchy correctly structured.")

    if headings:
        tree = ""
        for h in headings[:35]:
            lvl=h["level"]; txt=h["text"][:85]+("…" if len(h["text"])>85 else "")
            if lvl=="H1":
                tree += f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.85rem;color:#00d4ff;border-left:3px solid #00d4ff;padding:0.3rem 0.7rem;margin:0.15rem 0;background:rgba(0,212,255,0.05);border-radius:0 5px 5px 0;"><span style="opacity:0.45;font-size:0.7rem;">H1 ▸</span> {txt}</div>'
            elif lvl=="H2":
                tree += f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.78rem;color:#7dd3fc;border-left:3px solid #0ea5e9;padding:0.28rem 0.7rem;margin:0.15rem 0 0.15rem 1.2rem;background:rgba(14,165,233,0.04);border-radius:0 5px 5px 0;"><span style="opacity:0.45;font-size:0.65rem;">H2 ▶</span> {txt}</div>'
            else:
                tree += f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.72rem;color:#7a9bb5;border-left:3px solid #334e68;padding:0.22rem 0.7rem;margin:0.12rem 0 0.12rem 2.4rem;background:rgba(51,78,104,0.04);border-radius:0 5px 5px 0;"><span style="opacity:0.45;font-size:0.62rem;">H3 ›</span> {txt}</div>'
        if len(headings)>35:
            tree += f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;color:#3d5a73;padding:0.4rem 0.7rem;">… and {len(headings)-35} more nodes</div>'
        _md(f'<div style="background:rgba(6,13,20,0.85);border:1px solid rgba(0,212,255,0.14);border-radius:8px;padding:0.7rem;max-height:300px;overflow-y:auto;">{tree}</div>')
    _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.68rem;color:#3d5a73;padding:0.35rem 0;">TOTALS → <span style="color:#00d4ff;">H1: {h1c}</span> · <span style="color:#7dd3fc;">H2: {d.get("h2_count",0)}</span> · <span style="color:#7a9bb5;">H3: {d.get("h3_count",0)}</span></div>')

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Schema & OG ───────────────────────────────────────────────────────────
    _section_header("SCHEMA & SOCIAL GRAPH INTELLIGENCE")
    sc1, sc2 = st.columns(2, gap="large")
    og = d.get("og_tags",{})

    def _checklist(checks_list):
        rows = ""
        for tag, present, desc_txt in checks_list:
            ic = "#00ff88" if present else "#ff2d55"
            icon = "✦" if present else "✗"
            badge = (f'<span style="background:rgba(0,255,136,0.1);border:1px solid #00ff88;'
                     f'color:#00ff88;font-size:0.6rem;font-weight:700;padding:0.08rem 0.4rem;border-radius:3px;">ACTIVE</span>'
                     if present else
                     f'<span style="background:rgba(255,45,85,0.1);border:1px solid #ff2d55;'
                     f'color:#ff2d55;font-size:0.6rem;font-weight:700;padding:0.08rem 0.4rem;border-radius:3px;">MISSING</span>')
            rows += f'<div style="display:flex;align-items:center;gap:0.6rem;padding:0.4rem 0.7rem;border-bottom:1px solid rgba(0,212,255,0.06);font-family:\'Share Tech Mono\',monospace;font-size:0.75rem;"><span style="color:{ic};">{icon}</span><code style="color:#00d4ff;font-size:0.72rem;">{tag}</code><span style="color:#7a9bb5;flex:1;font-size:0.72rem;">{desc_txt}</span>{badge}</div>'
        return rows

    with sc1:
        og_checks = [
            ("og:title",       d.get("has_og_title",False),       "Social share title"),
            ("og:description", d.get("has_og_description",False),  "Social preview text"),
            ("og:image",       d.get("has_og_image",False),        "Preview thumbnail"),
            ("og:url",         "og:url" in og,                     "Canonical social URL"),
            ("og:type",        "og:type" in og,                    "Content type"),
            ("og:site_name",   "og:site_name" in og,               "Brand name"),
        ]
        _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem;">▸ OpenGraph (og:) Protocol</div>')
        _md(f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.18);border-radius:8px;overflow:hidden;">{_checklist(og_checks)}</div>')

    with sc2:
        jld_types = d.get("json_ld_types",[])
        jld_checks = [
            ("JSON-LD Present",   d.get("has_json_ld",False),  "Structured data block"),
            ("Schema @type",      bool(jld_types),              "Entity type declared"),
        ]
        extra = (f'<div style="padding:0.5rem 0.7rem;font-family:\'Share Tech Mono\',monospace;font-size:0.68rem;color:#00d4ff;border-top:1px solid rgba(0,212,255,0.1);">TYPES: {", ".join(jld_types[:4])}</div>'
                 if jld_types else "")
        _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem;">▸ JSON-LD Structured Data</div>')
        _md(f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.18);border-radius:8px;overflow:hidden;">{_checklist(jld_checks)}{extra}</div>')

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Accessibility ─────────────────────────────────────────────────────────
    _section_header("ACCESSIBILITY ENGINE — IMAGE ALT-TEXT AUDIT")
    ti = d.get("total_images",0); ma = d.get("missing_alt_count",0)
    miss_urls = d.get("missing_alt_urls",[])
    a1,a2,a3 = st.columns(3)
    a1.metric("TOTAL IMAGES", str(ti))
    a2.metric("MISSING ALT TEXT", str(ma), "⚠ WCAG VIOLATION" if ma>0 else "✦ CLEAN")
    a3.metric("ALT COVERAGE", f"{round((1-ma/max(ti,1))*100)}%",
              "PERFECT" if ma==0 else "NEEDS WORK")
    if miss_urls:
        with st.expander(f"⚠  {ma} image(s) missing alt — Click for full violation report"):
            st.info("Each missing alt text is a WCAG 2.1 Level A violation AND a missed Google Image Search ranking opportunity — critical for an art school.")
            st.dataframe(
                pd.DataFrame({"#":range(1,len(miss_urls)+1),"Image URL":miss_urls}),
                use_container_width=True, hide_index=True)
    elif ti > 0:
        st.success("✦  ALL IMAGES HAVE ALT ATTRIBUTES — Perfect accessibility compliance.")


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 3: PRESCRIPTION ENGINE
# ──────────────────────────────────────────────────────────────────────────────

def render_prescription_engine(d: dict, name: str = "SABS University"):
    _page_header("💊  PRESCRIPTION ENGINE",
                 "PRIORITISED ACTION PLAN · IMPACT/EFFORT MATRIX · 30-DAY ROADMAP")

    prescriptions = generate_prescriptions(d, name)
    total = len(prescriptions)

    if total == 0:
        st.success(f"✦  No significant issues found. {get_uni_short(name)} is in excellent SEO health!")
        return

    # ── Summary Banner ────────────────────────────────────────────────────────
    quick_wins = [p for p in prescriptions if p["quadrant"] == "⚡ Quick Win"]
    major_proj = [p for p in prescriptions if p["quadrant"] == "🏗️ Major Project"]
    critical   = [p for p in prescriptions if p["category"] == "🚨 Critical"]

    s1,s2,s3,s4 = st.columns(4)
    s1.metric("TOTAL ISSUES FOUND",  str(total),         "Action items generated")
    s2.metric("CRITICAL ISSUES",     str(len(critical)),  "Fix IMMEDIATELY" if critical else "None found")
    s3.metric("⚡ QUICK WINS",       str(len(quick_wins)),"High impact, low effort")
    s4.metric("🏗️ MAJOR PROJECTS",  str(len(major_proj)),"Plan for next month")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Impact / Effort Matrix ─────────────────────────────────────────────────
    _section_header("IMPACT / EFFORT MATRIX — STRATEGIC PRIORITISATION")

    _md("""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;
    font-family:'Share Tech Mono',monospace;font-size:0.68rem;margin-bottom:0.8rem;">
    <div style="background:rgba(0,255,136,0.07);border:1px solid rgba(0,255,136,0.25);
    border-radius:6px;padding:0.5rem 0.8rem;color:#00ff88;">
    ⚡ QUICK WINS (top-left) — Do this week. High impact, low effort.
    </div>
    <div style="background:rgba(0,102,255,0.07);border:1px solid rgba(0,102,255,0.25);
    border-radius:6px;padding:0.5rem 0.8rem;color:#60a5fa;">
    🏗️ MAJOR PROJECTS (top-right) — Plan for next month. High impact, high effort.
    </div>
    <div style="background:rgba(255,184,0,0.06);border:1px solid rgba(255,184,0,0.2);
    border-radius:6px;padding:0.5rem 0.8rem;color:#ffb800;">
    📋 FILL-INS (bottom-left) — Do when free. Low impact, low effort.
    </div>
    <div style="background:rgba(255,45,85,0.06);border:1px solid rgba(255,45,85,0.2);
    border-radius:6px;padding:0.5rem 0.8rem;color:#ff2d55;">
    ❌ DEPRIORITISE (bottom-right) — Skip for now. Low impact, high effort.
    </div>
    </div>
    """)

    # Build scatter plot
    cat_colors = {
        "🚨 Critical":      "#ff2d55",
        "📋 Meta Tags":     "#00d4ff",
        "🔧 Technical SEO": "#a855f7",
        "🏗️ DOM Structure": "#60a5fa",
        "⚙️ Schema Markup": "#f97316",
        "📱 Social Media":  "#22c55e",
        "♿ Accessibility": "#ffb800",
        "📝 Content":       "#e879f9",
        "⚡ Performance":   "#f43f5e",
        "🔗 Link Architecture": "#34d399",
    }

    fig_matrix = go.Figure()

    # Quadrant background shading
    fig_matrix.add_shape(type="rect", x0=0,x1=4.5,y0=5.5,y1=10.5,
        fillcolor="rgba(0,255,136,0.04)", line_color="rgba(0,0,0,0)")
    fig_matrix.add_shape(type="rect", x0=4.5,x1=10.5,y0=5.5,y1=10.5,
        fillcolor="rgba(0,102,255,0.04)", line_color="rgba(0,0,0,0)")
    fig_matrix.add_shape(type="rect", x0=0,x1=4.5,y0=0,y1=5.5,
        fillcolor="rgba(255,184,0,0.03)", line_color="rgba(0,0,0,0)")
    fig_matrix.add_shape(type="rect", x0=4.5,x1=10.5,y0=0,y1=5.5,
        fillcolor="rgba(255,45,85,0.03)", line_color="rgba(0,0,0,0)")

    # Quadrant labels
    for (tx,ty,label,lcolor) in [
        (2.2, 9.5, "⚡ QUICK WINS",      "#00ff88"),
        (7.5, 9.5, "🏗️ MAJOR PROJECTS", "#60a5fa"),
        (2.2, 1.0, "📋 FILL-INS",        "#ffb800"),
        (7.5, 1.0, "❌ DEPRIORITISE",    "#ff2d55"),
    ]:
        fig_matrix.add_annotation(x=tx, y=ty, text=label,
            font=dict(family="Orbitron",size=9,color=lcolor),
            showarrow=False, opacity=0.5)

    # Divider lines
    fig_matrix.add_shape(type="line",x0=4.5,x1=4.5,y0=0,y1=10.5,
        line=dict(color="rgba(0,212,255,0.15)",width=1,dash="dot"))
    fig_matrix.add_shape(type="line",x0=0,x1=10.5,y0=5.5,y1=5.5,
        line=dict(color="rgba(0,212,255,0.15)",width=1,dash="dot"))

    # One trace per category for legend
    for cat, plist in {p["category"]: [] for p in prescriptions}.items():
        cat_items = [p for p in prescriptions if p["category"]==cat]
        color = cat_colors.get(cat, "#7a9bb5")
        fig_matrix.add_trace(go.Scatter(
            x=[p["effort"]  for p in cat_items],
            y=[p["impact"]  for p in cat_items],
            mode="markers+text",
            marker=dict(size=14, color=color,
                        line=dict(color="rgba(0,0,0,0.5)", width=1),
                        opacity=0.85),
            text=[p["title"][:22]+"…" if len(p["title"])>22 else p["title"] for p in cat_items],
            textposition="top center",
            textfont=dict(family="Share Tech Mono", size=7.5, color="#7a9bb5"),
            name=cat,
            hovertemplate="<b>%{customdata[0]}</b><br>Impact: %{y}/10  Effort: %{x}/10<br>%{customdata[1]}<extra></extra>",
            customdata=[[p["title"], p["gain"]] for p in cat_items],
        ))

    fig_matrix.update_layout(
        **_PLY, height=520,
        xaxis=dict(range=[0,10.5], gridcolor="rgba(0,212,255,0.06)",
                   title=dict(text="IMPLEMENTATION EFFORT  →  (1=Easy  10=Hard)",
                              font=dict(family="Share Tech Mono",color="#3d5a73",size=10)),
                   tickvals=list(range(0,11)),
                   tickfont=dict(family="Share Tech Mono",color="#3d5a73",size=9)),
        yaxis=dict(range=[0,10.5], gridcolor="rgba(0,212,255,0.06)",
                   title=dict(text="↑  SEO IMPACT  (1=Minor  10=Critical)",
                              font=dict(family="Share Tech Mono",color="#3d5a73",size=10)),
                   tickvals=list(range(0,11)),
                   tickfont=dict(family="Share Tech Mono",color="#3d5a73",size=9)),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center",
                    font=dict(family="Share Tech Mono",color="#7a9bb5",size=9),
                    bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_matrix, use_container_width=True, config={"displayModeBar": False})

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Prioritised Action Items ──────────────────────────────────────────────
    _section_header("PRIORITISED ACTION ITEMS — RANKED BY IMPACT")

    for i, p in enumerate(prescriptions, 1):
        imp = p["impact"]; eff = p["effort"]
        imp_color = "#ff2d55" if imp>=9 else ("#ffb800" if imp>=7 else ("#00d4ff" if imp>=5 else "#3d5a73"))
        quad_color = {"⚡ Quick Win":"#00ff88","🏗️ Major Project":"#60a5fa",
                      "📋 Fill-In":"#ffb800","❌ Deprioritise":"#ff2d55"}.get(p["quadrant"],"#7a9bb5")

        with st.expander(f"#{i}  {p['title']}  ·  Impact {imp}/10  ·  {p['quadrant']}"):
            col_a, col_b = st.columns([3,1])
            with col_a:
                _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.3rem;">THE PROBLEM</div>')
                _md(f'<div style="font-family:\'Inter\',sans-serif;font-size:0.85rem;color:#e8f4f8;line-height:1.7;margin-bottom:0.8rem;">{p["description"]}</div>')
                _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.3rem;">THE FIX</div>')
                _md(f'<div style="font-family:\'Inter\',sans-serif;font-size:0.82rem;color:#00d4ff;line-height:1.7;border-left:2px solid #00d4ff;padding-left:0.7rem;margin-bottom:0.8rem;">{p["action"]}</div>')
                _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.3rem;">WHY IT MATTERS (SEO RATIONALE)</div>')
                _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.76rem;color:#7a9bb5;line-height:1.7;">{p["rationale"]}</div>')
            with col_b:
                st.metric("SEO IMPACT",  f"{imp}/10", "")
                st.metric("EFFORT",      f"{eff}/10", "")
                st.metric("FIX TIME",    p["fix_time"], "")
                st.metric("CATEGORY",    p["category"].split()[-1], "")
                _md(f'<div style="background:rgba({",".join(str(int(quad_color[i:i+2],16)) for i in (1,3,5))},0.1);border:1px solid {quad_color};border-radius:6px;padding:0.4rem 0.6rem;font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:{quad_color};text-align:center;margin-top:0.5rem;">{p["quadrant"]}</div>')
                _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.65rem;color:#3d5a73;margin-top:0.5rem;">EXPECTED GAIN:<br><span style="color:#00ff88;">{p["gain"]}</span></div>')

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 30-Day Action Plan ────────────────────────────────────────────────────
    _section_header("30-DAY EXECUTION ROADMAP")

    week1 = [p for p in prescriptions if p["effort"] <= 2]
    week2 = [p for p in prescriptions if 3 <= p["effort"] <= 4 and p["impact"] >= 6]
    week3 = [p for p in prescriptions if p["effort"] >= 5 and p["impact"] >= 6]

    w1,w2,w3 = st.columns(3, gap="large")
    for col, week, label, color, days in [
        (w1, week1, "WEEK 1 — QUICK WINS",    "#00ff88", "Days 1–7"),
        (w2, week2, "WEEK 2 — MEDIUM FIXES",  "#ffb800", "Days 8–14"),
        (w3, week3, "WEEK 3–4 — PROJECTS",    "#60a5fa", "Days 15–30"),
    ]:
        with col:
            _md(f'<div style="font-family:\'Orbitron\',monospace;font-size:0.72rem;font-weight:700;color:{color};letter-spacing:0.1em;border-bottom:1px solid {color}33;padding-bottom:0.3rem;margin-bottom:0.6rem;">{label}<br><span style="font-size:0.58rem;color:#3d5a73;">{days}</span></div>')
            if week:
                for p in week[:6]:
                    _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.73rem;color:#7a9bb5;padding:0.3rem 0;border-bottom:1px solid rgba(0,212,255,0.06);display:flex;gap:0.4rem;"><span style="color:{color};">▸</span>{p["title"][:40]+("…" if len(p["title"])>40 else "")}</div>')
            else:
                _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.72rem;color:#3d5a73;">No items in this category.</div>')


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 4: AI AGENT ASSISTANT
# ──────────────────────────────────────────────────────────────────────────────

def render_ai_agent(all_data: dict, url_map: dict):
    _page_header("🤖  SENTINEL AI CO-PILOT", "AUTONOMOUS SEO AGENT · META REWRITING · DEVELOPER TICKET GENERATION")
    
    _md("""
    <div style="background:rgba(10,22,40,0.45);border:1px solid rgba(0,212,255,0.12);
    border-radius:8px;padding:1.1rem;margin-bottom:1.5rem;line-height:1.6;font-size:0.82rem;color:#7a9bb5;">
        Deploy an autonomous AI agent to analyze competitive metrics, draft engineering tickets for site changes, optimize meta tags, or answer custom SEO strategy questions using Gemini 1.5 Flash.
    </div>
    """)
    
    # Select target university
    target_uni = st.selectbox("Select Target University to Analyze", list(url_map.keys()))
    target_data = all_data.get(target_uni, {})
    
    if not target_data:
        st.warning(f"No crawl data available for {target_uni}.")
        return
        
    # Inputs
    col_key, col_preset = st.columns([1, 1])
    with col_key:
        api_key = st.text_input("Gemini API Key (Optional)", type="password", 
                               help="Get a free key from Google AI Studio", 
                               value=st.session_state.get("gemini_api_key", ""))
        if api_key:
            st.session_state["gemini_api_key"] = api_key
            
        st.markdown(
            '<div style="font-size:0.75rem;margin-top:-0.5rem;color:#7a9bb5;">'
            'Don\'t have a key? Get one at <a href="https://aistudio.google.com/" target="_blank" style="color:#00d4ff;">Google AI Studio</a>. '
            'Leave empty to run in <b>Simulation Mode</b>.'
            '</div>', 
            unsafe_allow_html=True
        )
        
    with col_preset:
        preset = st.selectbox("Select Preset Agent Task", [
            "Draft engineering tickets (Jira/GitHub) for audit fixes",
            "Rewrite Meta Title and Description for target keywords",
            "Draft executive strategy summary comparing SABS and competitors",
            "Custom query / ask the agent anything"
        ])
        
    # Extra fields based on preset
    keywords = ""
    custom_prompt = ""
    if preset == "Rewrite Meta Title and Description for target keywords":
        keywords = st.text_input("Enter target keywords (separated by commas)", "art school karachi, fine arts admissions SABS")
    elif preset == "Custom query / ask the agent anything":
        custom_prompt = st.text_area("Your Custom Instruction / Query", "Analyze SABS's biggest weakness compared to NCA Lahore and suggest a plan.")
        
    st.markdown("<br>", unsafe_allow_html=True)
    dispatch = st.button("⚡  DISPATCH SENTINEL AGENT", use_container_width=True)
    
    if dispatch:
        # Construct prompt
        if preset == "Draft engineering tickets (Jira/GitHub) for audit fixes":
            prompt = f"""
Analyze the following SEO telemetry data for {target_uni} and draft professional engineering tickets (e.g. Jira/GitHub Issues) to resolve the identified technical issues.
For each ticket, include:
- Title
- Description / Problem Statement (using actual data)
- Technical Resolution steps
- Priority (High/Medium/Low)
- Acceptance Criteria

SEO Telemetry Data for {target_uni}:
{json.dumps(target_data, indent=2)}
"""
        elif preset == "Rewrite Meta Title and Description for target keywords":
            prompt = f"""
Optimize the homepage meta title and description tags for {target_uni}.
Current Title: "{target_data.get('title', '')}" (Length: {target_data.get('title_len', 0)})
Current Description: "{target_data.get('description', '')}" (Length: {target_data.get('desc_len', 0)})
Target Keywords: {keywords}

Provide:
1. 3 alternative options for optimized Title tags (must be between 50-60 characters, with character count shown).
2. 3 alternative options for optimized Meta Descriptions (must be between 150-160 characters, with character count shown).
3. Search engine result page (SERP) snippet preview of the recommended combination.
4. Rationale for why these optimizations will improve click-through-rate (CTR) and rankings for the targeted keywords.
"""
        elif preset == "Draft executive strategy summary comparing SABS and competitors":
            competitor_names = [name for name in all_data.keys() if name != target_uni]
            clean_comparison_data = {k: {
                "global_score": v.get("global_score", 0),
                "ttfb_ms": v.get("ttfb_ms", 0),
                "word_count": v.get("word_count", 0),
                "missing_alt_count": v.get("missing_alt_count", 0),
                "title": v.get("title", ""),
                "description": v.get("description", ""),
                "h1_count": v.get("h1_count", 0)
            } for k, v in all_data.items()}
            
            prompt = f"""
Write an executive SEO strategy report comparing {target_uni} to its competitors: {", ".join(competitor_names)}.
Analyze who is winning the digital dominance war, what SABS's strengths and weaknesses are based on the crawling stats, and what strategic actions SABS must take to capture search market share.

Roster Data:
{json.dumps(clean_comparison_data, indent=2)}
"""
        else: # Custom query
            prompt = f"""
The user has asked the following question about {target_uni}'s digital performance:
"{custom_prompt}"

Here is the crawled SEO telemetry data for {target_uni}:
{json.dumps(target_data, indent=2)}

Please answer their query comprehensively using the telemetry data above.
"""
            
        if api_key.strip():
            # Live API Mode
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key.strip())
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                with st.spinner("🤖 Dispatching agent to analyze telemetry... Please wait."):
                    response = model.generate_content(prompt)
                    st.success("✦ Sentinel Agent dispatch successful!")
                    st.markdown(response.text)
            except Exception as ex:
                st.error(f"⛔ Gemini API Error: {ex}")
                st.info("Check your API key and network connection, or clear the key to run in Simulation Mode.")
        else:
            # Simulation/Fallback Mode
            with st.spinner("🤖 Simulating Sentinel Agent analysis... Please wait."):
                time.sleep(1.0)
                
            st.success("✦ Sentinel Agent simulation complete!")
            
            if preset == "Draft engineering tickets (Jira/GitHub) for audit fixes":
                h1_status = "Missing" if target_data.get("h1_count", 0) == 0 else f"{target_data.get('h1_count')} detected"
                ttfb = target_data.get("ttfb_ms", 0)
                missing_alt = target_data.get("missing_alt_count", 0)
                total_img = target_data.get("total_images", 0)
                
                sim_output = f"""
### 🛠️ [SIMULATION MODE] GENERATED ENGINEERING TICKETS FOR {target_uni.upper()}

#### **TICKET-01: Fix Missing/Incorrect Heading Hierarchy**
* **Priority:** 🔴 Critical
* **Title:** Resolve Heading Outline Violations on Homepage
* **Problem Statement:** Homepage currently reports **{h1_status} H1 tags**. Search engines require exactly one H1 tag on the homepage to establish the primary context of the page.
* **Resolution Steps:**
  1. Audit existing headers (`<h1>`, `<h2>`, `<h3>`).
  2. Ensure there is exactly one `<h1>` wrapping the main brand name or primary value proposition (e.g. `<h1>SABS University of Art, Design and Heritages</h1>`).
  3. Demote any secondary headings to `<h2>` or `<h3>` as appropriate.
* **Acceptance Criteria:** Exactly 1 `<h1>` element detected in the DOM.

#### **TICKET-02: Fix WCAG Accessibility Alt-Text Violations**
* **Priority:** 🟡 High
* **Title:** Implement Alt-Text for Images on Homepage
* **Problem Statement:** Found **{missing_alt} out of {total_img} images** missing `alt` description attributes on the homepage, violating WCAG 2.1 Level A compliance and hurting Google Image Search optimization.
* **Resolution Steps:**
  1. Locate all `<img>` tags missing the `alt` attribute.
  2. Implement descriptive, keyword-rich `alt` text for each image.
  3. Ensure decorative images have an empty `alt=""` attribute so they are skipped by screen readers.
* **Acceptance Criteria:** `st.metric("IMAGES MISSING ALT")` returns 0 on re-crawl.

#### **TICKET-03: Optimize Server Response Time (TTFB)**
* **Priority:** 🟡 High
* **Title:** Improve Server Configuration to Reduce TTFB to <200ms
* **Problem Statement:** Homepage Time-to-First-Byte (TTFB) is currently clocked at **{ttfb} ms**. Google Core Web Vitals recommend a TTFB of less than 200ms for optimal user experience and ranking signals.
* **Resolution Steps:**
  1. Implement server-side caching or page caching for the homepage.
  2. Optimize database query execution times.
  3. Use a Content Delivery Network (CDN) to serve static assets.
* **Acceptance Criteria:** Server response time (TTFB) consistently below 300ms.
"""
            elif preset == "Rewrite Meta Title and Description for target keywords":
                keywords_val = keywords if keywords else "art school karachi, fine arts admissions SABS"
                sim_output = f"""
### ✍️ [SIMULATION MODE] OPTIMIZED META DATA FOR {target_uni.upper()}

**Target Keywords:** *{keywords_val}*

---

#### **Title Options (Target: 50–60 characters)**
1. `SABS University Admissions | Leading Art & Design School Karachi` (60 ch) — **[RECOMMENDED]**
2. `Fine Arts & Design Programs | SABS University Karachi` (53 ch)
3. `Study Fine Arts, Design & Heritage | SABS University Pakistan` (58 ch)

#### **Meta Description Options (Target: 150–160 characters)**
1. `Apply to SABS University, Pakistan's premier art school in Karachi. Explore world-class programs in Fine Arts, Communication Design, and Heritage. Register today.` (160 ch) — **[RECOMMENDED]**
2. `Discover SABS University Karachi. Offering professional degrees in Fine Arts and Design. Learn from top faculty in a creative, inspiring environment. Apply now.` (154 ch)
3. `Unlock your creative potential at SABS University. Study Fine Arts, Textile Design, and Architecture. View our admissions criteria, fee structure, and apply.` (156 ch)

#### **🔍 Google SERP Snippet Preview**
<div style="background-color:#ffffff; color:#1a0dab; font-family:arial,sans-serif; padding:15px; border-radius:8px; border:1px solid #dadce0; max-width:600px; margin:10px 0;">
    <h3 style="margin:0; font-size:20px; font-weight:normal; line-height:1.3; color:#1a0dab;">SABS University Admissions | Leading Art & Design School Karachi</h3>
    <div style="color:#006621; font-size:14px; line-height:1.3; margin-top:2px;">https://sabsu.edu.pk</div>
    <div style="color:#545454; font-size:14px; line-height:1.4; margin-top:4px;">Apply to SABS University, Pakistan's premier art school in Karachi. Explore world-class programs in Fine Arts, Communication Design, and Heritage. Register today.</div>
</div>
"""
            elif preset == "Draft executive strategy summary comparing SABS and competitors":
                sim_output = f"""
### 📊 [SIMULATION MODE] EXECUTIVE COMPETITIVE SEO STRATEGY REPORT

#### **1. Digital League Summary**
* **Protagonist:** {target_uni} (Global Score: **{target_data.get('global_score', 0)}/100**)
* **Competitors:**
"""
                for name, comp_data in all_data.items():
                    if name != target_uni:
                        sim_output += f"  - **{name}:** Global Score: **{comp_data.get('global_score', 0)}/100** (TTFB: {comp_data.get('ttfb_ms', 0)}ms)\n"
                        
                sim_output += f"""
#### **2. SWOT Analysis for {target_uni}**
* **Strengths:** Structured DOM outlines (if headings are correct), standard SSL implementation.
* **Weaknesses:** Sub-optimal page speed (TTFB: **{target_data.get('ttfb_ms', 0)}ms**), missing alt text on images (**{target_data.get('missing_alt_count', 0)}** missing attributes), and lack of JSON-LD Schema markup.
* **Opportunities:** Capture search share-of-voice (SOV) for keywords like *'Best Fine Arts Degree Karachi'* by implementing localized Schema markup and resolving basic homepage meta discrepancies.
* **Threats:** Competitors with faster response times and higher domain authority (like NCA Lahore) ranking higher on high-volume queries due to superior SEO health signals.

#### **3. Roadmap to Digital Dominance**
1. **Tech SEO Foundation (Days 1–7):** Add JSON-LD LocalBusiness or College schema markup to homepage to help Google map coordinates, contact details, and courses.
2. **On-Page Optimization (Days 8–14):** Rewrite and deploy the recommended Meta Title and Description. Resolve the homepage heading tag counts.
3. **Core Web Vitals & Image Optimization (Days 15–30):** Compress and add alt descriptions to all homepage image assets. Implement aggressive server-side caching.
"""
            else: # Custom query
                sim_output = f"""
### 💬 [SIMULATION MODE] CUSTOM QUERY RESPONSE FOR {target_uni.upper()}

**Your Query:** *"{custom_prompt}"*

**Agent Analysis:**
Because you are running in Simulation Mode, the Gemini API was not invoked. However, checking our local telemetry databases for **{target_uni}**, here is the relevant analysis:
- **Global Score:** {target_data.get('global_score', 0)}/100 (SEO Category Scores: {json.dumps(target_data.get('scores', {}))})
- **TTFB Performance:** {target_data.get('ttfb_ms', 0)} ms
- **Structural Quality:** {target_data.get('h1_count', 0)} H1 tag(s), {target_data.get('h2_count', 0)} H2 tag(s), and {target_data.get('h3_count', 0)} H3 tag(s).
- **Accessibility:** {target_data.get('missing_alt_count', 0)} images out of {target_data.get('total_images', 0)} are missing alternative text descriptions.

*Tip: Add a valid Gemini API Key above to unlock custom free-form conversation and deeper analytical synthesis.*
"""
            st.markdown(sim_output)


# ==============================================================================
#  SECTION 10: MAIN ROUTER
# ==============================================================================

all_data  = st.session_state.get("all_data",  None)
url_map   = st.session_state.get("url_map", {})
sabs_name = list(url_map.keys())[0] if url_map else "SABS University"
sabs_data = (all_data or {}).get(sabs_name, None)

if all_data is None:
    render_launcher_ui()
else:
    # Header with a small expander to adjust settings and download report
    col_hdr_a, col_hdr_b = st.columns([3, 1])
    with col_hdr_a:
        _md(f"""
        <div style="padding-top:0.4rem;">
            <span style="font-family:'Orbitron',monospace;font-size:1.8rem;font-weight:900;color:#00d4ff;text-shadow:0 0 10px rgba(0,212,255,0.5);letter-spacing:0.12em;">⚔ SENTINEL</span>
            <span style="font-family:'Share Tech Mono',monospace;font-size:0.75rem;color:#3d5a73;margin-left:1rem;letter-spacing:0.15em;">v1.0 SCAN COMPLETE — PRIMARY TARGET: {sabs_name.upper()}</span>
        </div>
        """)
    with col_hdr_b:
        pdf_bytes = generate_pdf_report(all_data, url_map)
        st.download_button(
            label="💾  DOWNLOAD PDF REPORT",
            data=pdf_bytes,
            file_name=f"sentinel_seo_report_{sabs_name.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    st.markdown("<div style='border-bottom:1px solid rgba(0,212,255,0.15);margin-bottom:1.5rem;margin-top:0.5rem;'></div>", unsafe_allow_html=True)

    with st.expander("🛠️ ADJUST TARGETS & RE-SCAN", expanded=False):
        render_launcher_ui(is_re_run=True)

    # Main navigation tabs
    tab_war_room, tab_deep_audit, tab_prescription, tab_ai_agent = st.tabs([
        "⚔️  THE WAR ROOM",
        f"🔬  {get_uni_short(sabs_name).upper()} DEEP AUDIT",
        "💊  PRESCRIPTION ENGINE",
        "🤖  AI AGENT ASSISTANT"
    ])

    with tab_war_room:
        render_war_room(all_data)

    with tab_deep_audit:
        if sabs_data is None:
            st.warning(f"No {get_uni_short(sabs_name)} data available.")
        elif "error" in sabs_data:
            st.error(f"⛔  Could not reach {sabs_name}: {sabs_data['error']}")
        else:
            sub_tab_audit, sub_tab_sitemap = st.tabs(["📄 PAGE-LEVEL DIAGNOSTICS", "🔗 SITEMAP.XML DEPTH SCANNER"])
            with sub_tab_audit:
                render_deep_audit(sabs_data, sabs_name)
            with sub_tab_sitemap:
                render_sitemap_scanner(sabs_name, url_map.get(sabs_name, ""))

    with tab_prescription:
        if sabs_data is None:
            st.warning(f"No {get_uni_short(sabs_name)} data available.")
        elif "error" in sabs_data:
            st.error(f"⛔  Could not reach {sabs_name}: {sabs_data['error']}")
        else:
            render_prescription_engine(sabs_data, sabs_name)

    with tab_ai_agent:
        render_ai_agent(all_data, url_map)
