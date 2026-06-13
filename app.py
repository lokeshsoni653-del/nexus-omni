# ==============================================================================
#  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗     ██████╗ ███╗   ███╗███╗   ██╗██╗
#  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝    ██╔═══██╗████╗ ████║████╗  ██║██║
#  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗    ██║   ██║██╔████╔██║██╔██╗ ██║██║
#  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║    ██║   ██║██║╚██╔╝██║██║╚██╗██║██║
#  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║    ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║
#  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝     ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝
#
#  NEXUS OMNI: Enterprise SEO Telemetry Suite
#  Author     : Engineered for SABS University Digital Marketing Assessment
#  Version    : 3.1.0 — Cloud-Compatible Release (HTML rendering fix)
#  Description: A single-file, multi-page Streamlit application that performs
#               real-time DOM architecture analysis, semantic NLP profiling,
#               and comprehensive SEO health diagnostics on any target URL.
#
#  BUGFIX v3.1.0: Added _md() helper to strip leading indentation whitespace
#  from all HTML strings before passing to st.markdown(). Streamlit's CommonMark
#  parser treats lines with 4+ leading spaces as code blocks, causing raw HTML
#  to render as plain text. .strip() ensures the HTML tag starts at column 0.
# ==============================================================================

# ── Standard Library ──────────────────────────────────────────────────────────
import re
import time
import json
import textwrap
import warnings
from collections import Counter
from urllib.parse import urljoin, urlparse

# ── Third-Party: Core ─────────────────────────────────────────────────────────
import requests
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from bs4 import BeautifulSoup

# ── Third-Party: NLP & Readability ────────────────────────────────────────────
import textstat
from textblob import TextBlob
import nltk
from nltk.corpus import stopwords
from nltk.util import ngrams

warnings.filterwarnings("ignore")

# ── NLTK Bootstrap ────────────────────────────────────────────────────────────
# SEO RATIONALE: NLTK stopwords are critical for lexical density analysis.
# Filtering out semantically empty words (the, and, is) isolates the
# meaningful keywords that search engines use for topical relevance scoring.
@st.cache_resource(show_spinner=False)
def _bootstrap_nltk():
    """Download required NLTK corpora once per session (cached at resource level)."""
    for corpus in ["stopwords", "punkt", "punkt_tab", "averaged_perceptron_tagger"]:
        try:
            nltk.download(corpus, quiet=True)
        except Exception:
            pass

_bootstrap_nltk()

# ==============================================================================
#  SECTION 1: GLOBAL PAGE CONFIGURATION & CUSTOM CSS INJECTION
# ==============================================================================

st.set_page_config(
    page_title="NEXUS OMNI · Enterprise SEO Telemetry",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CRITICAL RENDERING HELPER ─────────────────────────────────────────────────
# ROOT CAUSE FIX: Streamlit's CommonMark parser renders lines with 4+ leading
# spaces as fenced code blocks. Multi-line f-strings inside indented Python
# functions inherit that indentation in the string content itself. Using
# textwrap.dedent() + strip() guarantees the HTML tag is always at column 0,
# which CommonMark requires for HTML block recognition.
def _md(html: str) -> None:
    """Strip leading indentation and render HTML via st.markdown safely."""
    st.markdown(textwrap.dedent(html).strip(), unsafe_allow_html=True)


# ── Cyberpunk / Glassmorphism CSS Injection ────────────────────────────────────
CYBER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Inter:wght@300;400;500;600&display=swap');

:root {
    --bg-abyss:       #020509;
    --bg-deep:        #060d14;
    --bg-surface:     #0a1628;
    --bg-glass:       rgba(10, 22, 40, 0.75);
    --border-neon:    rgba(0, 212, 255, 0.35);
    --border-subtle:  rgba(0, 212, 255, 0.12);
    --accent-cyan:    #00d4ff;
    --accent-blue:    #0066ff;
    --accent-green:   #00ff88;
    --accent-amber:   #ffb800;
    --accent-red:     #ff2d55;
    --text-primary:   #e8f4f8;
    --text-secondary: #7a9bb5;
    --text-dim:       #3d5a73;
    --font-mono:      'Share Tech Mono', monospace;
    --font-ui:        'Inter', sans-serif;
    --font-title:     'Orbitron', monospace;
    --glow-cyan:      0 0 8px rgba(0,212,255,0.6), 0 0 20px rgba(0,212,255,0.25);
    --glow-green:     0 0 8px rgba(0,255,136,0.6), 0 0 20px rgba(0,255,136,0.2);
    --glow-red:       0 0 8px rgba(255,45,85,0.6),  0 0 20px rgba(255,45,85,0.2);
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: var(--bg-abyss) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-ui) !important;
}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
    z-index: 0;
}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #030810 0%, #050e1a 100%) !important;
    border-right: 1px solid var(--border-neon) !important;
    box-shadow: 4px 0 30px rgba(0,212,255,0.08) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: rgba(0,212,255,0.06) !important;
    border: 1px solid var(--border-neon) !important;
    border-radius: 6px !important;
    color: var(--accent-cyan) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
}
[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
    box-shadow: var(--glow-cyan) !important;
    border-color: var(--accent-cyan) !important;
}

.stButton > button {
    background: linear-gradient(135deg, rgba(0,102,255,0.15), rgba(0,212,255,0.15)) !important;
    border: 1px solid var(--accent-cyan) !important;
    border-radius: 6px !important;
    color: var(--accent-cyan) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    width: 100% !important;
    padding: 0.6rem 1rem !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0,102,255,0.35), rgba(0,212,255,0.35)) !important;
    box-shadow: var(--glow-cyan) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stMetric"] {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-neon) !important;
    border-radius: 10px !important;
    padding: 1.2rem 1.4rem !important;
    position: relative !important;
    overflow: hidden !important;
    backdrop-filter: blur(12px) !important;
    transition: border-color 0.3s ease !important;
}
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
}
[data-testid="stMetric"]:hover {
    border-color: var(--accent-cyan) !important;
    box-shadow: var(--glow-cyan) !important;
}
[data-testid="stMetricLabel"] {
    font-family: var(--font-mono) !important;
    font-size: 0.72rem !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-title) !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: var(--accent-cyan) !important;
    text-shadow: var(--glow-cyan) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--border-neon) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

.streamlit-expander {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-neon) !important;
    border-radius: 8px !important;
}

[data-testid="stRadio"] label {
    background: rgba(0,212,255,0.04) !important;
    border: 1px solid var(--border-subtle) !important;
    border-radius: 6px !important;
    padding: 0.5rem 0.8rem !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    font-family: var(--font-mono) !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.05em !important;
}
[data-testid="stRadio"] label:hover {
    border-color: var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
    background: rgba(0,212,255,0.08) !important;
}

