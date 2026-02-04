# MD Crawler

A web crawler that converts websites to markdown format, creating a local mirror with properly linked pages.

## Features

- **Headless browser crawling** using Selenium for JavaScript-enabled sites
- **Advanced markdown conversion** with Docling (no BeautifulSoup dependency)
- **Local link conversion** - all internal links are converted to local markdown paths
- **Domain restriction** - stays within the target website's domain
- **CLI interface** - simple command-line usage with Typer

## Requirements

- Python >= 3.12
- Chrome/Chromium browser
- chromedriver matching your Chrome version

## Installation

```bash
uv sync
```

## Usage

### Crawl a website

```bash
uv run mdcrawler crawl https://example.com
```

### Options

| Option | Description |
|--------|-------------|
| `-o, --output DIRECTORY` | Output directory (default: `mirror`) |
| `-m, --max-pages N` | Maximum number of pages to crawl (default: `10`) |

### Examples

```bash
# Crawl a website with default settings (max 10 pages)
uv run mdcrawler crawl https://example.com

# Crawl up to 50 pages
uv run mdcrawler crawl https://example.com --max-pages 50

# Output to custom directory
uv run mdcrawler crawl https://example.com -o ./my-mirror

# Combine options
uv run mdcrawler crawl https://example.com --output ./mirror --max-pages 100
```

### Single page conversion

```bash
uv run mdcrawler single-page https://example.com/page --output page.md
```

## Output

Each crawled page is saved as a markdown file in the output directory:
- `index.md` for the homepage
- `path_to_page.md` for subpages
- Query parameters are hashed to create unique filenames

Internal links are converted from:
```markdown
[Link text](https://example.com/page)
```
to:
```markdown
[Link text](page.md)
```

## Requirements

- Python >= 3.12
- Chrome/Chromium browser
- chromedriver matching your Chrome version

Note: Make sure your chromedriver version matches your Chrome version. You can download the matching version from https://chromedriver.chromium.org/

## License

MIT
