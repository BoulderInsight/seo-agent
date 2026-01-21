# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EngineOp is a Flask-based web analysis tool that evaluates websites across three optimization dimensions:
- **SEO** (Search Engine Optimization)
- **AEO** (Answer Engine Optimization)
- **GEO** (Generative Engine Optimization)

The tool crawls content, performs LLM-powered analysis via Anthropic or OpenAI APIs, and generates prioritized recommendations in Markdown, HTML, CSV, and PDF formats.

## Commands

```bash
# Run the application (http://localhost:5000)
python run.py

# Run tests
pytest
pytest tests/ -v --tb=short

# Linting
ruff check .
ruff check . --fix

# Type checking
mypy app/
```

## Architecture

### Analysis Workflow (Orchestrator Pattern)

The `app/services/orchestrator.py` coordinates the complete analysis pipeline:

1. **Crawling** - `crawler.py` fetches page(s) via BFS within domain
2. **Structure Analysis** - `structure_analyzer.py` validates HTML (H1s, meta, headings)
3. **LLM Analysis** (parallel) - Three analyzers call LLM concurrently:
   - `seo_analyzer.py` - Keywords, content gaps, quality scoring
   - `aeo_analyzer.py` - Q&A opportunities, featured snippet potential
   - `geo_analyzer.py` - Content defensibility, citation-worthiness, absorption risks
4. **Classification** - `classifier.py` determines content type
5. **Aggregation** - `aggregator.py` + `priority.py` score and combine recommendations
6. **Report Generation** - `report_generator.py` produces all output formats

### Key Data Flow

```
PageData (crawler) → Analysis models (LLM) → Recommendations → AnalysisResult
```

### Service Layer

- `LLMClient` (`llm_client.py`) - Abstracts Anthropic/OpenAI with retry logic and rate limit handling
- `Storage` (`storage.py`) - SQLite wrapper at `data/analyses.db`
- `csv_parser.py` - Handles SEMrush/Ahrefs keyword CSV formats

### Routes

- `POST /analyze` - Start analysis (rate-limited: 10/hour per session)
- `GET /results/<id>` - View results
- `GET /download/<id>/<format>` - Download (markdown/html/csv/pdf)
- `GET /history` - Past analyses

## Environment Variables

Required in `.env`:
```
LLM_PROVIDER=anthropic        # or "openai"
ANTHROPIC_API_KEY=...         # if using Anthropic
OPENAI_API_KEY=...            # if using OpenAI
```

## Key Models (`app/models.py`)

- `PageData` - Crawled page with extracted elements
- `SEOAnalysis`, `AEOAnalysis`, `GEOAnalysis` - LLM analysis outputs
- `Recommendation` with `PriorityScore` - Scored actionable items
- `AnalysisResult` - Complete result container

## Brand Colors

When working on UI or PDF generation, use these category colors:
- SEO: `#0eb981` (green)
- AEO: `#3b83f7` (blue)
- GEO: `#f59e0d` (orange)

## PDF Generation

`report_generator.py` uses WeasyPrint. The logo is embedded as base64 from `EngineOpDark.png`. The PDF follows a 6-page structure: Cover, Executive Summary, SEO, AEO, GEO, Action Roadmap.
