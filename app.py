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
#  Version    : 3.0.0 — Production Release
#  Description: A single-file, multi-page Streamlit application that performs
#               real-time DOM architecture analysis, semantic NLP profiling,
#               and comprehensive SEO health diagnostics on any target URL.
# ==============================================================================

# ── Standard Library ──────────────────────────────────────────────────────────
import re
import time
import json
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
# We need to filter out semantically "empty" words (the, and, is) to isolate
# the meaningful keywords that search engines actually use for topical relevance.
@st.cache_resource(show_spinner=False)
def _bootstrap_nltk():
    """Download required NLTK corpora once per session (cached at resource level)."""
    for corpus in ["stopwords", "punkt", "punkt_tab", "averaged_perceptron_tagger"]:
        try:
            nltk.download(corpus, quiet=True)
        except Exception:
            pass  # Graceful degradation if network is unavailable

_bootstrap_nltk()

# ==============================================================================
#  SECTION 1: GLOBAL PAGE CONFIGURATION & CUSTOM CSS INJECTION
#  The visual identity of NEXUS OMNI is established here BEFORE any widget
#  renders. Streamlit requires set_page_config() as the very first call.
# ==============================================================================

st.set_page_config(
    page_title="NEXUS OMNI · Enterprise SEO Telemetry",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Cyberpunk / Glassmorphism CSS Injection ────────────────────────────────────
# DESIGN RATIONALE: A professional SaaS tool never looks like a default app.
# Custom CSS overrides Streamlit's stylesheet to create a proprietary aesthetic
# that signals technical depth and innovation to non-technical stakeholders.
CYBER_CSS = """
<style>
/* ── Google Fonts Import ── */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Inter:wght@300;400;500;600&display=swap');

/* ── Root Variables (Design Tokens) ── */
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
    --glow-cyan:      0 0 8px rgba(0, 212, 255, 0.6), 0 0 20px rgba(0, 212, 255, 0.25);
    --glow-green:     0 0 8px rgba(0, 255, 136, 0.6), 0 0 20px rgba(0, 255, 136, 0.2);
    --glow-red:       0 0 8px rgba(255, 45, 85, 0.6),  0 0 20px rgba(255, 45, 85, 0.2);
}

/* ── Global Reset & Background ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background: var(--bg-abyss) !important;
    color: var(--text-primary) !important;
    font-family: var(--font-ui) !important;
}

/* Animated grid background for depth */
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

/* ── Hide Streamlit Chrome ── */
/* SEO PRESENTATION NOTE: Hiding the native menu makes this look like a
   fully custom SaaS product, not a Streamlit prototype. */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── Sidebar Styling ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #030810 0%, #050e1a 100%) !important;
    border-right: 1px solid var(--border-neon) !important;
    box-shadow: 4px 0 30px rgba(0, 212, 255, 0.08) !important;
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

/* ── Primary Button (Run Telemetry) ── */
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
    position: relative !important;
    overflow: hidden !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, rgba(0,102,255,0.35), rgba(0,212,255,0.35)) !important;
    box-shadow: var(--glow-cyan) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── Metric Cards (Glowing Data Nodes) ── */
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
[data-testid="stMetricDelta"] { font-family: var(--font-mono) !important; font-size: 0.75rem !important; }

/* ── Dataframe Styling ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border-neon) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── Expander ── */
.streamlit-expander {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-neon) !important;
    border-radius: 8px !important;
}
.streamlit-expander summary {
    color: var(--accent-cyan) !important;
    font-family: var(--font-mono) !important;
}

/* ── Info / Warning / Error Boxes ── */
[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.85rem !important;
    border-left-width: 3px !important;
}

/* ── Radio Navigation ── */
[data-testid="stRadio"] > div {
    gap: 0.3rem !important;
    flex-direction: column !important;
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
    color: var(--text-secondary) !important;
}
[data-testid="stRadio"] label:hover {
    border-color: var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
    background: rgba(0,212,255,0.08) !important;
}
[data-testid="stRadio"] [aria-checked="true"] + label,
[data-testid="stRadio"] label:has(input:checked) {
    border-color: var(--accent-cyan) !important;
    color: var(--accent-cyan) !important;
    background: rgba(0,212,255,0.12) !important;
    box-shadow: 0 0 6px rgba(0,212,255,0.3) !important;
}

/* ── Divider ── */
hr { border-color: var(--border-neon) !important; opacity: 0.5 !important; }

/* ── Section Headers ── */
.nexus-section-header {
    font-family: var(--font-title);
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--accent-cyan);
    letter-spacing: 0.25em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border-neon);
    padding-bottom: 0.4rem;
    margin-bottom: 1rem;
}
.nexus-page-title {
    font-family: var(--font-title);
    font-size: 1.6rem;
    font-weight: 900;
    color: var(--accent-cyan);
    text-shadow: var(--glow-cyan);
    letter-spacing: 0.08em;
}
.nexus-page-subtitle {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--text-secondary);
    letter-spacing: 0.08em;
    margin-top: -0.5rem;
    margin-bottom: 1.5rem;
}

/* ── Status Badge ── */
.badge-pass {
    display: inline-block;
    background: rgba(0,255,136,0.12);
    border: 1px solid var(--accent-green);
    color: var(--accent-green);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.15rem 0.6rem;
    border-radius: 4px;
    letter-spacing: 0.1em;
    text-shadow: var(--glow-green);
}
.badge-fail {
    display: inline-block;
    background: rgba(255,45,85,0.12);
    border: 1px solid var(--accent-red);
    color: var(--accent-red);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.15rem 0.6rem;
    border-radius: 4px;
    letter-spacing: 0.1em;
    text-shadow: var(--glow-red);
}
.badge-warn {
    display: inline-block;
    background: rgba(255,184,0,0.12);
    border: 1px solid var(--accent-amber);
    color: var(--accent-amber);
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.15rem 0.6rem;
    border-radius: 4px;
    letter-spacing: 0.1em;
}

/* ── Heading Tree Node ── */
.tree-h1 {
    font-family: var(--font-mono);
    font-size: 0.9rem;
    color: var(--accent-cyan);
    border-left: 3px solid var(--accent-cyan);
    padding: 0.35rem 0.8rem;
    margin: 0.2rem 0;
    background: rgba(0,212,255,0.05);
    border-radius: 0 6px 6px 0;
}
.tree-h2 {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: #7dd3fc;
    border-left: 3px solid #0ea5e9;
    padding: 0.3rem 0.8rem;
    margin: 0.2rem 0 0.2rem 1.5rem;
    background: rgba(14,165,233,0.05);
    border-radius: 0 6px 6px 0;
}
.tree-h3 {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-secondary);
    border-left: 3px solid #334e68;
    padding: 0.25rem 0.8rem;
    margin: 0.15rem 0 0.15rem 3rem;
    background: rgba(51,78,104,0.05);
    border-radius: 0 6px 6px 0;
}

/* ── Schema Checklist ── */
.schema-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 0.8rem;
    border-bottom: 1px solid rgba(0,212,255,0.07);
    font-family: var(--font-mono);
    font-size: 0.8rem;
}
.schema-row:last-child { border-bottom: none; }
.schema-icon-ok  { color: var(--accent-green); font-size: 1.1rem; }
.schema-icon-off { color: var(--accent-red);   font-size: 1.1rem; }

/* ── Sidebar Logo Area ── */
.sidebar-logo {
    font-family: var(--font-title);
    font-size: 1.1rem;
    font-weight: 900;
    color: var(--accent-cyan);
    text-shadow: var(--glow-cyan);
    letter-spacing: 0.1em;
    text-align: center;
    padding: 0.5rem 0;
}
.sidebar-version {
    font-family: var(--font-mono);
    font-size: 0.65rem;
    color: var(--text-dim);
    letter-spacing: 0.12em;
    text-align: center;
    margin-top: -0.3rem;
    margin-bottom: 1rem;
}

/* ── Plotly chart background override ── */
.js-plotly-plot .plotly .bg { fill: transparent !important; }

/* ── Scrollbar styling ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.25); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-cyan); }
</style>
"""
st.markdown(CYBER_CSS, unsafe_allow_html=True)


# ==============================================================================
#  SECTION 2: DATA EXTRACTION ENGINE
#  All web scraping, parsing, and computation logic lives here, separated from
#  UI rendering. This follows a clean data-pipeline architecture: fetch → parse
#  → compute → cache → render.
# ==============================================================================

# Plotly chart theme shared across all figures
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
    to specialised parsers. Results are cached for 5 minutes (ttl=300)
    to avoid hammering the target server on every rerun.

    SEO RATIONALE: Every extracted data point maps to a concrete ranking
    factor in Google's Quality Evaluator Guidelines or Core Web Vitals spec.

    Returns a flat dictionary of all extracted signals. On failure, returns
    {"error": <message>} so the UI can display a graceful warning.
    """
    result = {}

    # ── 1. TTFB Measurement ────────────────────────────────────────────────────
    # SEO RATIONALE: Time to First Byte is a direct Core Web Vitals signal.
    # Google has confirmed TTFB > 600ms negatively impacts crawl budget and
    # user experience scores. We measure it by recording elapsed time from
    # request dispatch to first response byte.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; NEXUSBot/3.0; +https://nexus-omni.io) "
            "AppleWebKit/537.36 KHTML, like Gecko Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    try:
        t_start = time.perf_counter()
        response = requests.get(
            url,
            headers=headers,
            timeout=15,
            allow_redirects=True,
            verify=True,
        )
        ttfb_ms = (time.perf_counter() - t_start) * 1000
        response.raise_for_status()
    except requests.exceptions.SSLError:
        # Retry without SSL verification for self-signed certs (common on uni sites)
        try:
            t_start = time.perf_counter()
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True, verify=False)
            ttfb_ms = (time.perf_counter() - t_start) * 1000
            response.raise_for_status()
        except Exception as e:
            return {"error": f"SSL failure and unverified retry failed: {e}"}
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

    # ── 2. HTML Parsing ────────────────────────────────────────────────────────
    # SEO RATIONALE: lxml is 2–5× faster than the default html.parser and handles
    # malformed university site HTML more gracefully, reducing false negatives
    # in structural analysis.
    try:
        soup = BeautifulSoup(response.text, "lxml")
    except Exception:
        soup = BeautifulSoup(response.text, "html.parser")

    # ── 3. Meta Architecture Extraction ───────────────────────────────────────
    # SEO RATIONALE: The <title> tag is the #1 on-page ranking factor.
    # Meta description drives click-through rate (CTR) in SERPs, which
    # indirectly feeds Google's quality signals.
    title_tag = soup.find("title")
    result["title"] = title_tag.get_text(strip=True) if title_tag else ""
    result["title_len"] = len(result["title"])

    desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    result["description"] = desc_tag.get("content", "").strip() if desc_tag else ""
    result["desc_len"] = len(result["description"])

    # ── 4. Canonical & Robots Signals ─────────────────────────────────────────
    # SEO RATIONALE: A canonical URL prevents duplicate content dilution.
    # The robots meta tag controls crawl indexation. Both are critical for
    # technical SEO health and must be audited on any enterprise site.
    canonical_tag = soup.find("link", rel=lambda r: r and "canonical" in r)
    result["canonical"] = canonical_tag.get("href", "") if canonical_tag else ""

    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    result["robots_meta"] = robots_tag.get("content", "") if robots_tag else ""

    # ── 5. Heading Hierarchy ──────────────────────────────────────────────────
    # SEO RATIONALE: Google uses heading tags as document outline signals.
    # A single H1 per page is mandated by best practice — it tells the crawler
    # the primary topic. H2/H3 represent semantic sub-topics that expand
    # topical authority through structured context.
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
    # SEO RATIONALE: Alt text is the primary signal search engines use to
    # understand image content. Missing alt attributes also violate WCAG 2.1
    # accessibility standards, which Google's Page Experience update factors
    # into ranking. Each missing alt is both an accessibility deficit and a
    # missed keyword injection opportunity.
    all_imgs = soup.find_all("img")
    missing_alt_urls = []
    for img in all_imgs:
        alt = img.get("alt")
        if alt is None or alt.strip() == "":
            src = img.get("src", img.get("data-src", ""))
            if src:
                missing_alt_urls.append(urljoin(url, src))
            else:
                missing_alt_urls.append("[inline / no src]")

    result["total_images"] = len(all_imgs)
    result["missing_alt_count"] = len(missing_alt_urls)
    result["missing_alt_urls"] = missing_alt_urls

    # ── 7. Link Architecture ──────────────────────────────────────────────────
    # SEO RATIONALE: Internal link density and anchor text distribution
    # directly influence PageRank flow and crawl depth. External links signal
    # topical authority when pointing to credible sources.
    parsed_base = urlparse(url)
    internal_links, external_links = 0, 0
    for a in soup.find_all("a", href=True):
        href = a["href"]
        parsed_href = urlparse(href)
        if parsed_href.netloc == "" or parsed_href.netloc == parsed_base.netloc:
            internal_links += 1
        elif parsed_href.scheme in ("http", "https"):
            external_links += 1

    result["internal_links"] = internal_links
    result["external_links"] = external_links

    # ── 8. Schema & OpenGraph Detection ───────────────────────────────────────
    # SEO RATIONALE: Schema.org JSON-LD markup enables Rich Results (star ratings,
    # FAQs, breadcrumbs) in Google SERPs, which boosts CTR by up to 30%.
    # OpenGraph tags control how pages render when shared on LinkedIn, Twitter,
    # Facebook — critical for the off-page link acquisition funnel.
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

    # ── 9. HTML5 Semantic Landmark Detection ──────────────────────────────────
    # SEO RATIONALE: HTML5 landmark elements (<header>, <main>, <nav>, <footer>,
    # <article>, <section>) improve both accessibility and crawler comprehension.
    # Google's Googlebot uses these to understand page regions and prioritise
    # which content to crawl — pages with clear landmarks rank better.
    semantic_tags = ["header", "main", "nav", "footer", "article", "section", "aside"]
    semantic_present = {tag: bool(soup.find(tag)) for tag in semantic_tags}
    result["semantic_tags"] = semantic_present
    result["semantic_score"] = sum(semantic_present.values())

    # ── 10. Body Text Extraction (NLP Pipeline Input) ─────────────────────────
    # SEO RATIONALE: The full visible body text is the primary topical signal
    # for semantic search algorithms. We strip navigation and boilerplate
    # by removing script/style nodes, leaving only content-bearing text.
    for noise in soup(["script", "style", "noscript", "template", "iframe"]):
        noise.decompose()
    raw_text = soup.get_text(separator=" ", strip=True)

    # Normalise whitespace
    raw_text = re.sub(r"\s+", " ", raw_text).strip()
    result["raw_text"] = raw_text
    result["word_count"] = len(raw_text.split())

    # ── 11. Readability Scoring ───────────────────────────────────────────────
    # SEO RATIONALE: Flesch-Kincaid Reading Ease (FKRE) measures content
    # accessibility. Scores 60–70 target general audiences (Grade 8–9 level).
    # Content that is too complex increases bounce rate, a negative UX signal
    # that indirectly depresses rankings through Google's behaviour data.
    if result["word_count"] > 30:
        result["fk_reading_ease"] = round(textstat.flesch_reading_ease(raw_text), 1)
        result["fk_grade_level"] = round(textstat.flesch_kincaid_grade(raw_text), 1)
        result["gunning_fog"] = round(textstat.gunning_fog(raw_text), 1)
    else:
        result["fk_reading_ease"] = None
        result["fk_grade_level"] = None
        result["gunning_fog"] = None

    # ── 12. Sentiment Analysis ────────────────────────────────────────────────
    # SEO RATIONALE: While Google does not directly use sentiment as a ranking
    # signal, positive emotional tone correlates with lower bounce rates and
    # higher dwell time — both indirect behavioural ranking signals.
    # University sites should project institutional confidence and authority.
    try:
        blob = TextBlob(raw_text[:5000])   # Limit to first 5 000 chars for perf
        result["sentiment_polarity"] = round(blob.sentiment.polarity, 4)
        result["sentiment_subjectivity"] = round(blob.sentiment.subjectivity, 4)
    except Exception:
        result["sentiment_polarity"] = 0.0
        result["sentiment_subjectivity"] = 0.0

    # ── 13. Keyword Extraction (N-gram Frequency) ──────────────────────────────
    # SEO RATIONALE: Keyword density and co-occurrence of topically related
    # terms (TF-IDF proxy) signal semantic relevance to Google's BERT/MUM models.
    # Bigrams and trigrams capture phrase-level intent better than unigrams.
    keywords_df = _extract_keywords(raw_text)
    result["keywords_df"] = keywords_df

    # ── 14. Health Score Aggregation ──────────────────────────────────────────
    # Composite 0–100 score derived from weighted sub-scores across four pillars:
    # Meta Health (25), DOM Structure (25), Accessibility (25), Content Quality (25)
    result["scores"] = _compute_health_scores(result)
    result["global_score"] = round(sum(result["scores"].values()) / len(result["scores"]) * 100 / 25, 1)
    result["global_score"] = min(100, result["global_score"])

    return result


def _extract_keywords(text: str, top_n: int = 15) -> pd.DataFrame:
    """
    Tokenize body text, remove stopwords, and compute bigram/trigram
    frequency distribution.

    SEO RATIONALE: Google's language models assess topical authority by
    detecting semantically dense keyword clusters. Surfacing the dominant
    n-grams reveals whether the page's linguistic fingerprint aligns with
    its intended target keywords.
    """
    try:
        stop_words = set(stopwords.words("english"))
    except LookupError:
        # Fallback minimal stopword list if NLTK corpus unavailable
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at",
                      "to", "for", "of", "with", "is", "are", "was", "were",
                      "be", "been", "being", "have", "has", "had", "do", "does",
                      "did", "will", "would", "could", "should", "may", "might",
                      "it", "its", "this", "that", "these", "those", "we", "our",
                      "us", "you", "your", "he", "she", "they", "their", "them",
                      "what", "which", "who", "not", "also", "as", "from"}

    # Tokenise: lowercase, strip non-alphanumeric, filter stopwords & short tokens
    tokens = [
        w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", text)
        if w.lower() not in stop_words
    ]

    # Generate bigrams and trigrams
    bigram_freq = Counter(
        " ".join(gram) for gram in ngrams(tokens, 2)
    )
    trigram_freq = Counter(
        " ".join(gram) for gram in ngrams(tokens, 3)
    )

    # Merge and select top N
    combined = bigram_freq + trigram_freq
    top_keywords = combined.most_common(top_n)

    if not top_keywords:
        return pd.DataFrame(columns=["Keyword", "Frequency"])

    df = pd.DataFrame(top_keywords, columns=["Keyword", "Frequency"])
    df["Keyword"] = df["Keyword"].str.title()
    return df


def _compute_health_scores(r: dict) -> dict:
    """
    Compute four pillar scores (each 0–25) for the radar chart and global KPI.

    Scoring methodology:
    ─────────────────────────────────────────────────────────────────────────
    META HEALTH      — title/desc present and within optimal length ranges
    DOM STRUCTURE    — H1 singular, H2/H3 hierarchy present, semantic HTML5
    ACCESSIBILITY    — alt text coverage, internal link density
    CONTENT QUALITY  — word count, readability, schema markup presence
    ─────────────────────────────────────────────────────────────────────────
    """
    scores = {"Meta Health": 0, "DOM Structure": 0, "Accessibility": 0, "Content Quality": 0}

    # ─── Meta Health (25 pts) ────────────────────────────────────────────────
    meta_pts = 0
    if r.get("title"):
        meta_pts += 8
        if 50 <= r["title_len"] <= 60:
            meta_pts += 5   # Optimal title length
        elif r["title_len"] < 50:
            meta_pts += 2
    if r.get("description"):
        meta_pts += 7
        if 150 <= r["desc_len"] <= 160:
            meta_pts += 5   # Optimal meta description length
        elif r["desc_len"] < 150:
            meta_pts += 2
    scores["Meta Health"] = min(25, meta_pts)

    # ─── DOM Structure (25 pts) ──────────────────────────────────────────────
    dom_pts = 0
    if r.get("h1_count") == 1:
        dom_pts += 10   # Single H1 is the canonical best practice
    elif r.get("h1_count", 0) > 1:
        dom_pts += 2    # Multiple H1s — partial credit (exists but wrong)
    if r.get("h2_count", 0) >= 2:
        dom_pts += 6
    if r.get("h3_count", 0) >= 1:
        dom_pts += 3
    # Semantic HTML5 score (max 6 pts from 7 possible landmark tags)
    dom_pts += min(6, r.get("semantic_score", 0))
    scores["DOM Structure"] = min(25, dom_pts)

    # ─── Accessibility (25 pts) ──────────────────────────────────────────────
    acc_pts = 0
    total_imgs = r.get("total_images", 0)
    missing_alt = r.get("missing_alt_count", 0)
    if total_imgs == 0:
        acc_pts += 15   # No images = no accessibility risk (neutral)
    else:
        alt_ratio = 1 - (missing_alt / total_imgs)
        acc_pts += round(alt_ratio * 15)
    # Internal linking score
    if r.get("internal_links", 0) >= 10:
        acc_pts += 10
    elif r.get("internal_links", 0) >= 3:
        acc_pts += 5
    scores["Accessibility"] = min(25, acc_pts)

    # ─── Content Quality (25 pts) ─────────────────────────────────────────────
    cq_pts = 0
    wc = r.get("word_count", 0)
    if wc >= 800:
        cq_pts += 8   # Long-form content correlates with higher rankings
    elif wc >= 300:
        cq_pts += 4
    elif wc >= 100:
        cq_pts += 2
    fk = r.get("fk_reading_ease")
    if fk is not None:
        if 50 <= fk <= 70:
            cq_pts += 7   # Ideal readability range for general audiences
        elif fk > 70:
            cq_pts += 4
        else:
            cq_pts += 2
    if r.get("has_json_ld"):
        cq_pts += 5   # Schema markup for rich results
    if r.get("has_og_title") and r.get("has_og_description"):
        cq_pts += 5   # Social graph metadata
    scores["Content Quality"] = min(25, cq_pts)

    return scores


# ==============================================================================
#  SECTION 3: SIDEBAR — URL INPUT, EXECUTION CONTROL & NAVIGATION
# ==============================================================================

with st.sidebar:
    st.markdown('<div class="sidebar-logo">⬡ NEXUS OMNI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-version">ENTERPRISE SEO TELEMETRY v3.0</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(
        '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;'
        'color:#3d5a73;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.4rem;">'
        "▸ Target Acquisition</div>",
        unsafe_allow_html=True,
    )

    # URL Input — default pre-loaded with the SABS university URL for demo readiness
    target_url = st.text_input(
        "Target URL",
        value="https://www.sabs.edu.pk",
        placeholder="https://example.com",
        label_visibility="collapsed",
    )

    run_btn = st.button("⚡  INITIATE TELEMETRY SCAN", use_container_width=True)

    st.markdown("---")
    st.markdown(
        '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;'
        'color:#3d5a73;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.5rem;">'
        "▸ Navigation Matrix</div>",
        unsafe_allow_html=True,
    )

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
    # Sidebar status indicator
    if "seo_data" in st.session_state and "error" not in st.session_state.seo_data:
        d = st.session_state.seo_data
        st.markdown(
            f"""<div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;
            color:#3d5a73;line-height:1.8;">
            <span style="color:#00d4ff;">■</span> STATUS: ONLINE<br>
            <span style="color:#00d4ff;">■</span> TTFB: {d.get('ttfb_ms','—')} ms<br>
            <span style="color:#00d4ff;">■</span> SCORE: {d.get('global_score','—')}/100<br>
            <span style="color:#00d4ff;">■</span> WORDS: {d.get('word_count','—'):,}
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.72rem;'
            'color:#3d5a73;">■ AWAITING TARGET URL</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.6rem;'
        'color:#1e3a4a;text-align:center;line-height:1.6;">'
        "NEXUS OMNI · SABS ASSESSMENT<br>"
        "© 2026 · PROPRIETARY TELEMETRY PLATFORM</div>",
        unsafe_allow_html=True,
    )


