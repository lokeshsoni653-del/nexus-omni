
================================================================================
  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗     ██████╗ ███╗   ███╗███╗   ██╗██╗
  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝    ██╔═══██╗████╗ ████║████╗  ██║██║
  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗    ██║   ██║██╔████╔██║██╔██╗ ██║██║
  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║    ██║   ██║██║╚██╔╝██║██║╚██╗██║██║
  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║    ╚██████╔╝██║ ╚═╝ ██║██║ ╚████║██║
  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝     ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝

  NEXUS OMNI: Enterprise SEO Telemetry Suite
  Version    : 3.0.0 — Production Release
  Platform   : Python / Streamlit
  Assessment : SEO & Digital Marketing — SABS University
================================================================================


--------------------------------------------------------------------------------
  WHAT IS THIS PROJECT?
--------------------------------------------------------------------------------

NEXUS OMNI is a live, custom-coded, multi-page web application built entirely
in Python. It performs real-time SEO (Search Engine Optimisation) diagnostics
on any website by directly fetching, scraping, and analysing its HTML source
code — no third-party SEO tools, no APIs, no subscriptions.

You enter a URL, click "Initiate Telemetry Scan," and within seconds the
application delivers a full technical audit across three dashboards:

  [1] EXECUTIVE HUD       — High-level KPI scores and health overview
  [2] DOM STRUCTURAL AUDIT — Deep technical inspection of the page's HTML
  [3] SEMANTIC NLP ENGINE  — AI-powered content and keyword analysis

This was built from scratch as a portfolio project to demonstrate applied
software engineering skills within a Digital Marketing context.


--------------------------------------------------------------------------------
  TECH STACK
--------------------------------------------------------------------------------

  Language      :  Python 3.10+
  Framework     :  Streamlit  (multi-page web interface)
  Web Scraping  :  Requests + BeautifulSoup4 + lxml
  Data          :  Pandas + NumPy
  Visualisation :  Plotly Graph Objects + Plotly Express
  NLP           :  NLTK (stopwords, n-gram tokenisation)
                   TextBlob (sentiment polarity & subjectivity)
                   TextStat (Flesch-Kincaid readability indexing)
  Styling       :  Custom CSS injected via Streamlit (cyberpunk / glassmorphism)


--------------------------------------------------------------------------------
  FILE STRUCTURE
--------------------------------------------------------------------------------

  nexus-omni/
  │
  ├── app.py              ← The entire application (single-file architecture)
  ├── requirements.txt    ← All Python dependencies (pinned versions)
  └── README.txt          ← This file


--------------------------------------------------------------------------------
  HOW TO INSTALL & RUN
--------------------------------------------------------------------------------

STEP 1 — Make sure Python 3.10 or higher is installed.
         Check by running:  python --version

STEP 2 — Open a terminal / PowerShell window and navigate to this folder:
         cd path\to\nexus-omni

STEP 3 — Install all dependencies:
         pip install -r requirements.txt --timeout 300 --retries 10

         NOTE: This may take 3–8 minutes on a slow connection.
               pyarrow (~27 MB) and numpy (~13 MB) are the largest packages.
               If it times out, re-run the same command — pip resumes from cache.

STEP 4 — Launch the application:
         streamlit run app.py

STEP 5 — The app will automatically open in your browser at:
         http://localhost:8501

