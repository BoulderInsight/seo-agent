# PRD: Web Analysis Tool for SEO, AEO, and GEO

## Introduction

A browser-based web analysis tool that evaluates websites and individual pages across three optimization dimensions: traditional Search Engine Optimization (SEO), Answer Engine Optimization (AEO), and Generative Engine Optimization (GEO). The tool helps marketers, founders, and agencies understand how their content performs for both traditional search engines and AI-powered answer engines.

Users provide a URL (single page or full site) and optionally upload keyword data from SEMrush/Ahrefs CSVs. The tool crawls the content, analyzes it using LLM-powered evaluation, and produces prioritized recommendations in a human-readable report.

## Goals

- Enable single-page or multi-page site analysis with configurable crawl depth
- Accept optional CSV uploads containing keyword/search data from SEMrush or Ahrefs
- Identify SEO opportunities: keyword gaps, missing clusters, content structure issues
- Identify AEO opportunities: question-based content, FAQ potential, People Also Ask alignment
- Identify GEO opportunities: content defensibility, citation-worthiness, proprietary value
- Classify each content piece as SEO, AEO, GEO, or overlapping
- Flag content at risk of LLM absorption without citation
- Generate prioritized recommendations with clear rationale
- Output reports in Markdown and HTML formats
- Optionally export keywords and questions as CSV

## User Stories

### US-001: Project scaffolding and configuration
**Description:** As a developer, I need the basic project structure with dependencies so I can build the application.

**Acceptance Criteria:**
- [ ] Create Python project with `pyproject.toml` or `requirements.txt`
- [ ] Include dependencies: Flask/FastAPI, BeautifulSoup4, requests, openai/anthropic SDK
- [ ] Create folder structure: `app/`, `app/routes/`, `app/services/`, `app/templates/`, `app/static/`
- [ ] Create `.env.example` with required environment variables (LLM API key)
- [ ] Create basic `README.md` with setup instructions
- [ ] Typecheck passes (if using type hints) or linting passes

---

### US-002: Basic web server with home page
**Description:** As a user, I want to access the tool via a web browser so I can use a visual interface.

**Acceptance Criteria:**
- [ ] Flask/FastAPI app runs on `localhost:5000` (or similar)
- [ ] Home page renders at `/` with application title
- [ ] Basic HTML template with CSS styling (clean, professional look)
- [ ] Typecheck/lint passes
- [ ] Verify home page loads in browser

---

### US-003: URL input form on home page
**Description:** As a user, I want to enter a URL to analyze so the tool knows what content to evaluate.

**Acceptance Criteria:**
- [ ] Form with text input for URL
- [ ] Radio buttons or toggle: "Single Page" vs "Full Site"
- [ ] Number input for max pages (shown only when "Full Site" selected, default 10, max 50)
- [ ] Submit button labeled "Analyze"
- [ ] Client-side validation: URL must start with http:// or https://
- [ ] Typecheck/lint passes
- [ ] Verify form displays and validates in browser

---

### US-004: CSV upload for keyword data
**Description:** As a user, I want to optionally upload a CSV with keyword data so the tool can incorporate search volume and difficulty metrics.

**Acceptance Criteria:**
- [ ] File upload input on home page form (optional, not required)
- [ ] Accepts `.csv` files only
- [ ] Help text explaining expected format (columns: keyword, volume, difficulty, cpc)
- [ ] Upload limited to 5MB max file size
- [ ] Typecheck/lint passes
- [ ] Verify file selector works in browser

---

### US-005: CSV parsing service
**Description:** As a developer, I need a service to parse uploaded CSV files into structured keyword data.

**Acceptance Criteria:**
- [ ] Service function: `parse_keyword_csv(file) -> list[KeywordData]`
- [ ] Handles SEMrush format (Keyword, Search Volume, Keyword Difficulty, CPC)
- [ ] Handles Ahrefs format (Keyword, Volume, KD, CPC)
- [ ] Returns list of dicts with normalized keys: `keyword`, `volume`, `difficulty`, `cpc`
- [ ] Gracefully handles missing columns (uses None for missing values)
- [ ] Raises clear error for unparseable files
- [ ] Unit tests for both formats pass
- [ ] Typecheck/lint passes

