# kg_extractor

A Python library for extracting knowledge graphs from text using LLMs and storing them in FalkorDB.

## Installation

```bash
pip install .
```

## Requirements
- Python 3.8+
- FalkorDB running locally (default: localhost:6379)
- Google Gemini API key (set `GEMINI_API_KEY` in your `.env`)

## Usage

```python
from kg_extractor import extract_knowledge_graph
from kg_extractor.input_text import text  # Example input

# Your own list of dicts, e.g., [{"article_0": "..."}, ...]
# text = ...

db_name = "your_db_name"
extract_knowledge_graph(text, db_name)
```

## Example
See `examples/run_extraction.py` for a runnable example.

## License
MIT
