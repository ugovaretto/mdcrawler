# MD Crawler v0.6.0

A web crawler that converts websites to markdown format, creating a local mirror with properly linked pages.

## Features

- **Headless browser crawling** using Selenium
- **Advanced markdown conversion** with Docling
- **Local link conversion** - internal links to local markdown paths
- **Domain restriction** - stays within target website
- **CLI interface** with Typer
- **Depth control** - crawl specific depth levels from starting URL
- **Asset downloading** - images and files to `assets/` subdirectory with proper markdown references

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
| `-d, --depth` | Maximum crawl depth (0 = unlimited, default: 1) |
| `--download-assets` | Download assets |

### Examples

```bash
uv run mdcrawler crawl https://example.com
uv run mdcrawler crawl https://example.com --max-pages 50
uv run mdcrawler crawl https://example.com -o ./my-mirror
uv run mdcrawler crawl https://example.com --download-assets
uv run mdcrawler crawl https://example.com --max-pages 100 --download-assets

# Crawl with depth control
uv run mdcrawler crawl https://example.com --depth 2
uv run mdcrawler crawl https://example.com --depth 0 --max-pages 100
```

### Image Assets

When `--download-assets` is enabled:
- All images from crawled pages are downloaded to `mirror/assets/`
- Image references in markdown are converted to local paths (e.g., `assets/image.jpg`)
- Images are properly referenced in the markdown output

### Single page conversion

```bash
uv run mdcrawler single-page https://example.com/page --output page.md
```

### Crawl depth explained

- `--depth 1` (default): Only crawl the starting page and its immediate links (1 level deep)
- `--depth 2`: Crawl 2 levels deep from the starting page
- `--depth 0`: Unlimited depth, crawl until max_pages is reached

**Note**: The default depth is `1`, which means only pages immediately linked from the starting page will be crawled. For books.toscrape.com with 50 pages of products, this means only the first page's 20 product links are followed. To crawl more pages, use `--depth 0` for unlimited depth or specify a higher depth value.

## Output

Each crawled page saved as markdown file:
- `index.md` for homepage
- Subpages as `path_to_page.md`

Internal links converted from `[text](url)` to `[text](page.md)`.

Assets downloaded to `assets/` subdirectory.

## License

MIT