---

### US-006: Single page crawler service
**Description:** As a developer, I need a service to fetch and extract content from a single URL.

**Acceptance Criteria:**
- [ ] Service function: `crawl_page(url) -> PageData`
- [ ] Fetches HTML with proper User-Agent header
- [ ] Extracts: title, meta description, h1-h6 headings, paragraph text, links
- [ ] Handles timeouts (10 second limit)
- [ ] Handles HTTP errors gracefully (returns error status)
- [ ] Returns structured `PageData` object with all extracted content
- [ ] Typecheck/lint passes

---

### US-007: Multi-page crawler service
**Description:** As a developer, I need a service to crawl multiple pages from a site up to a configurable limit.

**Acceptance Criteria:**
- [ ] Service function: `crawl_site(start_url, max_pages) -> list[PageData]`
- [ ] Discovers internal links from each crawled page
- [ ] Respects `max_pages` limit (stops when reached)
- [ ] Avoids duplicate URLs (normalizes and dedupes)
- [ ] Stays within same domain (no external links)
- [ ] Returns list of `PageData` objects
- [ ] Typecheck/lint passes

---

### US-008: Content structure analyzer
**Description:** As a developer, I need a service to analyze page structure and identify structural issues.

**Acceptance Criteria:**
- [ ] Service function: `analyze_structure(page_data) -> StructureAnalysis`
- [ ] Detects: missing H1, multiple H1s, skipped heading levels
- [ ] Detects: missing meta description, meta description too long/short
- [ ] Detects: thin content (< 300 words), very long content (> 3000 words)
- [ ] Detects: presence/absence of FAQ sections, TLDR sections
- [ ] Detects: presence of schema.org markup
- [ ] Returns structured analysis with findings and severity levels
- [ ] Typecheck/lint passes

---

### US-009: LLM client service
**Description:** As a developer, I need a service to send prompts to an LLM and receive responses.

**Acceptance Criteria:**
- [ ] Service class: `LLMClient` with method `analyze(prompt, content) -> str`
- [ ] Reads API key from environment variable
- [ ] Supports OpenAI or Anthropic (configurable via env var)
- [ ] Handles rate limits with basic retry (3 attempts)
- [ ] Handles API errors gracefully with clear error messages
- [ ] Typecheck/lint passes

---

### US-010: SEO analysis prompt and parser
**Description:** As a developer, I need an LLM prompt to analyze content for SEO opportunities.

**Acceptance Criteria:**
- [ ] Prompt template that accepts page content and optional keyword data
- [ ] Asks LLM to identify: primary topic, target keywords, missing keyword opportunities
- [ ] Asks LLM to identify: content gaps, thematic cluster opportunities
- [ ] Asks LLM to rate content quality for SEO (1-10 scale with rationale)
- [ ] Parser function to extract structured data from LLM response
- [ ] Returns `SEOAnalysis` object with findings
- [ ] Typecheck/lint passes

---

### US-011: AEO analysis prompt and parser
**Description:** As a developer, I need an LLM prompt to analyze content for Answer Engine Optimization.

**Acceptance Criteria:**
- [ ] Prompt template that accepts page content
- [ ] Asks LLM to identify: questions the content answers, questions it should answer
- [ ] Asks LLM to identify: People Also Ask opportunities, featured snippet potential
- [ ] Asks LLM to evaluate: answer format quality (concise, direct, well-structured)
- [ ] Asks LLM to rate AEO readiness (1-10 scale with rationale)
- [ ] Parser function to extract structured data from LLM response
- [ ] Returns `AEOAnalysis` object with findings
- [ ] Typecheck/lint passes

---