# ==============================================================================
#  SECTION 4: DATA PIPELINE TRIGGER
#  When the user clicks "Run Telemetry", fetch+parse is invoked and the result
#  is stored in session_state so all three pages can read it without re-fetching.
# ==============================================================================

if run_btn:
    # Basic URL sanity check before sending any network request
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
#  SECTION 5: PAGE RENDERING
#  Each page reads exclusively from st.session_state["seo_data"]. All UI logic
#  is encapsulated in dedicated render_* functions for clarity and testability.
# ==============================================================================

def _no_data_warning():
    """Render a stylised prompt when no scan has been executed yet."""
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
    height:60vh;gap:1rem;">
        <div style="font-family:'Orbitron',monospace;font-size:3rem;color:rgba(0,212,255,0.15);
        letter-spacing:0.2em;">⬡</div>
        <div style="font-family:'Orbitron',monospace;font-size:1rem;color:rgba(0,212,255,0.5);
        letter-spacing:0.2em;text-transform:uppercase;">AWAITING TARGET ACQUISITION</div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;color:#3d5a73;
        text-align:center;max-width:400px;line-height:1.7;">
        Enter a URL in the sidebar panel and click<br>
        <span style="color:#00d4ff;">⚡ INITIATE TELEMETRY SCAN</span><br>
        to begin the diagnostic sequence.
        </div>
    </div>
    """, unsafe_allow_html=True)


def _error_panel(msg: str):
    """Gracefully render scraper errors without exposing raw tracebacks."""
    st.markdown(f"""
    <div style="border:1px solid #ff2d55;border-radius:10px;padding:1.5rem;
    background:rgba(255,45,85,0.06);margin-top:1rem;">
        <div style="font-family:'Orbitron',monospace;font-size:0.85rem;color:#ff2d55;
        letter-spacing:0.15em;margin-bottom:0.6rem;">⚠  TELEMETRY FAILURE — NETWORK EXCEPTION</div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.78rem;
        color:#7a9bb5;line-height:1.8;">{msg}</div>
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;
        color:#3d5a73;margin-top:0.8rem;">
        ■ Verify the URL is publicly accessible<br>
        ■ Confirm the server is not geo-restricted<br>
        ■ Try an alternative URL (with or without www.)
        </div>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 1: EXECUTIVE HUD