STEP 6 — In the sidebar, enter any URL (e.g., https://www.sabs.edu.pk)
         and click "INITIATE TELEMETRY SCAN".


--------------------------------------------------------------------------------
  DASHBOARD PAGES — WHAT THEY DO
--------------------------------------------------------------------------------

  PAGE 1: EXECUTIVE HUD
  ─────────────────────
  The "boardroom view." Displays the most critical SEO signals at a glance:

  • Global Health Score (0–100)
    A composite score aggregated from four SEO pillars: Meta Health,
    DOM Structure, Accessibility, and Content Quality.

  • Time to First Byte (TTFB)
    Measures server response speed in milliseconds. Google's Core Web Vitals
    guidelines classify TTFB < 200ms as "Good," 200–600ms as "Needs Improvement,"
    and > 600ms as "Poor." Slow TTFB reduces crawl budget allocation.

  • SEO Health Radar Chart
    An interactive Plotly radar chart showing scores across all four pillars
    plotted against a perfect-score reference polygon.

  • HTML5 Semantic Landmark Audit
    A boolean checklist of <header>, <main>, <nav>, <footer>, <article>,
    <section>, <aside>. These help Googlebot understand page regions.

  • Quick Diagnostic Metrics
    H1 tag count, title length, meta description length, JSON-LD schema
    detection, Open Graph status, and canonical URL status.


  PAGE 2: DOM STRUCTURAL AUDIT
  ─────────────────────────────
  The technical engine room. Performs deep HTML architecture analysis:

  • Meta Architecture Matrix
    Extracts the <title> and <meta name="description"> tags. Displays a
    visual character-fill bar showing whether lengths are within the
    optimal Google SERP display ranges:
      - Title: 50–60 characters (avoids truncation in search results)
      - Description: 150–160 characters (maximises preview real estate)

  • Heading Hierarchy Tree
    Extracts all H1, H2, and H3 tags and renders them as a nested visual
    tree. Issues a critical alert if:
      - No H1 exists (crawler cannot determine the primary page topic)
      - Multiple H1s exist (topic dilution across the document)

  • Schema & Open Graph Intelligence
    Scans for JSON-LD structured data (Schema.org) and OpenGraph (og:) tags.
    JSON-LD enables Rich Results in Google SERPs (star ratings, FAQ dropdowns,
    breadcrumbs), which can increase Click-Through Rate by 20–30%.
    OpenGraph controls how pages appear when shared on social media.

  • Accessibility Engine — Alt Text Audit
    Identifies every <img> tag missing an alt attribute. Each missing alt
    is simultaneously:
      (a) A WCAG 2.1 Level A accessibility violation
      (b) A missed keyword injection point for Google Image Search
    The full list of offending image URLs is displayed in an expandable panel.

  • Link Architecture Analysis
    Counts internal vs. external links. Internal links distribute PageRank
    through the site. External links to credible sources signal topical authority.


  PAGE 3: SEMANTIC NLP ENGINE
  ────────────────────────────
  AI-powered content analysis using Natural Language Processing:

  • Lexical Density — Keyword Extraction
    Tokenises the entire page body text, removes English stop words (the, and,
    is, etc.), and computes the frequency of all bigrams (2-word phrases) and
    trigrams (3-word phrases). The top 15 are rendered as an interactive
    horizontal bar chart.

    WHY THIS MATTERS: Google's BERT and MUM language models understand phrase-
    level intent. High-frequency relevant phrases confirm topical authority.

  • Flesch-Kincaid Readability Indexing
    Calculates three readability scores using the TextStat library:
      - Flesch Reading Ease  (target: 60–70 for general audiences)
      - Flesch-Kincaid Grade Level  (target: Grade 8–9)
      - Gunning Fog Index  (target: < 12)

    WHY THIS MATTERS: Complex content (low readability) correlates with higher
    bounce rates and lower dwell time — indirect negative ranking signals.

  • Content Sentiment Profiling
    Uses TextBlob's NLP model to calculate:
      - Polarity  : -1.0 (very negative) to +1.0 (very positive)
      - Subjectivity : 0.0 (factual) to 1.0 (highly opinionated)

    A visual polarity spectrum bar shows where the page's tone sits.
    University and institutional pages should score slightly positive
    to project authority and confidence.

  • Content Quality Summary Matrix
    A full data table comparing every measured NLP metric against its
    industry benchmark, with a clear PASS / WARN / FAIL status flag.


--------------------------------------------------------------------------------
  HOW THE GLOBAL HEALTH SCORE IS CALCULATED
--------------------------------------------------------------------------------

  The score is out of 100, derived from four pillars each worth 25 points:

  PILLAR 1 — META HEALTH (25 pts)
    +8  pts : Title tag exists
    +5  pts : Title length is 50–60 chars (optimal)
    +7  pts : Meta description exists
    +5  pts : Description length is 150–160 chars (optimal)

  PILLAR 2 — DOM STRUCTURE (25 pts)
    +10 pts : Exactly one H1 tag (canonical best practice)
    +6  pts : Two or more H2 tags present
    +3  pts : At least one H3 tag present
    +6  pts : Up to 6 HTML5 semantic landmark elements detected

  PILLAR 3 — ACCESSIBILITY (25 pts)
    +15 pts : Alt text coverage score (proportional to images with alt)
    +10 pts : Internal link count ≥ 10 (strong site navigation structure)

  PILLAR 4 — CONTENT QUALITY (25 pts)
    +8  pts : Word count ≥ 800 (long-form content)
    +7  pts : Flesch Reading Ease score is 50–70 (accessible)
    +5  pts : JSON-LD structured data detected
    +5  pts : OpenGraph title and description both present

  FINAL SCORE = Average of four pillar scores scaled to 100
  Ratings:  80–100 = EXCELLENT  |  55–79 = MODERATE  |  0–54 = CRITICAL


--------------------------------------------------------------------------------
  IMPORTANT NOTES
--------------------------------------------------------------------------------

  • Some websites block automated scrapers (Cloudflare, WAF protection).
    The app handles this gracefully with a styled error message — no raw
    Python tracebacks are ever shown to the user.

  • Some university sites use self-signed SSL certificates. The app
    automatically retries with SSL verification disabled in this case.

  • Results are cached for 5 minutes per URL to avoid hammering the target
    server with repeated requests during a single session.

  • NLTK language data (stopwords, punkt tokeniser) is downloaded
    automatically on first launch and requires a one-time internet connection.


--------------------------------------------------------------------------------
  CONTACT / CREDITS
--------------------------------------------------------------------------------

  Developed by    : Lokesh Kumar (Software Engineering Student, SABS University)
  Assessment      : SEO & Digital Marketing
  Academic Year   : 2026
  Architecture    : Single-file Streamlit MPA (Multi-Page Application)
  Lines of Code   : ~700 (app.py) — fully commented with SEO rationale

================================================================================
  END OF README
================================================================================