### US-012: GEO analysis prompt and parser
**Description:** As a developer, I need an LLM prompt to analyze content for Generative Engine Optimization.

**Acceptance Criteria:**
- [ ] Prompt template that accepts page content
- [ ] Asks LLM to evaluate: content originality (generic vs. proprietary)
- [ ] Asks LLM to identify: citation-worthy elements (frameworks, data, unique insights)
- [ ] Asks LLM to flag: content at risk of absorption without attribution
- [ ] Asks LLM to suggest: ways to make content more defensible and authoritative
- [ ] Asks LLM to rate GEO strength (1-10 scale with rationale)
- [ ] Parser function to extract structured data from LLM response
- [ ] Returns `GEOAnalysis` object with findings
- [ ] Typecheck/lint passes

---

### US-013: Content classification service
**Description:** As a developer, I need a service to classify content as SEO, AEO, GEO, or overlapping.

**Acceptance Criteria:**
- [ ] Service function: `classify_content(seo, aeo, geo) -> ContentClassification`
- [ ] Uses scores from all three analyses to determine primary optimization type
- [ ] Identifies overlapping opportunities (content that serves multiple purposes)
- [ ] Returns classification with confidence level and explanation
- [ ] Typecheck/lint passes

---

### US-014: Priority scoring service
**Description:** As a developer, I need a service to calculate priority scores for recommendations.

**Acceptance Criteria:**
- [ ] Service function: `calculate_priority(recommendation, keyword_data) -> PriorityScore`
- [ ] Factors: potential impact (high/medium/low), effort estimate, keyword volume if available
- [ ] Factors: competition/difficulty if available, strategic value
- [ ] Returns score 1-100 with breakdown of contributing factors
- [ ] Sorts recommendations by priority score descending
- [ ] Typecheck/lint passes

---

### US-015: Recommendation aggregator service
**Description:** As a developer, I need a service to compile all analyses into prioritized recommendations.

**Acceptance Criteria:**
- [ ] Service function: `aggregate_recommendations(structure, seo, aeo, geo, keywords) -> list[Recommendation]`
- [ ] Combines findings from all analysis types
- [ ] Deduplicates similar recommendations
- [ ] Applies priority scoring to each recommendation
- [ ] Groups recommendations by type (SEO, AEO, GEO, Structure)
- [ ] Returns sorted list with top recommendations first
- [ ] Typecheck/lint passes

---

### US-016: Markdown report generator
**Description:** As a user, I want the analysis results as a Markdown report so I can read and share findings easily.

**Acceptance Criteria:**
- [ ] Service function: `generate_markdown_report(analysis_results) -> str`
- [ ] Includes: Executive summary with overall scores
- [ ] Includes: Page-by-page breakdown (for multi-page analysis)
- [ ] Includes: Top 10 prioritized recommendations with rationale
- [ ] Includes: SEO findings section with keyword opportunities
- [ ] Includes: AEO findings section with question opportunities
- [ ] Includes: GEO findings section with defensibility analysis
- [ ] Includes: Structural issues and fixes
- [ ] Well-formatted with headers, lists, and emphasis
- [ ] Typecheck/lint passes

---

### US-017: HTML report generator
**Description:** As a user, I want the analysis results as an HTML report so I can view them with nice formatting in a browser.

**Acceptance Criteria:**
- [ ] Service function: `generate_html_report(analysis_results) -> str`
- [ ] Converts Markdown report to styled HTML
- [ ] Includes CSS for professional appearance (colors, typography, spacing)
- [ ] Includes collapsible sections for detailed findings
- [ ] Includes visual score indicators (colored badges or bars)
- [ ] Responsive design (readable on desktop and tablet)
- [ ] Typecheck/lint passes

---

### US-018: CSV export for keywords and questions
**Description:** As a user, I want to export discovered keywords and questions as a CSV so I can use them in other tools.