hr { border-color: var(--border-neon) !important; opacity: 0.5 !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.25); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }
</style>
"""
st.markdown(CYBER_CSS, unsafe_allow_html=True)


# ==============================================================================
#  SECTION 2: DATA EXTRACTION ENGINE
# ==============================================================================

_PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Share Tech Mono, monospace", color="#7a9bb5", size=11),
    margin=dict(l=20, r=20, t=40, b=20),
)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_and_parse(url: str) -> dict:
    """
    Master scraping function — fetches HTML, measures TTFB, and delegates
    to specialised parsers. Cached for 5 minutes to avoid hammering the
    target server on every rerun.

    SEO RATIONALE: Every extracted data point maps to a concrete ranking
    factor in Google's Quality Evaluator Guidelines or Core Web Vitals spec.

    Returns a flat dictionary of all extracted signals.
    On failure, returns {"error": <message>} for graceful UI degradation.
    """
    result = {}

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; NEXUSBot/3.0; +https://nexus-omni.io) "
            "AppleWebKit/537.36 KHTML like Gecko Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }

    # ── 1. TTFB Measurement ───────────────────────────────────────────────────
    # SEO RATIONALE: Time to First Byte is a direct Core Web Vitals signal.
    # Google has confirmed TTFB > 600ms negatively impacts crawl budget and
    # UX scores. Measured from request dispatch to first response byte.
    try:
        t_start = time.perf_counter()
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True, verify=True)
        ttfb_ms = (time.perf_counter() - t_start) * 1000
        response.raise_for_status()
    except requests.exceptions.SSLError:
        try:
            t_start = time.perf_counter()
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True, verify=False)
            ttfb_ms = (time.perf_counter() - t_start) * 1000
            response.raise_for_status()
        except Exception as e:
            return {"error": f"SSL failure and unverified retry also failed: {e}"}
    except requests.exceptions.ConnectionError as e:
        return {"error": f"Connection refused or DNS lookup failure. Target may be offline. [{e}]"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out after 15 seconds. The server may be under load or geo-blocked."}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {response.status_code} error returned. [{e}]"}
    except Exception as e:
        return {"error": f"Unexpected network error: {e}"}

    result["ttfb_ms"] = round(ttfb_ms, 1)
    result["status_code"] = response.status_code
    result["final_url"] = response.url
    result["content_type"] = response.headers.get("Content-Type", "unknown")
    result["content_size_kb"] = round(len(response.content) / 1024, 1)

    # ── 2. HTML Parsing ───────────────────────────────────────────────────────
    # SEO RATIONALE: lxml is 2–5× faster than html.parser and handles
    # malformed HTML more gracefully, reducing false negatives in analysis.
    try:
        soup = BeautifulSoup(response.text, "lxml")
    except Exception:
        soup = BeautifulSoup(response.text, "html.parser")

    # ── 3. Meta Architecture Extraction ──────────────────────────────────────
    # SEO RATIONALE: <title> is the #1 on-page ranking factor.
    # Meta description drives CTR in SERPs — indirectly feeds quality signals.
    title_tag = soup.find("title")
    result["title"] = title_tag.get_text(strip=True) if title_tag else ""
    result["title_len"] = len(result["title"])

    desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    result["description"] = desc_tag.get("content", "").strip() if desc_tag else ""
    result["desc_len"] = len(result["description"])

    # ── 4. Canonical & Robots ─────────────────────────────────────────────────
    canonical_tag = soup.find("link", rel=lambda r: r and "canonical" in r)
    result["canonical"] = canonical_tag.get("href", "") if canonical_tag else ""

    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    result["robots_meta"] = robots_tag.get("content", "") if robots_tag else ""

    # ── 5. Heading Hierarchy ──────────────────────────────────────────────────
    # SEO RATIONALE: A single H1 is the page's topical declaration to
    # Googlebot. H2/H3 expand topical authority through structured context.
    headings = []
    for level in ["h1", "h2", "h3"]:
        for tag in soup.find_all(level):
            text = tag.get_text(strip=True)
            if text:
                headings.append({"level": level.upper(), "text": text})

    result["headings"] = headings
    result["h1_count"] = sum(1 for h in headings if h["level"] == "H1")
    result["h2_count"] = sum(1 for h in headings if h["level"] == "H2")
    result["h3_count"] = sum(1 for h in headings if h["level"] == "H3")

    # ── 6. Image Alt-Text Audit ───────────────────────────────────────────────
    # SEO RATIONALE: Alt text is how search engines understand image content.
    # Missing alt attributes violate WCAG 2.1 and miss keyword injection
    # opportunities for Google Image Search — an extra organic traffic channel.
    all_imgs = soup.find_all("img")
    missing_alt_urls = []
    for img in all_imgs:
        alt = img.get("alt")
        if alt is None or alt.strip() == "":
            src = img.get("src", img.get("data-src", ""))
            missing_alt_urls.append(urljoin(url, src) if src else "[inline / no src]")

    result["total_images"] = len(all_imgs)
    result["missing_alt_count"] = len(missing_alt_urls)
    result["missing_alt_urls"] = missing_alt_urls

    # ── 7. Link Architecture ──────────────────────────────────────────────────
    parsed_base = urlparse(url)
    internal_links, external_links = 0, 0
    for a in soup.find_all("a", href=True):
        parsed_href = urlparse(a["href"])
        if parsed_href.netloc == "" or parsed_href.netloc == parsed_base.netloc:
            internal_links += 1
        elif parsed_href.scheme in ("http", "https"):
            external_links += 1

    result["internal_links"] = internal_links
    result["external_links"] = external_links

    # ── 8. Schema & OpenGraph Detection ──────────────────────────────────────
    # SEO RATIONALE: JSON-LD enables Rich Results (star ratings, FAQs,
    # breadcrumbs) boosting CTR by 20-30%. OpenGraph controls social previews.
    og_tags = {}
    for meta in soup.find_all("meta"):
        prop = meta.get("property", "")
        if prop.startswith("og:"):
            og_tags[prop] = meta.get("content", "")

    json_ld_blocks = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            json_ld_blocks.append(json.loads(script.string or "{}"))
        except (json.JSONDecodeError, TypeError):
            pass

    result["og_tags"] = og_tags
    result["has_og_title"] = "og:title" in og_tags
    result["has_og_description"] = "og:description" in og_tags
    result["has_og_image"] = "og:image" in og_tags
    result["has_json_ld"] = len(json_ld_blocks) > 0
    result["json_ld_types"] = [b.get("@type", "Unknown") for b in json_ld_blocks if isinstance(b, dict)]

    # ── 9. HTML5 Semantic Landmarks ───────────────────────────────────────────
    # SEO RATIONALE: Landmarks help Googlebot identify page regions and
    # prioritise which content to crawl. Pages with clear landmarks rank better.
    semantic_tags = ["header", "main", "nav", "footer", "article", "section", "aside"]
    semantic_present = {tag: bool(soup.find(tag)) for tag in semantic_tags}
    result["semantic_tags"] = semantic_present
    result["semantic_score"] = sum(semantic_present.values())

    # ── 10. Body Text Extraction ──────────────────────────────────────────────
    for noise in soup(["script", "style", "noscript", "template", "iframe"]):
        noise.decompose()
    raw_text = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True)).strip()
    result["raw_text"] = raw_text
    result["word_count"] = len(raw_text.split())

    # ── 11. Readability Scoring ───────────────────────────────────────────────
    # SEO RATIONALE: Flesch-Kincaid score measures content accessibility.
    # Scores 60-70 target general audiences. High complexity raises bounce
    # rate — a negative UX signal that depresses rankings via behaviour data.
    if result["word_count"] > 30:
        result["fk_reading_ease"] = round(textstat.flesch_reading_ease(raw_text), 1)
        result["fk_grade_level"] = round(textstat.flesch_kincaid_grade(raw_text), 1)
        result["gunning_fog"] = round(textstat.gunning_fog(raw_text), 1)
    else:
        result["fk_reading_ease"] = None
        result["fk_grade_level"] = None
        result["gunning_fog"] = None

    # ── 12. Sentiment Analysis ────────────────────────────────────────────────
    # SEO RATIONALE: Positive tone correlates with lower bounce rates and
    # higher dwell time — indirect behavioural ranking signals for Google.
    try:
        blob = TextBlob(raw_text[:5000])
        result["sentiment_polarity"] = round(blob.sentiment.polarity, 4)
        result["sentiment_subjectivity"] = round(blob.sentiment.subjectivity, 4)
    except Exception:
        result["sentiment_polarity"] = 0.0
        result["sentiment_subjectivity"] = 0.0

    # ── 13. Keyword Extraction ────────────────────────────────────────────────
    result["keywords_df"] = _extract_keywords(raw_text)

    # ── 14. Health Score ──────────────────────────────────────────────────────
    result["scores"] = _compute_health_scores(result)
    result["global_score"] = min(100, round(sum(result["scores"].values()) / len(result["scores"]) * 100 / 25, 1))

    return result


def _extract_keywords(text: str, top_n: int = 15) -> pd.DataFrame:
    """Tokenise, remove stopwords, compute bigram/trigram frequency."""
    try:
        stop_words = set(stopwords.words("english"))
    except LookupError:
        stop_words = {"the","a","an","and","or","but","in","on","at","to","for","of","with",
                      "is","are","was","were","be","been","have","has","had","do","does","did",
                      "will","would","could","should","may","might","it","its","this","that",
                      "these","those","we","our","us","you","your","he","she","they","their",
                      "them","what","which","who","not","also","as","from"}

    tokens = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", text) if w.lower() not in stop_words]
    combined = Counter(" ".join(g) for g in ngrams(tokens, 2)) + Counter(" ".join(g) for g in ngrams(tokens, 3))
    top = combined.most_common(top_n)

    if not top:
        return pd.DataFrame(columns=["Keyword", "Frequency"])
    df = pd.DataFrame(top, columns=["Keyword", "Frequency"])
    df["Keyword"] = df["Keyword"].str.title()
    return df


def _compute_health_scores(r: dict) -> dict:
    """Compute four pillar scores (0-25 each) for radar chart and global KPI."""
    scores = {"Meta Health": 0, "DOM Structure": 0, "Accessibility": 0, "Content Quality": 0}

    # Meta Health
    mp = 0
    if r.get("title"):
        mp += 8
        mp += 5 if 50 <= r["title_len"] <= 60 else 2
    if r.get("description"):
        mp += 7
        mp += 5 if 150 <= r["desc_len"] <= 160 else 2
    scores["Meta Health"] = min(25, mp)

    # DOM Structure
    dp = 0
    if r.get("h1_count") == 1:   dp += 10
    elif r.get("h1_count", 0) > 1: dp += 2
    if r.get("h2_count", 0) >= 2: dp += 6
    if r.get("h3_count", 0) >= 1: dp += 3
    dp += min(6, r.get("semantic_score", 0))
    scores["DOM Structure"] = min(25, dp)

    # Accessibility
    ap = 0
    total = r.get("total_images", 0)
    miss = r.get("missing_alt_count", 0)
    ap += 15 if total == 0 else round((1 - miss / total) * 15)
    ap += 10 if r.get("internal_links", 0) >= 10 else (5 if r.get("internal_links", 0) >= 3 else 0)
    scores["Accessibility"] = min(25, ap)

    # Content Quality
    cp = 0
    wc = r.get("word_count", 0)
    cp += 8 if wc >= 800 else (4 if wc >= 300 else (2 if wc >= 100 else 0))
    fk = r.get("fk_reading_ease")
    if fk is not None:
        cp += 7 if 50 <= fk <= 70 else (4 if fk > 70 else 2)
    if r.get("has_json_ld"): cp += 5
    if r.get("has_og_title") and r.get("has_og_description"): cp += 5
    scores["Content Quality"] = min(25, cp)

    return scores


# ==============================================================================
#  SECTION 3: SIDEBAR
# ==============================================================================

with st.sidebar:
    _md("""
    <div style="font-family:'Orbitron',monospace;font-size:1.1rem;font-weight:900;
    color:#00d4ff;text-shadow:0 0 8px rgba(0,212,255,0.6);letter-spacing:0.1em;
    text-align:center;padding:0.5rem 0;">⬡ NEXUS OMNI</div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;color:#1e3a4a;
    letter-spacing:0.12em;text-align:center;margin-top:-0.3rem;margin-bottom:1rem;">
    ENTERPRISE SEO TELEMETRY v3.1</div>
    """)
    st.markdown("---")

    _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.4rem;">▸ Target Acquisition</div>')

    target_url = st.text_input(
        "Target URL",
        value="https://www.sabs.edu.pk",
        placeholder="https://example.com",
        label_visibility="collapsed",
    )

    run_btn = st.button("⚡  INITIATE TELEMETRY SCAN", use_container_width=True)

    st.markdown("---")
    _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.5rem;">▸ Navigation Matrix</div>')

    page = st.radio(
        "Navigation",
        options=[
            "🚨  EXECUTIVE HUD",
            "⚙️  DOM STRUCTURAL AUDIT",
            "🧠  SEMANTIC NLP ENGINE",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    if "seo_data" in st.session_state and "error" not in st.session_state.seo_data:
        d = st.session_state.seo_data
        _md(f"""
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#3d5a73;line-height:1.8;">
        <span style="color:#00d4ff;">■</span> STATUS: ONLINE<br>
        <span style="color:#00d4ff;">■</span> TTFB: {d.get('ttfb_ms','—')} ms<br>
        <span style="color:#00d4ff;">■</span> SCORE: {d.get('global_score','—')}/100<br>
        <span style="color:#00d4ff;">■</span> WORDS: {d.get('word_count',0):,}
        </div>
        """)
    else:
        _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.72rem;color:#3d5a73;">■ AWAITING TARGET URL</div>')

    st.markdown("<br>", unsafe_allow_html=True)
    _md("""
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.6rem;color:#1e3a4a;
    text-align:center;line-height:1.6;">
    NEXUS OMNI · SABS ASSESSMENT<br>© 2026 · PROPRIETARY TELEMETRY PLATFORM
    </div>
    """)


# ==============================================================================
#  SECTION 4: DATA PIPELINE TRIGGER
# ==============================================================================

if run_btn:
    if not target_url.strip():
        st.error("⛔  No target URL detected. Enter a valid URL in the sidebar.")
    elif not re.match(r"^https?://", target_url.strip()):
        st.warning("⚠️  URL must begin with http:// or https://")
    else:
        with st.spinner("🔍  Dispatching telemetry probes … parsing DOM architecture …"):
            seo_data = fetch_and_parse(target_url.strip())
        st.session_state["seo_data"] = seo_data
        st.session_state["scanned_url"] = target_url.strip()
        if "error" in seo_data:
            st.error(f"⛔  TELEMETRY FAILURE — {seo_data['error']}")


# ==============================================================================
#  SECTION 5: PAGE RENDER FUNCTIONS
# ==============================================================================

def _no_data_warning():
    _md("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
    height:60vh;gap:1rem;text-align:center;">
    <div style="font-family:'Orbitron',monospace;font-size:3rem;color:rgba(0,212,255,0.15);letter-spacing:0.2em;">⬡</div>
    <div style="font-family:'Orbitron',monospace;font-size:1rem;color:rgba(0,212,255,0.5);letter-spacing:0.2em;text-transform:uppercase;">AWAITING TARGET ACQUISITION</div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;color:#3d5a73;max-width:400px;line-height:1.7;">
    Enter a URL in the sidebar panel and click<br>
    <span style="color:#00d4ff;">⚡ INITIATE TELEMETRY SCAN</span><br>
    to begin the diagnostic sequence.
    </div>
    </div>
    """)


