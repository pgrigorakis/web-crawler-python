# web-crawler-python

An async web crawler that starts from a base URL, follows internal links, and
writes a JSON report of each page's heading, first paragraph, and outgoing links.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
git clone git@github.com:pgrigorakis/web-crawler-python.git
cd web-crawler-python
uv sync
```

## Usage

```bash
uv run main.py <base_url> <max_concurrency> <max_pages>
```

- `base_url` — where to start crawling
- `max_concurrency` — max simultaneous requests
- `max_pages` — stop after crawling this many pages

Example:

```bash
uv run main.py https://learnwebscraping.dev/practice/ecommerce/ 5 50
```

Results are written to `report.json`.

## Tests

```bash
uv run python -m unittest
```