# ──────────────────────────────────────────────────────────────────────────────

def render_executive_hud(d: dict):
    """
    Render the high-level KPI dashboard. This is the 'boardroom view' —
    designed to communicate health at a glance before drilling into details.
    """
    st.markdown('<div class="nexus-page-title">EXECUTIVE HUD</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="nexus-page-subtitle">REAL-TIME TELEMETRY · {st.session_state.get("scanned_url","")}</div>',
        unsafe_allow_html=True,
    )

    # ── Row 1: Core KPI Metrics ───────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)

    # Global Health Score
    gs = d.get("global_score", 0)
    gs_delta = "EXCELLENT" if gs >= 80 else ("MODERATE" if gs >= 55 else "CRITICAL")
    c1.metric("🎯  GLOBAL HEALTH SCORE", f"{gs}/100", gs_delta)

    # TTFB Classification
    ttfb = d.get("ttfb_ms", 0)
    ttfb_label = "FAST" if ttfb < 200 else ("MODERATE" if ttfb < 600 else "SLOW")
    c2.metric("⚡  SERVER TTFB", f"{ttfb} ms", ttfb_label)

    # Word Count
    wc = d.get("word_count", 0)
    c3.metric("📝  TOTAL WORDS", f"{wc:,}", "LONG-FORM" if wc >= 800 else ("MED" if wc >= 300 else "THIN"))

    # Image Accessibility
    total_imgs = d.get("total_images", 0)
    miss_alt = d.get("missing_alt_count", 0)
    c4.metric("🖼  IMAGES MISSING ALT", str(miss_alt), f"of {total_imgs} total")

    # HTTP Status
    status = d.get("status_code", "—")
    c5.metric("🌐  HTTP STATUS", str(status), "OK" if status == 200 else "CHECK")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Radar Chart + Semantic Tags ────────────────────────────────────
    col_radar, col_tags = st.columns([3, 2], gap="large")

    with col_radar:
        st.markdown('<div class="nexus-section-header">◈ SEO HEALTH RADAR — 4-PILLAR ANALYSIS</div>', unsafe_allow_html=True)

        scores = d.get("scores", {})
        categories = list(scores.keys())
        values = list(scores.values())

        # Close the radar loop
        categories_loop = categories + [categories[0]]
        values_loop = values + [values[0]]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=values_loop,
            theta=categories_loop,
            fill="toself",
            fillcolor="rgba(0, 212, 255, 0.12)",
            line=dict(color="#00d4ff", width=2.5),
            name="SEO Score",
            hovertemplate="<b>%{theta}</b><br>Score: %{r}/25<extra></extra>",
        ))
        # Target reference polygon (perfect score = 25 per axis)
        fig_radar.add_trace(go.Scatterpolar(
            r=[25] * len(categories_loop),
            theta=categories_loop,
            fill="toself",
            fillcolor="rgba(0,102,255,0.04)",
            line=dict(color="rgba(0,102,255,0.25)", width=1, dash="dot"),
            name="Target (25)",
            hoverinfo="skip",
        ))

        fig_radar.update_layout(
            **_PLOTLY_LAYOUT,
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                angularaxis=dict(
                    linecolor="rgba(0,212,255,0.2)",
                    gridcolor="rgba(0,212,255,0.08)",
                    tickfont=dict(family="Share Tech Mono", color="#7a9bb5", size=11),
                ),
                radialaxis=dict(
                    visible=True,
                    range=[0, 25],
                    gridcolor="rgba(0,212,255,0.08)",
                    linecolor="rgba(0,212,255,0.1)",
                    tickfont=dict(family="Share Tech Mono", color="#3d5a73", size=9),
                    tickvals=[5, 10, 15, 20, 25],
                ),
            ),
            legend=dict(
                x=0.85, y=1.1,
                font=dict(family="Share Tech Mono", color="#7a9bb5", size=9),
                bgcolor="rgba(0,0,0,0)",
            ),
            height=380,
        )
        st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})

    with col_tags:
        st.markdown('<div class="nexus-section-header">◈ HTML5 SEMANTIC LANDMARK AUDIT</div>', unsafe_allow_html=True)

        # SEO RATIONALE: HTML5 semantic landmarks help Googlebot identify
        # page regions: <header> = site identity, <main> = primary content,
        # <nav> = navigation signals, <article> = standalone indexable content.
        semantic = d.get("semantic_tags", {})
        tag_descriptions = {
            "header": "Site Identity Region",
            "main": "Primary Content Zone",
            "nav": "Navigation Structure",
            "footer": "Footer Authority Block",
            "article": "Standalone Content Unit",
            "section": "Thematic Grouping",
            "aside": "Supplemental Context",
        }

        html_rows = ""
        for tag, present in semantic.items():
            icon = "✦" if present else "✗"
            icon_class = "schema-icon-ok" if present else "schema-icon-off"
            status_badge = '<span class="badge-pass">DETECTED</span>' if present else '<span class="badge-fail">MISSING</span>'
            html_rows += f"""
            <div class="schema-row">
                <span class="{icon_class}">{icon}</span>
                <code style="color:#00d4ff;font-size:0.78rem;">&lt;{tag}&gt;</code>
                <span style="color:#7a9bb5;flex:1;">{tag_descriptions.get(tag,'')}</span>
                {status_badge}
            </div>"""

        semantic_score = d.get("semantic_score", 0)
        html_rows += f"""
        <div style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',monospace;
        font-size:0.75rem;color:#3d5a73;border-top:1px solid rgba(0,212,255,0.1);
        margin-top:0.3rem;">
        SEMANTIC COVERAGE: {semantic_score}/7 landmarks detected
        </div>"""

        st.markdown(
            f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);'
            f'border-radius:8px;overflow:hidden;">{html_rows}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 3: Quick Stats Band ───────────────────────────────────────────────
    st.markdown('<div class="nexus-section-header">◈ RAPID DIAGNOSTIC TELEMETRY</div>', unsafe_allow_html=True)

    q1, q2, q3, q4, q5, q6 = st.columns(6)

    h1_count = d.get("h1_count", 0)
    h1_status = "✦ PASS" if h1_count == 1 else ("✗ FAIL" if h1_count == 0 else "⚠ WARN")

    title_len = d.get("title_len", 0)
    title_status = "✦ PASS" if 50 <= title_len <= 60 else ("✗ FAIL" if title_len == 0 else "⚠ WARN")

    desc_len = d.get("desc_len", 0)
    desc_status = "✦ PASS" if 150 <= desc_len <= 160 else ("✗ FAIL" if desc_len == 0 else "⚠ WARN")

    schema_status = "✦ PASS" if d.get("has_json_ld") else "✗ FAIL"
    og_status = "✦ PASS" if d.get("has_og_title") else "✗ FAIL"
    canonical_status = "✦ PASS" if d.get("canonical") else "⚠ WARN"

    q1.metric("H1 TAGS", str(h1_count), h1_status)
    q2.metric("TITLE LENGTH", f"{title_len} ch", title_status)
    q3.metric("META DESC LEN", f"{desc_len} ch", desc_status)
    q4.metric("JSON-LD SCHEMA", "DETECTED" if d.get("has_json_ld") else "MISSING", schema_status)
    q5.metric("OPEN GRAPH", "ACTIVE" if d.get("has_og_title") else "ABSENT", og_status)
    q6.metric("CANONICAL TAG", "SET" if d.get("canonical") else "ABSENT", canonical_status)


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 2: STRUCTURAL DOM AUDIT
# ──────────────────────────────────────────────────────────────────────────────