def _error_panel(msg: str):
    _md(f"""
    <div style="border:1px solid #ff2d55;border-radius:10px;padding:1.5rem;
    background:rgba(255,45,85,0.06);margin-top:1rem;">
    <div style="font-family:'Orbitron',monospace;font-size:0.85rem;color:#ff2d55;
    letter-spacing:0.15em;margin-bottom:0.6rem;">⚠  TELEMETRY FAILURE — NETWORK EXCEPTION</div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.78rem;color:#7a9bb5;line-height:1.8;">{msg}</div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;color:#3d5a73;margin-top:0.8rem;">
    ■ Verify the URL is publicly accessible<br>
    ■ Confirm the server is not geo-restricted<br>
    ■ Try an alternative URL (with or without www.)
    </div>
    </div>
    """)


# ── Shared UI helpers ─────────────────────────────────────────────────────────
def _section_header(title: str):
    _md(f'<div style="font-family:\'Orbitron\',monospace;font-size:0.75rem;font-weight:700;color:#00d4ff;letter-spacing:0.25em;text-transform:uppercase;border-bottom:1px solid rgba(0,212,255,0.35);padding-bottom:0.4rem;margin-bottom:1rem;">◈ {title}</div>')


def _page_header(title: str, subtitle: str):
    _md(f'<div style="font-family:\'Orbitron\',monospace;font-size:1.6rem;font-weight:900;color:#00d4ff;text-shadow:0 0 8px rgba(0,212,255,0.6);letter-spacing:0.08em;">{title}</div>')
    _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.78rem;color:#7a9bb5;letter-spacing:0.08em;margin-top:-0.5rem;margin-bottom:1.5rem;">{subtitle}</div>')


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 1: EXECUTIVE HUD
# ──────────────────────────────────────────────────────────────────────────────