**Acceptance Criteria:**
- [ ] Service function: `generate_csv_export(analysis_results) -> str`
- [ ] Includes columns: item, type (keyword/question), source (SEO/AEO/GEO), priority, notes
- [ ] Includes all discovered keyword opportunities
- [ ] Includes all discovered question opportunities
- [ ] Proper CSV escaping for special characters
- [ ] Typecheck/lint passes

---

### US-019: Analysis orchestrator service
**Description:** As a developer, I need a main service to coordinate the full analysis workflow.

**Acceptance Criteria:**
- [ ] Service function: `run_analysis(url, mode, max_pages, keyword_csv) -> AnalysisResult`
- [ ] Orchestrates: crawling → structure analysis → LLM analyses → classification → recommendations
- [ ] Handles single page vs. full site mode
- [ ] Integrates keyword data if CSV provided
- [ ] Returns complete `AnalysisResult` with all components
- [ ] Handles errors gracefully with partial results where possible
- [ ] Typecheck/lint passes

---

### US-020: Analysis API endpoint
**Description:** As a user, I want to submit an analysis request and receive results via the web interface.

**Acceptance Criteria:**
- [ ] POST endpoint `/analyze` accepts form data (URL, mode, max_pages, CSV file)
- [ ] Validates inputs and returns clear error messages for invalid data
- [ ] Calls analysis orchestrator service
- [ ] Returns redirect to results page on success
- [ ] Handles analysis errors with user-friendly error page
- [ ] Typecheck/lint passes
- [ ] Verify form submission works in browser

---

### US-021: Analysis progress indicator
**Description:** As a user, I want to see progress while analysis runs so I know the tool is working.

**Acceptance Criteria:**
- [ ] Loading page shown after form submission
- [ ] Displays current step: "Crawling...", "Analyzing SEO...", "Analyzing AEO...", etc.
- [ ] Uses polling or server-sent events to update status
- [ ] Shows estimated time or progress percentage
- [ ] Redirects to results when complete
- [ ] Typecheck/lint passes
- [ ] Verify progress displays in browser

---

### US-022: Results page with Markdown report
**Description:** As a user, I want to view the analysis results on a dedicated results page.

**Acceptance Criteria:**
- [ ] Results page at `/results/<analysis_id>`
- [ ] Displays rendered Markdown report as HTML
- [ ] Shows overall scores prominently (SEO, AEO, GEO scores)
- [ ] Shows content classification badge
- [ ] Clean, readable typography
- [ ] Typecheck/lint passes
- [ ] Verify results page displays correctly in browser

---

### US-023: Download buttons for reports
**Description:** As a user, I want to download the report in different formats so I can save and share it.

**Acceptance Criteria:**
- [ ] "Download Markdown" button on results page
- [ ] "Download HTML" button on results page
- [ ] "Download CSV" button on results page (keywords/questions export)
- [ ] Downloads trigger file save with appropriate filename (includes domain and date)
- [ ] Typecheck/lint passes
- [ ] Verify all download buttons work in browser

---

### US-024: Analysis history storage
**Description:** As a user, I want past analyses saved so I can revisit them later.

**Acceptance Criteria:**
- [ ] Store analysis results in SQLite database (or JSON files for simplicity)
- [ ] Each analysis has unique ID, timestamp, URL, and results
- [ ] Results persist across server restarts
- [ ] Typecheck/lint passes

---

### US-025: Analysis history page
**Description:** As a user, I want to see a list of past analyses so I can compare results over time.

**Acceptance Criteria:**
- [ ] History page at `/history`
- [ ] Lists past analyses: URL, date, overall scores
- [ ] Sorted by date descending (most recent first)
- [ ] Click to view full results
- [ ] Delete button to remove old analyses
- [ ] Typecheck/lint passes
- [ ] Verify history page works in browser

---

### US-026: Error handling and user feedback
**Description:** As a user, I want clear error messages when something goes wrong so I can fix issues.

