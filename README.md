# MD Crawler v0.2.1

A web crawler that converts websites to markdown format, creating a local mirror with properly linked pages.

## Features

- **Headless browser crawling** using Selenium
- **Advanced markdown conversion** with Docling
- **Local link conversion** - internal links to local markdown paths
- **Domain restriction** - stays within target website
- **CLI interface** with Typer
- **Asset downloading** - to `assets/` subdirectory

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
| `-o, --output` | Output directory |
| `-m, --max-pages` | Maximum pages to crawl |
| `--download-assets` | Download assets |

### Examples

```bash
uv run mdcrawler crawl https://example.com
uv run mdcrawler crawl https://example.com --max-pages 50
uv run mdcrawler crawl https://example.com -o ./my-mirror
uv run mdcrawler crawl https://example.com --download-assets
uv run mdcrawler crawl https://example.com --max-pages 100 --download-assets
```

### Single page conversion

```bash
uv run mdcrawler single-page https://example.com/page --output page.md
```

## Output

Each crawled page saved as markdown file:
- `index.md` for homepage
- Subpages as `path_to_page.md`

Internal links converted from `[text](url)` to `[text](page.md)`.

Assets downloaded to `assets/` subdirectory.

## License

MIT