def render_executive_hud(d: dict):
    _page_header("EXECUTIVE HUD", f"REAL-TIME TELEMETRY · {st.session_state.get('scanned_url','')}")

    c1, c2, c3, c4, c5 = st.columns(5)
    gs = d.get("global_score", 0)
    ttfb = d.get("ttfb_ms", 0)
    wc = d.get("word_count", 0)
    miss_alt = d.get("missing_alt_count", 0)
    total_imgs = d.get("total_images", 0)
    status = d.get("status_code", "—")

    c1.metric("🎯  GLOBAL HEALTH SCORE", f"{gs}/100",
              "EXCELLENT" if gs >= 80 else ("MODERATE" if gs >= 55 else "CRITICAL"))
    c2.metric("⚡  SERVER TTFB", f"{ttfb} ms",
              "FAST" if ttfb < 200 else ("MODERATE" if ttfb < 600 else "SLOW"))
    c3.metric("📝  TOTAL WORDS", f"{wc:,}",
              "LONG-FORM" if wc >= 800 else ("MEDIUM" if wc >= 300 else "THIN"))
    c4.metric("🖼  IMAGES MISSING ALT", str(miss_alt), f"of {total_imgs} total")
    c5.metric("🌐  HTTP STATUS", str(status), "OK" if status == 200 else "CHECK")

    st.markdown("<br>", unsafe_allow_html=True)

    col_radar, col_tags = st.columns([3, 2], gap="large")

    with col_radar:
        _section_header("SEO HEALTH RADAR — 4-PILLAR ANALYSIS")
        scores = d.get("scores", {})
        cats = list(scores.keys())
        vals = list(scores.values())
        cats_l = cats + [cats[0]]
        vals_l = vals + [vals[0]]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=vals_l, theta=cats_l, fill="toself",
            fillcolor="rgba(0,212,255,0.12)",
            line=dict(color="#00d4ff", width=2.5), name="SEO Score",
            hovertemplate="<b>%{theta}</b><br>Score: %{r}/25<extra></extra>",
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=[25]*len(cats_l), theta=cats_l, fill="toself",
            fillcolor="rgba(0,102,255,0.04)",
            line=dict(color="rgba(0,102,255,0.25)", width=1, dash="dot"),
            name="Target (25)", hoverinfo="skip",
        ))
        fig_radar.update_layout(
            **_PLOTLY_LAYOUT,
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                angularaxis=dict(linecolor="rgba(0,212,255,0.2)", gridcolor="rgba(0,212,255,0.08)",
                                 tickfont=dict(family="Share Tech Mono", color="#7a9bb5", size=11)),
                radialaxis=dict(visible=True, range=[0, 25], gridcolor="rgba(0,212,255,0.08)",
                                linecolor="rgba(0,212,255,0.1)",
                                tickfont=dict(family="Share Tech Mono", color="#3d5a73", size=9),
                                tickvals=[5,10,15,20,25]),
            ),
            legend=dict(x=0.85, y=1.1, font=dict(family="Share Tech Mono", color="#7a9bb5", size=9),
                        bgcolor="rgba(0,0,0,0)"),
            height=380,
        )
        st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

    with col_tags:
        _section_header("HTML5 SEMANTIC LANDMARK AUDIT")
        semantic = d.get("semantic_tags", {})
        tag_desc = {
            "header": "Site Identity Region", "main": "Primary Content Zone",
            "nav": "Navigation Structure", "footer": "Footer Authority Block",
            "article": "Standalone Content Unit", "section": "Thematic Grouping",
            "aside": "Supplemental Context",
        }
        rows = ""
        for tag, present in semantic.items():
            icon = "✦" if present else "✗"
            icon_color = "#00ff88" if present else "#ff2d55"
            badge = '<span style="display:inline-block;background:rgba(0,255,136,0.12);border:1px solid #00ff88;color:#00ff88;font-size:0.65rem;font-weight:700;padding:0.1rem 0.5rem;border-radius:4px;letter-spacing:0.1em;">DETECTED</span>' if present else '<span style="display:inline-block;background:rgba(255,45,85,0.12);border:1px solid #ff2d55;color:#ff2d55;font-size:0.65rem;font-weight:700;padding:0.1rem 0.5rem;border-radius:4px;letter-spacing:0.1em;">MISSING</span>'
            rows += f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.45rem 0.8rem;border-bottom:1px solid rgba(0,212,255,0.07);font-family:\'Share Tech Mono\',monospace;font-size:0.78rem;"><span style="color:{icon_color};font-size:1rem;">{icon}</span><code style="color:#00d4ff;font-size:0.75rem;">&lt;{tag}&gt;</code><span style="color:#7a9bb5;flex:1;">{tag_desc.get(tag,"")}</span>{badge}</div>'

        sem_score = d.get("semantic_score", 0)
        rows += f'<div style="padding:0.5rem 0.8rem;font-family:\'Share Tech Mono\',monospace;font-size:0.72rem;color:#3d5a73;border-top:1px solid rgba(0,212,255,0.1);">COVERAGE: {sem_score}/7 landmarks</div>'
        _md(f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);border-radius:8px;overflow:hidden;">{rows}</div>')

    st.markdown("<br>", unsafe_allow_html=True)
    _section_header("RAPID DIAGNOSTIC TELEMETRY")

    q1, q2, q3, q4, q5, q6 = st.columns(6)
    h1c = d.get("h1_count", 0)
    tl = d.get("title_len", 0)
    dl = d.get("desc_len", 0)

    q1.metric("H1 TAGS", str(h1c), "✦ PASS" if h1c == 1 else ("✗ FAIL" if h1c == 0 else "⚠ WARN"))
    q2.metric("TITLE LENGTH", f"{tl} ch", "✦ PASS" if 50 <= tl <= 60 else ("✗ FAIL" if tl == 0 else "⚠ WARN"))
    q3.metric("META DESC LEN", f"{dl} ch", "✦ PASS" if 150 <= dl <= 160 else ("✗ FAIL" if dl == 0 else "⚠ WARN"))
    q4.metric("JSON-LD SCHEMA", "DETECTED" if d.get("has_json_ld") else "MISSING",
              "✦ PASS" if d.get("has_json_ld") else "✗ FAIL")
    q5.metric("OPEN GRAPH", "ACTIVE" if d.get("has_og_title") else "ABSENT",
              "✦ PASS" if d.get("has_og_title") else "✗ FAIL")
    q6.metric("CANONICAL TAG", "SET" if d.get("canonical") else "ABSENT",
              "✦ PASS" if d.get("canonical") else "⚠ WARN")


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 2: DOM STRUCTURAL AUDIT
# ──────────────────────────────────────────────────────────────────────────────