**Acceptance Criteria:**
- [ ] Invalid URL shows specific error message
- [ ] Crawl failures show which URLs failed and why
- [ ] LLM API errors show helpful message (check API key, rate limits)
- [ ] CSV parse errors show line number and issue
- [ ] All errors use consistent error page template
- [ ] Typecheck/lint passes
- [ ] Verify error messages display correctly

---

### US-027: Environment configuration and validation
**Description:** As a user, I want the tool to validate configuration on startup so I know if setup is incomplete.

**Acceptance Criteria:**
- [ ] Check for required environment variable (LLM API key) on startup
- [ ] Display clear error if API key missing
- [ ] Log which LLM provider is configured
- [ ] Support `.env` file loading
- [ ] Typecheck/lint passes

---

### US-028: Basic rate limiting and abuse prevention
**Description:** As a developer, I need basic protections against abuse of the analysis tool.

**Acceptance Criteria:**
- [ ] Limit max pages per analysis to 50
- [ ] Limit max CSV file size to 5MB
- [ ] Add delay between page fetches (1 second) to avoid hammering sites
- [ ] Basic request rate limiting (max 10 analyses per hour per session)
- [ ] Typecheck/lint passes

## Non-Goals

- **No CMS integration**: Tool does not publish or modify any content directly
- **No backlink analysis**: No crawling or buying of backlinks
- **No competitor analysis**: Focus is on the provided URL only, not competitors
- **No real-time monitoring**: One-time analysis only, no continuous tracking
- **No user authentication**: Tool runs locally or as a simple web app without accounts
- **No paid API integrations**: Only CSV import for keyword data, no SEMrush/Ahrefs API calls
- **No content generation**: Recommendations only, no AI-written content output
- **No browser extension**: Web app only for initial version

## Technical Considerations

### Tech Stack
- **Backend**: Python 3.11+ with Flask or FastAPI
- **Crawling**: requests + BeautifulSoup4 (or httpx for async)
- **LLM**: OpenAI or Anthropic SDK (configurable)
- **Storage**: SQLite for analysis history
- **Frontend**: Jinja2 templates with minimal JavaScript
- **Styling**: Tailwind CSS or simple custom CSS

### LLM Usage
- Required for SEO, AEO, and GEO analysis
- User must provide API key via environment variable
- Consider token costs: summarize long content before sending to LLM
- Use structured prompts to get parseable responses

### Crawling Considerations
- Respect robots.txt where reasonable
- Use appropriate User-Agent string
- Add delays between requests to be polite
- Handle common issues: redirects, JavaScript-rendered content (note: JS content may not be fully captured)

### CSV Format Support
- SEMrush export format (Keyword, Search Volume, Keyword Difficulty, CPC)
- Ahrefs export format (Keyword, Volume, KD, CPC)
- Flexible parser that handles column name variations

### Report Structure
- Executive summary with scores and top recommendations
- Detailed findings organized by category (SEO, AEO, GEO, Structure)
- Each recommendation includes: what, why, priority, and how

## Execution & Tooling Contract

This PRD is intended to be executed autonomously using an agentic workflow (Ralph) in YOLO mode.

### Execution Rules
- Do not ask clarifying questions
- Do not pause for confirmation
- Do not modify scope unless required to satisfy acceptance criteria
- Execute user stories in dependency order
- Treat acceptance criteria as binding requirements
- Favor working, verifiable implementations over placeholders

### Tooling Authorization

The following tools and plugins are authorized for use during execution:

- **frontend-design**
  - Use for UI layout, component structure, and visual hierarchy
  - Do not redesign branding or invent visual identity
  - Focus on clarity, hierarchy, and usability

- **commit-commands**
  - Use only if code artifacts are generated
  - Commits should be logical, atomic, and scoped to completed user stories

- **code-review**
  - Use only as a final verification step
  - Do not block execution on review feedback

The following tools may be installed but should not be used unless explicitly required by acceptance criteria:
- github
- playwright
- context7
- pinecone

### Output Expectations
- Code should be runnable locally
- All acceptance criteria should be verifiable
- Errors should fail loudly and clearly
