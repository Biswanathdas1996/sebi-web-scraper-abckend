# SEBI Circulars Multi-Agent Workflow (LangChain + LangGraph)

Pipeline:

1. Scrape listing metadata
2. Download PDFs
3. Summarize PDFs
4. Generate static dashboard

## Setup

```powershell
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

Optional OpenAI key for better summaries:

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

## Run

```powershell
python index.py
```

Open `site/index.html` afterward.