def render_dom_audit(d: dict):
    _page_header("DOM STRUCTURAL AUDIT", "TECHNICAL BACKEND · METADATA · SCHEMA · ACCESSIBILITY")

    # ── A: Meta Architecture Matrix ───────────────────────────────────────────
    _section_header("META ARCHITECTURE MATRIX")
    ma1, ma2 = st.columns(2, gap="large")

    with ma1:
        title = d.get("title", "")
        tl = d.get("title_len", 0)
        if tl == 0:
            tc, tv = "#ff2d55", "CRITICAL — Title tag absent"
        elif tl < 50:
            tc, tv = "#ffb800", f"TOO SHORT ({tl}/50–60 chars)"
        elif tl > 60:
            tc, tv = "#ffb800", f"TOO LONG ({tl}/50–60 chars)"
        else:
            tc, tv = "#00ff88", f"OPTIMAL ({tl}/50–60 chars)"
        fp = min(100, (tl / 60) * 100)
        _md(f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);border-radius:8px;padding:1.2rem;"><div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.6rem;">▸ &lt;TITLE&gt; TAG</div><div style="font-family:\'Inter\',sans-serif;font-size:0.88rem;color:#e8f4f8;margin-bottom:0.8rem;min-height:2.5rem;word-break:break-all;">"{title if title else "NOT FOUND"}"</div><div style="background:rgba(0,212,255,0.06);border-radius:4px;height:6px;overflow:hidden;margin-bottom:0.5rem;"><div style="height:100%;width:{fp:.0f}%;background:{tc};border-radius:4px;"></div></div><div style="display:flex;justify-content:space-between;font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;"><span>0</span><span style="color:{tc};">{tv}</span><span>60</span></div></div>')

    with ma2:
        desc = d.get("description", "")
        dl = d.get("desc_len", 0)
        if dl == 0:
            dc, dv = "#ff2d55", "CRITICAL — Meta description absent"
        elif dl < 150:
            dc, dv = "#ffb800", f"TOO SHORT ({dl}/150–160 chars)"
        elif dl > 160:
            dc, dv = "#ffb800", f"TOO LONG ({dl}/150–160 chars)"
        else:
            dc, dv = "#00ff88", f"OPTIMAL ({dl}/150–160 chars)"
        fpd = min(100, (dl / 160) * 100)
        _md(f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);border-radius:8px;padding:1.2rem;"><div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.6rem;">▸ META DESCRIPTION</div><div style="font-family:\'Inter\',sans-serif;font-size:0.88rem;color:#e8f4f8;margin-bottom:0.8rem;min-height:2.5rem;word-break:break-all;">"{desc if desc else "NOT FOUND"}"</div><div style="background:rgba(0,212,255,0.06);border-radius:4px;height:6px;overflow:hidden;margin-bottom:0.5rem;"><div style="height:100%;width:{fpd:.0f}%;background:{dc};border-radius:4px;"></div></div><div style="display:flex;justify-content:space-between;font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;"><span>0</span><span style="color:{dc};">{dv}</span><span>160</span></div></div>')

    st.markdown("<br>", unsafe_allow_html=True)
    cr1, cr2 = st.columns(2, gap="large")
    canonical = d.get("canonical", "")
    robots = d.get("robots_meta", "")
    with cr1:
        can_color = "#00d4ff" if canonical else "#ff2d55"
        can_text = f"✦ {canonical}" if canonical else "✗  &lt;link rel='canonical'&gt; NOT FOUND"
        _md(f'<div style="background:rgba(10,22,40,0.6);border:1px solid rgba(0,212,255,0.12);border-radius:8px;padding:1rem 1.2rem;"><span style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;">CANONICAL URL</span><br><span style="font-family:\'Share Tech Mono\',monospace;font-size:0.8rem;color:{can_color};">{can_text}</span></div>')
    with cr2:
        if "noindex" in robots.lower():
            rob_color, rob_text = "#ffb800", "⚠ NOINDEX DETECTED — Page excluded from SERPs"
        elif robots:
            rob_color, rob_text = "#00ff88", f"✦ {robots}"
        else:
            rob_color, rob_text = "#3d5a73", "— No robots meta (defaults to index,follow)"
        _md(f'<div style="background:rgba(10,22,40,0.6);border:1px solid rgba(0,212,255,0.12);border-radius:8px;padding:1rem 1.2rem;"><span style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;">ROBOTS META DIRECTIVE</span><br><span style="font-family:\'Share Tech Mono\',monospace;font-size:0.8rem;color:{rob_color};">{rob_text}</span></div>')

    st.markdown("<br>", unsafe_allow_html=True)

    # ── B: Heading Hierarchy Tree ──────────────────────────────────────────────
    _section_header("HEADING HIERARCHY TREE — DOCUMENT OUTLINE")
    headings = d.get("headings", [])
    h1c = d.get("h1_count", 0)

    if h1c == 0:
        st.error("⚠  CRITICAL — H1 TAG ABSENT: No primary heading found. Google cannot determine the topical focus of this page.")
    elif h1c > 1:
        st.warning(f"⚠  WARNING — MULTIPLE H1 TAGS ({h1c}): Topic authority is diluted. Best practice mandates exactly ONE H1 per page.")
    else:
        st.success("✦  PASS — SINGULAR H1 DETECTED: Heading hierarchy is correctly structured.")

    if headings:
        tree_html = ""
        for h in headings[:40]:
            lvl = h["level"]
            txt = h["text"][:90] + ("…" if len(h["text"]) > 90 else "")
            if lvl == "H1":
                tree_html += f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.9rem;color:#00d4ff;border-left:3px solid #00d4ff;padding:0.35rem 0.8rem;margin:0.2rem 0;background:rgba(0,212,255,0.05);border-radius:0 6px 6px 0;"><span style="opacity:0.5;">H1 ▸</span> {txt}</div>'
            elif lvl == "H2":
                tree_html += f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.82rem;color:#7dd3fc;border-left:3px solid #0ea5e9;padding:0.3rem 0.8rem;margin:0.2rem 0 0.2rem 1.5rem;background:rgba(14,165,233,0.05);border-radius:0 6px 6px 0;"><span style="opacity:0.5;">H2 ▶</span> {txt}</div>'
            else:
                tree_html += f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.75rem;color:#7a9bb5;border-left:3px solid #334e68;padding:0.25rem 0.8rem;margin:0.15rem 0 0.15rem 3rem;background:rgba(51,78,104,0.05);border-radius:0 6px 6px 0;"><span style="opacity:0.5;">H3 ›</span> {txt}</div>'

        if len(headings) > 40:
            tree_html += f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;padding:0.5rem 0.8rem;">… and {len(headings)-40} more nodes</div>'

        _md(f'<div style="background:rgba(6,13,20,0.8);border:1px solid rgba(0,212,255,0.15);border-radius:8px;padding:0.8rem;max-height:350px;overflow-y:auto;">{tree_html}</div>')
    else:
        _md('<div style="font-family:\'Share Tech Mono\',monospace;color:#3d5a73;font-size:0.8rem;padding:1rem;">No heading tags (H1–H3) detected in DOM.</div>')

    _md(f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.72rem;color:#3d5a73;padding:0.4rem 0;">HEADING TOTALS → <span style="color:#00d4ff;">H1: {h1c}</span> · <span style="color:#7dd3fc;">H2: {d.get("h2_count",0)}</span> · <span style="color:#7a9bb5;">H3: {d.get("h3_count",0)}</span></div>')

    st.markdown("<br>", unsafe_allow_html=True)

    # ── C: Schema & OpenGraph Checklist ───────────────────────────────────────
    _section_header("SCHEMA & SOCIAL GRAPH INTELLIGENCE")
    sc1, sc2 = st.columns(2, gap="large")

    def _schema_rows(checks):
        rows = ""
        for tag, present, desc_txt in checks:
            icon = "✦" if present else "✗"
            ic = "#00ff88" if present else "#ff2d55"
            badge = '<span style="display:inline-block;background:rgba(0,255,136,0.12);border:1px solid #00ff88;color:#00ff88;font-size:0.65rem;font-weight:700;padding:0.1rem 0.45rem;border-radius:4px;">ACTIVE</span>' if present else '<span style="display:inline-block;background:rgba(255,45,85,0.12);border:1px solid #ff2d55;color:#ff2d55;font-size:0.65rem;font-weight:700;padding:0.1rem 0.45rem;border-radius:4px;">MISSING</span>'
            rows += f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.45rem 0.8rem;border-bottom:1px solid rgba(0,212,255,0.07);font-family:\'Share Tech Mono\',monospace;font-size:0.78rem;"><span style="color:{ic};font-size:1rem;">{icon}</span><code style="color:#00d4ff;font-size:0.75rem;">{tag}</code><span style="color:#7a9bb5;flex:1;font-size:0.76rem;">{desc_txt}</span>{badge}</div>'
        return rows

    og = d.get("og_tags", {})
    with sc1:
        checks_og = [
            ("og:title",       d.get("has_og_title",       False), "Social share title"),
            ("og:description", d.get("has_og_description", False), "Social preview description"),
            ("og:image",       d.get("has_og_image",       False), "Social preview thumbnail"),
            ("og:url",         "og:url" in og,                     "Canonical social URL"),
            ("og:type",        "og:type" in og,                    "Content type declaration"),
            ("og:site_name",   "og:site_name" in og,               "Brand identity tag"),
        ]
        _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">▸ OpenGraph Protocol (og:) Tags</div>')
        _md(f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);border-radius:8px;overflow:hidden;">{_schema_rows(checks_og)}</div>')

    with sc2:
        json_ld_types = d.get("json_ld_types", [])
        checks_jld = [
            ("JSON-LD Present",   d.get("has_json_ld", False),  "Structured data block detected"),
            ("Schema.org @type",  bool(json_ld_types),           "Entity type declared"),
        ]
        extra = ""
        if json_ld_types:
            extra = f'<div style="padding:0.6rem 0.8rem;font-family:\'Share Tech Mono\',monospace;font-size:0.72rem;color:#00d4ff;border-top:1px solid rgba(0,212,255,0.1);">SCHEMA TYPES: {", ".join(json_ld_types[:5])}</div>'
        _md('<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">▸ JSON-LD Structured Data</div>')
        _md(f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);border-radius:8px;overflow:hidden;">{_schema_rows(checks_jld)}{extra}</div>')

    st.markdown("<br>", unsafe_allow_html=True)

    # ── D: Accessibility Engine ────────────────────────────────────────────────
    _section_header("ACCESSIBILITY ENGINE — IMAGE ALT-TEXT AUDIT")
    total_imgs = d.get("total_images", 0)
    missing_alt = d.get("missing_alt_count", 0)
    missing_urls = d.get("missing_alt_urls", [])

    acc1, acc2, acc3 = st.columns(3)
    acc1.metric("TOTAL IMAGES", str(total_imgs))
    acc2.metric("MISSING ALT TEXT", str(missing_alt),
                "⚠ WCAG VIOLATION" if missing_alt > 0 else "✦ CLEAN")
    acc3.metric("ALT COVERAGE",
                f"{round((1 - missing_alt/max(total_imgs,1))*100)}%",
                "EXCELLENT" if missing_alt == 0 else "NEEDS WORK")

    if missing_urls:
        with st.expander(f"⚠  {missing_alt} IMAGE(S) MISSING ALT — Click to Expand Violation Report"):
            st.info("SEO IMPACT: Each missing alt attribute is a missed keyword injection point AND a WCAG 2.1 Level A violation. Google uses alt text to index images, providing an extra organic traffic channel.")
            df_m = pd.DataFrame({"#": range(1, len(missing_urls)+1), "Image URL (Missing Alt)": missing_urls})
            st.dataframe(df_m, use_container_width=True, hide_index=True)
    elif total_imgs > 0:
        st.success("✦  ALL IMAGES HAVE ALT ATTRIBUTES — Perfect WCAG accessibility compliance.")
    else:
        st.info("ℹ  No <img> elements found in the parsed DOM.")

    st.markdown("<br>", unsafe_allow_html=True)
    _section_header("LINK ARCHITECTURE ANALYSIS")
    la1, la2, la3 = st.columns(3)
    int_l = d.get("internal_links", 0)
    ext_l = d.get("external_links", 0)
    la1.metric("INTERNAL LINKS", str(int_l), "Good PageRank flow" if int_l >= 10 else "Sparse")
    la2.metric("EXTERNAL LINKS", str(ext_l), "Authority signals" if ext_l > 0 else "No outbound")
    la3.metric("PAGE SIZE", f"{d.get('content_size_kb',0)} KB",
               "Optimised" if d.get("content_size_kb", 0) < 500 else "Large")


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 3: SEMANTIC NLP ENGINE
# ──────────────────────────────────────────────────────────────────────────────

def render_nlp_engine(d: dict):
    _page_header("SEMANTIC NLP ENGINE", "LEXICAL ANALYSIS · READABILITY INDEXING · SENTIMENT PROFILING")

    # ── A: Keyword Chart ──────────────────────────────────────────────────────
    _section_header("LEXICAL DENSITY — TOP 15 SEMANTIC KEYWORDS (BI/TRI-GRAM)")
    kw_df = d.get("keywords_df", pd.DataFrame())

    if kw_df is not None and not kw_df.empty:
        fig_kw = px.bar(
            kw_df.sort_values("Frequency"), x="Frequency", y="Keyword",
            orientation="h", color="Frequency",
            color_continuous_scale=[[0.0,"rgba(0,102,255,0.6)"],[0.5,"rgba(0,162,255,0.8)"],[1.0,"#00d4ff"]],
            template="plotly_dark",
        )
        fig_kw.update_layout(
            **_PLOTLY_LAYOUT, height=420, coloraxis_showscale=False,
            xaxis=dict(gridcolor="rgba(0,212,255,0.08)", linecolor="rgba(0,212,255,0.1)",
                       title=dict(text="OCCURRENCE FREQUENCY", font=dict(family="Share Tech Mono", color="#3d5a73", size=10))),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", title=dict(text=""),
                       tickfont=dict(family="Share Tech Mono", color="#7a9bb5", size=10)),
            bargap=0.3,
        )
        fig_kw.update_traces(marker_line_color="rgba(0,212,255,0.3)", marker_line_width=1,
                             hovertemplate="<b>%{y}</b><br>Frequency: %{x}<extra></extra>")
        st.plotly_chart(fig_kw, use_container_width=True, config={"displayModeBar": False})

        with st.expander("▸ View Raw Keyword Data Matrix"):
            kw_show = kw_df.reset_index(drop=True)
            kw_show.index += 1
            st.dataframe(kw_show, use_container_width=True)
    else:
        st.info("Insufficient text content to perform n-gram analysis.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── B: Readability Indexing ────────────────────────────────────────────────
    _section_header("READABILITY INDEXING — FLESCH-KINCAID ANALYSIS")
    st.info("WHY READABILITY IS AN SEO SIGNAL: Pages with Flesch Reading Ease scores of 60–70 correlate with lower bounce rates and higher dwell time — both indirect behavioural signals in Google's ranking algorithm. Content that is too complex (low FKRE) increases abandonment even on authoritative domains.")

    fk_ease = d.get("fk_reading_ease")
    fk_grade = d.get("fk_grade_level")
    fog = d.get("gunning_fog")

    if fk_ease is not None:
        r1, r2, r3 = st.columns(3)
        if fk_ease >= 70:    ease_label, ease_color = "EASY — Mass Audience", "#00ff88"
        elif fk_ease >= 60:  ease_label, ease_color = "STANDARD — Ideal Range", "#00d4ff"
        elif fk_ease >= 50:  ease_label, ease_color = "FAIRLY DIFFICULT", "#ffb800"
        else:                ease_label, ease_color = "DIFFICULT — Expert Level", "#ff2d55"

        r1.metric("FLESCH READING EASE", str(fk_ease), ease_label)
        r2.metric("F-K GRADE LEVEL", f"Grade {fk_grade}", f"US Grade {fk_grade} reading level")
        r3.metric("GUNNING FOG INDEX", str(fog), f"Grade {fog} comprehension needed")

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=fk_ease,
            delta={"reference": 65, "increasing": {"color": "#00ff88"}, "decreasing": {"color": "#ff2d55"}},
            number={"font": {"family": "Orbitron", "color": "#00d4ff", "size": 36}},
            gauge={
                "axis": {"range": [0,100], "tickfont": {"family":"Share Tech Mono","color":"#3d5a73","size":9}},
                "bar": {"color": ease_color, "thickness": 0.25},
                "bgcolor": "rgba(0,0,0,0)",
                "bordercolor": "rgba(0,212,255,0.2)",
                "steps": [
                    {"range":[0,30],  "color":"rgba(255,45,85,0.08)"},
                    {"range":[30,60], "color":"rgba(255,184,0,0.08)"},
                    {"range":[60,80], "color":"rgba(0,212,255,0.08)"},
                    {"range":[80,100],"color":"rgba(0,255,136,0.08)"},
                ],
                "threshold": {"line":{"color":"#00d4ff","width":2},"thickness":0.75,"value":65},
            },
            title={"text":"FLESCH READING EASE SCORE","font":{"family":"Share Tech Mono","color":"#7a9bb5","size":11}},
        ))
        fig_gauge.update_layout(**_PLOTLY_LAYOUT, height=280)
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Insufficient text content (<30 words) to compute readability scores.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── C: Sentiment Analysis ──────────────────────────────────────────────────
    _section_header("CONTENT SENTIMENT PROFILING — PSYCHOLOGICAL TONE ANALYSIS")
    polarity     = d.get("sentiment_polarity", 0.0)
    subjectivity = d.get("sentiment_subjectivity", 0.0)

    if polarity > 0.1:
        s_label, s_color, s_icon = "POSITIVE", "#00ff88", "✦"
        s_desc = "The page projects an optimistic, confident, and welcoming tone — ideal for institutional authority."
    elif polarity < -0.1:
        s_label, s_color, s_icon = "NEGATIVE", "#ff2d55", "✗"
        s_desc = "The page carries a negative or cautionary tone, which may increase bounce rates and reduce engagement dwell time."
    else:
        s_label, s_color, s_icon = "NEUTRAL", "#7a9bb5", "●"
        s_desc = "The page has a factual, informational tone — appropriate for academic content but low in emotional engagement."

    subj_label = "HIGHLY SUBJECTIVE" if subjectivity > 0.6 else ("MIXED" if subjectivity > 0.3 else "OBJECTIVE / FACTUAL")

    sm1, sm2, sm3 = st.columns(3)
    sm1.metric("SENTIMENT TONE",    s_label,     f"Polarity: {polarity:+.4f}")
    sm2.metric("SUBJECTIVITY",      subj_label,  f"Score: {subjectivity:.4f}")
    sm3.metric("CONTENT CONFIDENCE","HIGH" if polarity > 0.05 and subjectivity < 0.5 else "LOW", "")

    # Polarity spectrum bar
    bar_pos = ((polarity + 1) / 2 * 100)
    _md(f"""
    <div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);border-radius:8px;padding:1.2rem;margin-top:0.8rem;">
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:#3d5a73;letter-spacing:0.1em;margin-bottom:0.8rem;">POLARITY SPECTRUM &nbsp; [ −1.0 = NEGATIVE &nbsp;·&nbsp; 0.0 = NEUTRAL &nbsp;·&nbsp; +1.0 = POSITIVE ]</div>
    <div style="position:relative;background:linear-gradient(90deg,rgba(255,45,85,0.3),rgba(255,184,0,0.2),rgba(0,212,255,0.2),rgba(0,255,136,0.3));border-radius:4px;height:10px;overflow:visible;">
    <div style="position:absolute;left:{bar_pos:.1f}%;top:50%;transform:translate(-50%,-50%);width:14px;height:14px;border-radius:50%;background:{s_color};box-shadow:0 0 10px {s_color};border:2px solid #020509;"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-family:'Share Tech Mono',monospace;font-size:0.68rem;color:#3d5a73;margin-top:0.5rem;"><span>NEGATIVE −1.0</span><span>NEUTRAL 0.0</span><span>POSITIVE +1.0</span></div>
    <div style="margin-top:1rem;padding:0.8rem;background:rgba(0,0,0,0.2);border-radius:6px;font-family:'Inter',sans-serif;font-size:0.82rem;color:#e8f4f8;line-height:1.6;border-left:3px solid {s_color};">
    <span style="color:{s_color};font-weight:600;">{s_icon} {s_label}:</span> {s_desc}
    </div>
    </div>
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── D: Summary Matrix ─────────────────────────────────────────────────────
    _section_header("CONTENT QUALITY SUMMARY MATRIX")
    summary_data = {
        "Signal": ["Word Count","Flesch Reading Ease","FK Grade Level","Gunning Fog","Sentiment Polarity","Subjectivity","Keyword Diversity"],
        "Measured Value": [
            f"{d.get('word_count',0):,} words",
            str(fk_ease) if fk_ease else "N/A",
            f"Grade {fk_grade}" if fk_grade else "N/A",
            str(fog) if fog else "N/A",
            f"{polarity:+.4f}", f"{subjectivity:.4f}",
            str(len(kw_df) if kw_df is not None and not kw_df.empty else 0),
        ],
        "Benchmark Target": [
            "≥ 800 words", "60–70", "Grade 8–9", "< 12", "> 0.05", "0.3–0.6", "≥ 10 phrases",
        ],
        "Status": [
            "✦ PASS" if d.get("word_count",0) >= 800 else ("⚠ WARN" if d.get("word_count",0) >= 300 else "✗ FAIL"),
            "✦ PASS" if fk_ease and 60 <= fk_ease <= 70 else ("⚠ WARN" if fk_ease else "✗ FAIL"),
            "✦ PASS" if fk_grade and 8 <= fk_grade <= 9 else "⚠ WARN",
            "✦ PASS" if fog and fog < 12 else "⚠ WARN",
            "✦ PASS" if polarity > 0.05 else "⚠ WARN",
            "✦ PASS" if 0.3 <= subjectivity <= 0.6 else "⚠ WARN",
            "✦ PASS" if kw_df is not None and len(kw_df) >= 10 else "⚠ WARN",
        ],
    }
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)


# ==============================================================================
#  SECTION 6: MAIN ROUTER
# ==============================================================================

seo_data = st.session_state.get("seo_data", None)

if "🚨" in page:
    if seo_data is None:               _no_data_warning()
    elif "error" in seo_data:          _error_panel(seo_data["error"])
    else:                              render_executive_hud(seo_data)

elif "⚙️" in page:
    if seo_data is None:               _no_data_warning()
    elif "error" in seo_data:          _error_panel(seo_data["error"])
    else:                              render_dom_audit(seo_data)

elif "🧠" in page:
    if seo_data is None:               _no_data_warning()
    elif "error" in seo_data:          _error_panel(seo_data["error"])
    else:                              render_nlp_engine(seo_data)
