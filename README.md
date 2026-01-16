# SEO Agent - Web Analysis Tool

A browser-based web analysis tool that evaluates websites across three optimization dimensions:
- **SEO** (Search Engine Optimization)
- **AEO** (Answer Engine Optimization)
- **GEO** (Generative Engine Optimization)

## Setup

### Prerequisites
- Python 3.11 or higher
- An API key from OpenAI or Anthropic

### Installation

1. Clone the repository and navigate to the project directory:
```bash
cd seo-agent
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create your environment file:
```bash
cp .env.example .env
```

5. Edit `.env` and add your API key:
```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here
```

### Running the Application

```bash
python run.py
```

The application will be available at `http://localhost:5000`

## Usage

1. Enter a URL to analyze
2. Choose "Single Page" or "Full Site" mode
3. Optionally upload a CSV with keyword data from SEMrush or Ahrefs
4. Click "Analyze" and wait for results
5. Download reports in Markdown, HTML, or CSV format

## CSV Format

The tool accepts keyword CSV exports from SEMrush or Ahrefs with columns:
- Keyword
- Search Volume / Volume
- Keyword Difficulty / KD
- CPC

## Development

Run linting:
```bash
ruff check .
```

Run type checking:
```bash
mypy app/
```

Run tests:
```bash
pytest
```