def render_dom_audit(d: dict):
    """
    Deep-dive technical audit of DOM architecture, meta tags, heading hierarchy,
    schema markup, and image accessibility.
    """
    st.markdown('<div class="nexus-page-title">DOM STRUCTURAL AUDIT</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="nexus-page-subtitle">TECHNICAL BACKEND · METADATA · SCHEMA · ACCESSIBILITY</div>',
        unsafe_allow_html=True,
    )

    # ── A: Meta Architecture Matrix ───────────────────────────────────────────
    st.markdown('<div class="nexus-section-header">◈ META ARCHITECTURE MATRIX</div>', unsafe_allow_html=True)

    # SEO RATIONALE: Title tags must be 50–60 chars to avoid SERP truncation.
    # Meta descriptions at 150–160 chars maximise ad-like preview real-estate.
    # Both directly impact Click-Through Rate (CTR) from search results.
    ma1, ma2 = st.columns(2, gap="large")

    with ma1:
        title = d.get("title", "")
        title_len = d.get("title_len", 0)
        if title_len == 0:
            title_color, title_verdict = "#ff2d55", "CRITICAL — Title tag absent"
        elif title_len < 50:
            title_color, title_verdict = "#ffb800", f"TOO SHORT ({title_len}/50–60 chars)"
        elif title_len > 60:
            title_color, title_verdict = "#ffb800", f"TOO LONG ({title_len}/50–60 chars) — SERP truncation risk"
        else:
            title_color, title_verdict = "#00ff88", f"OPTIMAL ({title_len}/50–60 chars)"

        # Visual character-fill bar
        fill_pct = min(100, (title_len / 60) * 100)
        bar_color = title_color

        st.markdown(f"""
        <div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);
        border-radius:8px;padding:1.2rem;">
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
            color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;
            margin-bottom:0.6rem;">▸ &lt;TITLE&gt; TAG</div>

            <div style="font-family:'Inter',sans-serif;font-size:0.88rem;
            color:#e8f4f8;margin-bottom:0.8rem;min-height:2.5rem;
            word-break:break-all;">"{title if title else 'NOT FOUND'}"</div>

            <div style="background:rgba(0,212,255,0.06);border-radius:4px;
            height:6px;overflow:hidden;margin-bottom:0.5rem;">
                <div style="height:100%;width:{fill_pct:.0f}%;
                background:{bar_color};border-radius:4px;
                transition:width 0.8s ease;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;
            font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:#3d5a73;">
                <span>0</span><span style="color:{title_color};">{title_verdict}</span><span>60</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with ma2:
        desc = d.get("description", "")
        desc_len = d.get("desc_len", 0)
        if desc_len == 0:
            desc_color, desc_verdict = "#ff2d55", "CRITICAL — Meta description absent"
        elif desc_len < 150:
            desc_color, desc_verdict = "#ffb800", f"TOO SHORT ({desc_len}/150–160 chars)"
        elif desc_len > 160:
            desc_color, desc_verdict = "#ffb800", f"TOO LONG ({desc_len}/150–160 chars)"
        else:
            desc_color, desc_verdict = "#00ff88", f"OPTIMAL ({desc_len}/150–160 chars)"

        fill_pct_d = min(100, (desc_len / 160) * 100)

        st.markdown(f"""
        <div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);
        border-radius:8px;padding:1.2rem;">
            <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
            color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;
            margin-bottom:0.6rem;">▸ META DESCRIPTION</div>

            <div style="font-family:'Inter',sans-serif;font-size:0.88rem;
            color:#e8f4f8;margin-bottom:0.8rem;min-height:2.5rem;
            word-break:break-all;">"{desc if desc else 'NOT FOUND'}"</div>

            <div style="background:rgba(0,212,255,0.06);border-radius:4px;
            height:6px;overflow:hidden;margin-bottom:0.5rem;">
                <div style="height:100%;width:{fill_pct_d:.0f}%;
                background:{desc_color};border-radius:4px;
                transition:width 0.8s ease;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;
            font-family:'Share Tech Mono',monospace;font-size:0.7rem;color:#3d5a73;">
                <span>0</span><span style="color:{desc_color};">{desc_verdict}</span><span>160</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Canonical + Robots row
    st.markdown("<br>", unsafe_allow_html=True)
    cr1, cr2 = st.columns(2, gap="large")
    with cr1:
        canonical = d.get("canonical", "")
        st.markdown(f"""
        <div style="background:rgba(10,22,40,0.6);border:1px solid rgba(0,212,255,0.12);
        border-radius:8px;padding:1rem 1.2rem;">
            <span style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
            color:#3d5a73;letter-spacing:0.1em;">CANONICAL URL</span><br>
            <span style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;
            color:{'#00d4ff' if canonical else '#ff2d55'};">
            {"✦ " + canonical if canonical else "✗  &lt;link rel='canonical'&gt; NOT FOUND"}</span>
        </div>
        """, unsafe_allow_html=True)
    with cr2:
        robots = d.get("robots_meta", "")
        st.markdown(f"""
        <div style="background:rgba(10,22,40,0.6);border:1px solid rgba(0,212,255,0.12);
        border-radius:8px;padding:1rem 1.2rem;">
            <span style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
            color:#3d5a73;letter-spacing:0.1em;">ROBOTS META DIRECTIVE</span><br>
            <span style="font-family:'Share Tech Mono',monospace;font-size:0.8rem;
            color:{'#ffb800' if 'noindex' in robots.lower() else '#00ff88' if robots else '#3d5a73'};">
            {"⚠ NOINDEX DETECTED — Page excluded from SERPs" if 'noindex' in robots.lower()
              else ("✦ " + robots) if robots else "— No robots meta found (defaults to index,follow)"}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── B: Heading Hierarchy Tree ──────────────────────────────────────────────
    st.markdown('<div class="nexus-section-header">◈ HEADING HIERARCHY TREE — DOCUMENT OUTLINE</div>', unsafe_allow_html=True)

    headings = d.get("headings", [])
    h1_count = d.get("h1_count", 0)

    # Alert logic for H1 violations
    # SEO RATIONALE: The H1 is the page's topical declaration to Googlebot.
    # Zero H1s = the crawler cannot determine the primary topic.
    # Multiple H1s = topic dilution, confuses the crawler's content model.
    if h1_count == 0:
        st.markdown("""
        <div style="border:1px solid #ff2d55;border-radius:8px;padding:0.8rem 1rem;
        background:rgba(255,45,85,0.06);font-family:'Share Tech Mono',monospace;
        font-size:0.8rem;color:#ff2d55;margin-bottom:0.8rem;">
        ⚠  CRITICAL ALERT — H1 TAG ABSENT: No primary heading found. Google cannot
        determine the topical focus of this page. This is a high-priority SEO defect.
        </div>""", unsafe_allow_html=True)
    elif h1_count > 1:
        st.markdown(f"""
        <div style="border:1px solid #ffb800;border-radius:8px;padding:0.8rem 1rem;
        background:rgba(255,184,0,0.06);font-family:'Share Tech Mono',monospace;
        font-size:0.8rem;color:#ffb800;margin-bottom:0.8rem;">
        ⚠  WARNING — MULTIPLE H1 TAGS ({h1_count}): Topic authority is diluted across
        multiple primary headings. Google best practice mandates exactly ONE H1 per page.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="border:1px solid #00ff88;border-radius:8px;padding:0.8rem 1rem;
        background:rgba(0,255,136,0.04);font-family:'Share Tech Mono',monospace;
        font-size:0.8rem;color:#00ff88;margin-bottom:0.8rem;">
        ✦  PASS — SINGULAR H1 DETECTED: Heading hierarchy is correctly structured.
        </div>""", unsafe_allow_html=True)

    if headings:
        tree_html = ""
        for h in headings[:40]:   # Cap at 40 nodes to prevent UI overflow
            level = h["level"]
            text = h["text"][:90] + ("…" if len(h["text"]) > 90 else "")
            css_class = f"tree-{level.lower()}"
            prefix = {"H1": "H1 ▸", "H2": "H2 ▶", "H3": "H3 ›"}[level]
            tree_html += f'<div class="{css_class}"><span style="opacity:0.5;">{prefix}</span> {text}</div>'

        if len(headings) > 40:
            tree_html += f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;color:#3d5a73;padding:0.5rem 0.8rem;">… and {len(headings)-40} more heading nodes</div>'

        st.markdown(
            f'<div style="background:rgba(6,13,20,0.8);border:1px solid rgba(0,212,255,0.15);'
            f'border-radius:8px;padding:0.8rem;max-height:350px;overflow-y:auto;">{tree_html}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-family:\'Share Tech Mono\',monospace;color:#3d5a73;'
            'font-size:0.8rem;padding:1rem;">No heading tags (H1–H3) detected in DOM.</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.72rem;color:#3d5a73;'
        f'padding:0.4rem 0;">HEADING TOTALS → '
        f'<span style="color:#00d4ff;">H1: {h1_count}</span> · '
        f'<span style="color:#7dd3fc;">H2: {d.get("h2_count",0)}</span> · '
        f'<span style="color:#7a9bb5;">H3: {d.get("h3_count",0)}</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── C: Schema & OpenGraph Checklist ───────────────────────────────────────
    st.markdown('<div class="nexus-section-header">◈ SCHEMA & SOCIAL GRAPH INTELLIGENCE</div>', unsafe_allow_html=True)

    sc1, sc2 = st.columns(2, gap="large")

    with sc1:
        og = d.get("og_tags", {})
        checks_og = [
            ("og:title",       d.get("has_og_title",       False), "Social share title"),
            ("og:description", d.get("has_og_description", False), "Social preview description"),
            ("og:image",       d.get("has_og_image",       False), "Social preview thumbnail"),
            ("og:url",         "og:url" in og,                     "Canonical social URL"),
            ("og:type",        "og:type" in og,                    "Content type declaration"),
            ("og:site_name",   "og:site_name" in og,               "Brand identity tag"),
        ]
        rows_og = ""
        for tag, present, desc_txt in checks_og:
            icon = "✦" if present else "✗"
            icon_color = "#00ff88" if present else "#ff2d55"
            badge = f'<span class="badge-pass">ACTIVE</span>' if present else f'<span class="badge-fail">MISSING</span>'
            rows_og += f"""<div class="schema-row">
                <span style="color:{icon_color};font-size:1rem;">{icon}</span>
                <code style="color:#00d4ff;font-size:0.75rem;">{tag}</code>
                <span style="color:#7a9bb5;flex:1;font-size:0.76rem;">{desc_txt}</span>
                {badge}
            </div>"""

        st.markdown(
            f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;'
            f'color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">'
            f'▸ OpenGraph Protocol (og:) Tags</div>'
            f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);'
            f'border-radius:8px;overflow:hidden;">{rows_og}</div>',
            unsafe_allow_html=True,
        )

    with sc2:
        json_ld_types = d.get("json_ld_types", [])
        has_jld = d.get("has_json_ld", False)

        schema_checks = [
            ("JSON-LD Present",       has_jld,                "Structured data block detected"),
            ("Schema.org @type",      bool(json_ld_types),    "Entity type declared"),
            ("Twitter:card",          False,                  "Twitter card meta"),
        ]
        # Check for twitter card
        # (Note: twitter meta tags not yet separately extracted; shown as informational)

        rows_jld = ""
        for tag, present, desc_txt in schema_checks:
            icon = "✦" if present else "✗"
            icon_color = "#00ff88" if present else "#ff2d55"
            badge = f'<span class="badge-pass">ACTIVE</span>' if present else f'<span class="badge-fail">MISSING</span>'
            rows_jld += f"""<div class="schema-row">
                <span style="color:{icon_color};font-size:1rem;">{icon}</span>
                <code style="color:#00d4ff;font-size:0.75rem;">{tag}</code>
                <span style="color:#7a9bb5;flex:1;font-size:0.76rem;">{desc_txt}</span>
                {badge}
            </div>"""

        if json_ld_types:
            types_str = ", ".join(json_ld_types[:5])
            rows_jld += f"""<div style="padding:0.6rem 0.8rem;font-family:'Share Tech Mono',
            monospace;font-size:0.72rem;color:#00d4ff;border-top:1px solid rgba(0,212,255,0.1);">
            DETECTED SCHEMA TYPES: {types_str}</div>"""

        st.markdown(
            f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7rem;'
            f'color:#3d5a73;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">'
            f'▸ JSON-LD Structured Data</div>'
            f'<div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);'
            f'border-radius:8px;overflow:hidden;">{rows_jld}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── D: Accessibility Engine ────────────────────────────────────────────────
    st.markdown('<div class="nexus-section-header">◈ ACCESSIBILITY ENGINE — IMAGE ALT-TEXT AUDIT</div>', unsafe_allow_html=True)

    total_imgs = d.get("total_images", 0)
    missing_alt = d.get("missing_alt_count", 0)
    missing_urls = d.get("missing_alt_urls", [])

    acc1, acc2, acc3 = st.columns(3)
    acc1.metric("TOTAL IMAGES", str(total_imgs))
    acc2.metric("MISSING ALT TEXT", str(missing_alt), "⚠ WCAG VIOLATION" if missing_alt > 0 else "✦ CLEAN")
    acc3.metric("ALT COVERAGE", f"{round((1 - missing_alt/max(total_imgs,1))*100)}%",
                "EXCELLENT" if missing_alt == 0 else "NEEDS WORK")

    if missing_urls:
        with st.expander(
            f"⚠  {missing_alt} IMAGE(S) MISSING ALT ATTRIBUTE — Click to Expand Violation Report",
            expanded=False,
        ):
            st.markdown(
                '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.72rem;'
                'color:#ffb800;margin-bottom:0.8rem;">'
                'SEO IMPACT: Each missing alt attribute is a missed keyword injection point AND '
                'a WCAG 2.1 Level A violation. Google uses alt text to index images in Google Image Search, '
                'providing an additional organic traffic channel.</div>',
                unsafe_allow_html=True,
            )
            df_missing = pd.DataFrame(
                {"#": range(1, len(missing_urls) + 1), "Image URL (Missing Alt Attribute)": missing_urls}
            )
            st.dataframe(
                df_missing,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "#": st.column_config.NumberColumn(width="small"),
                    "Image URL (Missing Alt Attribute)": st.column_config.TextColumn(width="large"),
                },
            )
    elif total_imgs > 0:
        st.success("✦  ALL IMAGES HAVE ALT ATTRIBUTES — Perfect WCAG accessibility compliance detected.")
    else:
        st.info("ℹ  No <img> elements found in the parsed DOM.")

    # Link Architecture Summary
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="nexus-section-header">◈ LINK ARCHITECTURE ANALYSIS</div>', unsafe_allow_html=True)
    la1, la2, la3 = st.columns(3)
    int_links = d.get("internal_links", 0)
    ext_links = d.get("external_links", 0)
    total_links = int_links + ext_links
    la1.metric("INTERNAL LINKS", str(int_links), "Good PageRank flow" if int_links >= 10 else "Sparse")
    la2.metric("EXTERNAL LINKS", str(ext_links), "Authority signals" if ext_links > 0 else "No outbound")
    la3.metric("PAGE SIZE", f"{d.get('content_size_kb',0)} KB", "Optimised" if d.get("content_size_kb",0) < 500 else "Large")


# ──────────────────────────────────────────────────────────────────────────────
#  PAGE 3: SEMANTIC NLP ENGINE
# ──────────────────────────────────────────────────────────────────────────────

def render_nlp_engine(d: dict):
    """
    NLP-driven content analysis: keyword extraction, readability scoring,
    and sentiment polarity analysis.
    """
    st.markdown('<div class="nexus-page-title">SEMANTIC NLP ENGINE</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="nexus-page-subtitle">LEXICAL ANALYSIS · READABILITY INDEXING · SENTIMENT PROFILING</div>',
        unsafe_allow_html=True,
    )

    # ── A: Keyword Extraction + Frequency Chart ────────────────────────────────
    st.markdown('<div class="nexus-section-header">◈ LEXICAL DENSITY — TOP 15 SEMANTIC KEYWORDS (BI/TRI-GRAM)</div>', unsafe_allow_html=True)

    # SEO RATIONALE: Bigrams and trigrams reveal the page's dominant phrase-level
    # topics. Google's NLP models (BERT, MUM) understand natural language phrases,
    # not just individual keywords. High-frequency phrases that align with search
    # intent signals confirm the page's topical relevance.
    kw_df = d.get("keywords_df", pd.DataFrame())

    if kw_df is not None and not kw_df.empty:
        fig_kw = px.bar(
            kw_df.sort_values("Frequency"),
            x="Frequency",
            y="Keyword",
            orientation="h",
            color="Frequency",
            color_continuous_scale=[
                [0.0,  "rgba(0,102,255,0.6)"],
                [0.5,  "rgba(0,162,255,0.8)"],
                [1.0,  "#00d4ff"],
            ],
            template="plotly_dark",
        )
        fig_kw.update_layout(
            **_PLOTLY_LAYOUT,
            height=420,
            coloraxis_showscale=False,
            xaxis=dict(
                gridcolor="rgba(0,212,255,0.08)",
                linecolor="rgba(0,212,255,0.1)",
                title=dict(text="OCCURRENCE FREQUENCY", font=dict(family="Share Tech Mono", color="#3d5a73", size=10)),
            ),
            yaxis=dict(
                gridcolor="rgba(0,0,0,0)",
                title=dict(text=""),
                tickfont=dict(family="Share Tech Mono", color="#7a9bb5", size=10),
            ),
            bargap=0.3,
        )
        fig_kw.update_traces(
            marker_line_color="rgba(0,212,255,0.3)",
            marker_line_width=1,
            hovertemplate="<b>%{y}</b><br>Frequency: %{x}<extra></extra>",
        )
        st.plotly_chart(fig_kw, use_container_width=True, config={"displayModeBar": False})

        # Show raw DataFrame in expander
        with st.expander("▸ View Raw Keyword Data Matrix"):
            styled_df = kw_df.reset_index(drop=True)
            styled_df.index += 1
            st.dataframe(styled_df, use_container_width=True)
    else:
        st.markdown(
            '<div style="font-family:\'Share Tech Mono\',monospace;color:#3d5a73;'
            'font-size:0.8rem;padding:1rem;">Insufficient text content to perform n-gram analysis.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── B: Readability Indexing ────────────────────────────────────────────────
    st.markdown('<div class="nexus-section-header">◈ READABILITY INDEXING — FLESCH-KINCAID ANALYSIS</div>', unsafe_allow_html=True)

    # SEO RATIONALE explainer block
    st.markdown("""
    <div style="background:rgba(0,102,255,0.06);border:1px solid rgba(0,102,255,0.25);
    border-radius:8px;padding:1rem 1.2rem;margin-bottom:1rem;
    font-family:'Share Tech Mono',monospace;font-size:0.78rem;color:#7a9bb5;line-height:1.8;">
    <span style="color:#00d4ff;font-weight:700;">WHY READABILITY IS AN SEO SIGNAL:</span><br>
    The Flesch-Kincaid Reading Ease (FKRE) score measures how accessible content is to a general audience.
    Pages with FKRE scores between 60–70 (Grade 8–9 level) correlate with lower bounce rates, higher
    dwell time, and more social shares — all of which are indirect behavioural signals that Google's
    quality algorithms use to assess page quality. Complex, jargon-heavy content (low FKRE) can
    reduce engagement even on authoritative domains.
    </div>
    """, unsafe_allow_html=True)

    fk_ease = d.get("fk_reading_ease")
    fk_grade = d.get("fk_grade_level")
    fog = d.get("gunning_fog")

    if fk_ease is not None:
        r1, r2, r3 = st.columns(3)

        # Flesch Reading Ease interpretation
        if fk_ease >= 70:
            ease_label, ease_color = "EASY — Mass Audience", "#00ff88"
        elif fk_ease >= 60:
            ease_label, ease_color = "STANDARD — Ideal Range", "#00d4ff"
        elif fk_ease >= 50:
            ease_label, ease_color = "FAIRLY DIFFICULT", "#ffb800"
        else:
            ease_label, ease_color = "DIFFICULT — Expert Level", "#ff2d55"

        r1.metric("FLESCH READING EASE", str(fk_ease), ease_label)
        r2.metric("F-K GRADE LEVEL", f"Grade {fk_grade}", f"US Grade {fk_grade} reading level")
        r3.metric("GUNNING FOG INDEX", str(fog), f"Grade {fog} comprehension needed")

        # Visual gauge for Reading Ease score
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=fk_ease,
            delta={"reference": 65, "increasing": {"color": "#00ff88"}, "decreasing": {"color": "#ff2d55"}},
            number={"font": {"family": "Orbitron", "color": "#00d4ff", "size": 36}},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"family": "Share Tech Mono", "color": "#3d5a73", "size": 9}},
                "bar": {"color": ease_color, "thickness": 0.25},
                "bgcolor": "rgba(0,0,0,0)",
                "bordercolor": "rgba(0,212,255,0.2)",
                "steps": [
                    {"range": [0,  30],  "color": "rgba(255,45,85,0.08)"},
                    {"range": [30, 60],  "color": "rgba(255,184,0,0.08)"},
                    {"range": [60, 80],  "color": "rgba(0,212,255,0.08)"},
                    {"range": [80, 100], "color": "rgba(0,255,136,0.08)"},
                ],
                "threshold": {
                    "line": {"color": "#00d4ff", "width": 2},
                    "thickness": 0.75,
                    "value": 65,
                },
            },
            title={"text": "FLESCH READING EASE SCORE", "font": {"family": "Share Tech Mono", "color": "#7a9bb5", "size": 11}},
        ))
        fig_gauge.update_layout(**_PLOTLY_LAYOUT, height=280)
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    else:
        st.markdown(
            '<div style="font-family:\'Share Tech Mono\',monospace;color:#3d5a73;'
            'font-size:0.8rem;padding:1rem;">Insufficient text content (&lt;30 words) to compute readability scores.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── C: Sentiment Analysis ──────────────────────────────────────────────────
    st.markdown('<div class="nexus-section-header">◈ CONTENT SENTIMENT PROFILING — PSYCHOLOGICAL TONE ANALYSIS</div>', unsafe_allow_html=True)

    polarity     = d.get("sentiment_polarity", 0.0)
    subjectivity = d.get("sentiment_subjectivity", 0.0)

    # Classify polarity
    if polarity > 0.1:
        sentiment_label = "POSITIVE"
        sentiment_color = "#00ff88"
        sentiment_icon  = "✦"
        sentiment_desc  = "The page projects an optimistic, confident, and welcoming tone — ideal for institutional authority."
    elif polarity < -0.1:
        sentiment_label = "NEGATIVE"
        sentiment_color = "#ff2d55"
        sentiment_icon  = "✗"
        sentiment_desc  = "The page carries a negative or cautionary tone, which may increase bounce rates and reduce engagement dwell time."
    else:
        sentiment_label = "NEUTRAL"
        sentiment_color = "#7a9bb5"
        sentiment_icon  = "●"
        sentiment_desc  = "The page has a factual, informational tone — appropriate for academic content but low in emotional engagement."

    # Subjectivity label
    if subjectivity > 0.6:
        subj_label = "HIGHLY SUBJECTIVE"
    elif subjectivity > 0.3:
        subj_label = "MIXED"
    else:
        subj_label = "OBJECTIVE / FACTUAL"

    sm1, sm2, sm3 = st.columns(3)
    sm1.metric("SENTIMENT TONE", sentiment_label, f"Polarity: {polarity:+.4f}")
    sm2.metric("SUBJECTIVITY", subj_label, f"Score: {subjectivity:.4f}")
    sm3.metric("CONTENT CONFIDENCE", "HIGH" if polarity > 0.05 and subjectivity < 0.5 else "LOW", "")

    # Visual polarity gauge
    st.markdown(f"""
    <div style="background:rgba(10,22,40,0.75);border:1px solid rgba(0,212,255,0.2);
    border-radius:8px;padding:1.2rem;margin-top:0.8rem;">
        <div style="font-family:'Share Tech Mono',monospace;font-size:0.7rem;
        color:#3d5a73;letter-spacing:0.1em;margin-bottom:0.8rem;">
        POLARITY SPECTRUM  [ −1.0 = NEGATIVE · 0.0 = NEUTRAL · +1.0 = POSITIVE ]</div>

        <div style="position:relative;background:linear-gradient(90deg,
            rgba(255,45,85,0.3), rgba(255,184,0,0.2), rgba(0,212,255,0.2), rgba(0,255,136,0.3));
            border-radius:4px;height:10px;overflow:visible;">
            <div style="position:absolute;
                left:{((polarity + 1) / 2 * 100):.1f}%;
                top:50%;transform:translate(-50%,-50%);
                width:14px;height:14px;border-radius:50%;
                background:{sentiment_color};
                box-shadow:0 0 10px {sentiment_color}, 0 0 3px {sentiment_color};
                border:2px solid #020509;
                transition:left 0.8s ease;">
            </div>
        </div>

        <div style="display:flex;justify-content:space-between;
        font-family:'Share Tech Mono',monospace;font-size:0.68rem;
        color:#3d5a73;margin-top:0.5rem;">
            <span>NEGATIVE −1.0</span><span>NEUTRAL 0.0</span><span>POSITIVE +1.0</span>
        </div>

        <div style="margin-top:1rem;padding:0.8rem;
        background:rgba(0,0,0,0.2);border-radius:6px;
        font-family:'Inter',sans-serif;font-size:0.82rem;
        color:#e8f4f8;line-height:1.6;border-left:3px solid {sentiment_color};">
        <span style="color:{sentiment_color};font-weight:600;">{sentiment_icon} {sentiment_label}:</span> {sentiment_desc}
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── D: NLP Summary Table ──────────────────────────────────────────────────
    st.markdown('<div class="nexus-section-header">◈ CONTENT QUALITY SUMMARY MATRIX</div>', unsafe_allow_html=True)

    summary_data = {
        "Signal": [
            "Word Count",
            "Flesch Reading Ease",
            "FK Grade Level",
            "Gunning Fog Index",
            "Sentiment Polarity",
            "Sentiment Subjectivity",
            "Keyword Diversity (Unique Bigrams)",
        ],
        "Measured Value": [
            f"{d.get('word_count', 0):,} words",
            str(fk_ease) if fk_ease else "N/A",
            f"Grade {fk_grade}" if fk_grade else "N/A",
            str(fog) if fog else "N/A",
            f"{polarity:+.4f}",
            f"{subjectivity:.4f}",
            str(len(kw_df) if kw_df is not None and not kw_df.empty else 0),
        ],
        "Benchmark Target": [
            "≥ 800 words (long-form)",
            "60–70 (General audience)",
            "Grade 8–9",
            "< 12 (Accessible)",
            "> 0.05 (Positive brand tone)",
            "0.3–0.6 (Balanced)",
            "≥ 10 distinct phrases",
        ],
        "Status": [
            "✦ PASS" if d.get("word_count", 0) >= 800 else ("⚠ WARN" if d.get("word_count", 0) >= 300 else "✗ FAIL"),
            "✦ PASS" if fk_ease and 60 <= fk_ease <= 70 else ("⚠ WARN" if fk_ease else "✗ FAIL"),
            "✦ PASS" if fk_grade and 8 <= fk_grade <= 9 else "⚠ WARN" if fk_grade else "✗ FAIL",
            "✦ PASS" if fog and fog < 12 else "⚠ WARN" if fog else "✗ FAIL",
            "✦ PASS" if polarity > 0.05 else "⚠ WARN",
            "✦ PASS" if 0.3 <= subjectivity <= 0.6 else "⚠ WARN",
            "✦ PASS" if kw_df is not None and len(kw_df) >= 10 else "⚠ WARN",
        ],
    }

    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)


# ==============================================================================
#  SECTION 6: MAIN ROUTER — Dispatch to correct page render function
# ==============================================================================

# Retrieve any cached data from session state
seo_data = st.session_state.get("seo_data", None)

if "🚨" in page:
    if seo_data is None:
        _no_data_warning()
    elif "error" in seo_data:
        _error_panel(seo_data["error"])
    else:
        render_executive_hud(seo_data)

elif "⚙️" in page:
    if seo_data is None:
        _no_data_warning()
    elif "error" in seo_data:
        _error_panel(seo_data["error"])
    else:
        render_dom_audit(seo_data)

elif "🧠" in page:
    if seo_data is None:
        _no_data_warning()
    elif "error" in seo_data:
        _error_panel(seo_data["error"])
    else:
        render_nlp_engine(seo_data)
