# MD Crawler - Project Overview

## Project Description

MD Crawler is a web crawling tool that creates a local markdown mirror of remote websites. The crawler converts HTML pages to markdown format while properly converting internal links to local markdown paths and downloading assets to maintain a self-contained local copy of the website.

## Technical Stack

### Core Technologies

- **Python 3.12+** - The primary programming language
- **uv** - Python package manager and virtual environment tool (used for ALL project management)
- **Selenium (headless)** - For rendering JavaScript and extracting HTML content
- **Docling** - For converting HTML to markdown with advanced formatting preservation

### Excluded Libraries
- No BeautifulSoup or other HTML parsing libraries
- No external scraping frameworks

### Build & Tooling (All via uv)

```bash
# Install dependencies
uv sync

# Run the crawler
uv run mdcrawler crawl <url>

# Run tests
uv run pytest

# Format code
uv run ruff format

# Lint code
uv run ruff check
```

## Project Structure

```
mdcrawler/
├── src/
│   └── mdcrawler/
│       ├── __init__.py
│       ├── main.py          # CLI entry point with Typer
│       └── crawler/
│           ├── __init__.py
│           └── web_crawler.py   # Main crawler logic
├── pyproject.toml           # uv project configuration
├── README.md
├── AGENTS.md                # This file - project documentation for agents
└── test-websites.md         # List of test websites for validation
```

## Key Features

### 1. Web Crawling
- **Headless browser crawling** using Selenium ChromeDriver
- **JavaScript rendering** for dynamic content
- **Domain restriction** to stay within target website
- **Depth control** - crawl specific levels deep from starting URL
- **Maximum page limit** - control how many pages to crawl

### 2. Markdown Conversion
- **HTML to Markdown** conversion using Docling
- **Image handling** - converts `<img>` tags to markdown syntax before conversion
- **Link conversion** - converts HTML anchor tags to markdown links
- **Proper path normalization** - `.html` paths converted to `.md`

### 3. Asset Management
- **Image downloading** to `assets/` subdirectory
- **URL-to-path mapping** - tracks original URLs to local paths
- **Local reference replacement** - image links point to local assets

### 4. Link Management
- **Internal link conversion** - converts remote links to local markdown paths
- **Path normalization** - handles various URL formats
- **Relative path support** - resolves relative links correctly
- **External link preservation** - keeps external links as-is

### 5. CLI Interface
Built with Typer for a user-friendly command-line interface:

```bash
uv run mdcrawler crawl <url> [options]
uv run mdcrawler single-page <url> [options]
```

## Usage

### Basic Crawl
```bash
uv run mdcrawler crawl https://books.toscrape.com
```

### With Options
```bash
# Specify output directory
uv run mdcrawler crawl https://example.com -o ./output

# Limit number of pages
uv run mdcrawler crawl https://example.com --max-pages 50

# Control crawl depth
uv run mdcrawler crawl https://example.com --depth 2

# Download assets
uv run mdcrawler crawl https://example.com --download-assets

# Unlimited depth with max pages
uv run mdcrawler crawl https://example.com --depth 0 --max-pages 100
```

### Single Page Conversion
```bash
uv run mdcrawler single-page https://example.com/page --output page.md
```

## Output Format

Each crawled page is saved as a markdown file with the following structure:

```markdown
# [Original URL](Original URL)

**Source URL:** Original URL

---

[Markdown content from Docling]
```

### Filename Generation
URLs are converted to safe filenames:
- `https://example.com/catalogue/book/index.html` → `catalogue_book_index_html.md`
- Paths are normalized: `/` → `_`, special chars → `_`
- Query strings get a hash suffix

### Asset Structure
```
output/
├── index.md
├── catalogue_book_index_html.md
└── assets/
    ├── image1.jpg
    ├── image2.png
    └── ...
```

## Progress Summary

### Version 0.7.0 (Current)
- Added `--use-sitemap` option to discover URLs from sitemap.xml files
- Implemented sitemap parsing to improve crawl coverage
- Sitemap support is optional (default: disabled) for backward compatibility
- Added `_parse_sitemap()` method to handle both regular sitemaps and sitemap indexes
- Added `_get_sitemap_url()` to automatically discover sitemap locations

### Version 0.6.0

### Version 0.5.0
- Fixed anchor tag conversion to markdown links before Docling processing
- Fixed duplicate link issue where both image+text and text-only links appeared
- Fixed regex pattern to correctly match markdown links with nested brackets
- Fixed image URLs incorrectly being converted to local paths when they should remain
- Updated all internal links to use local markdown paths

### Version 0.4.0
- Added `--depth` option for depth-based crawling
- Implemented depth tracking in the crawler
- Updated documentation with depth option

### Version 0.3.0
- Fixed import errors (Docling API changes)
- Implemented `_convert_img_tags_to_markdown()` for proper image handling
- Implemented `_download_images()` to track URL-to-local-path mappings
- Implemented `_replace_image_refs_in_markdown()` for local image references
- Updated `_fix_local_links()` to skip image references
- Tested with `https://books.toscrape.com`

### Version 0.4.0
- Added `--depth` option for depth-based crawling
- Implemented depth tracking in the crawler
- Updated documentation with depth option

### Version 0.3.0
- Fixed import errors (Docling API changes)
- Implemented `_convert_img_tags_to_markdown()` for proper image handling
- Implemented `_download_images()` to track URL-to-local-path mappings
- Implemented `_replace_image_refs_in_markdown()` for local image references
- Updated `_fix_local_links()` to skip image references
- Tested with `https://books.toscrape.com`

### Version 0.3.0
- Fixed import errors (Docling API changes)
- Implemented `_convert_img_tags_to_markdown()` for proper image handling
- Implemented `_download_images()` to track URL-to-local-path mappings
- Implemented `_replace_image_refs_in_markdown()` for local image references
- Updated `_fix_local_links()` to skip image references
- Tested with `https://books.toscrape.com`

### Version 0.2.1
- Fixed image download functionality
- Updated README with download-assets feature

### Version 0.2.0
- Implemented image and asset downloading functionality

### Version 0.1.0
- Initial implementation of web crawler
- HTML to markdown conversion using Docling

## Current State & Known Issues

### Working Features
- ✅ Headless Selenium crawling
- ✅ JavaScript rendering
- ✅ HTML to Markdown conversion via Docling
- ✅ Image downloading to assets directory
- ✅ Image references converted to local paths
- ✅ Depth-based crawling
- ✅ Max pages limit
- ✅ Domain restriction
- ✅ CLI with Typer
- ✅ Sitemap.xml parsing (opt-in via `--use-sitemap`)

### Known Issues / In Progress
- Links with both full URL and local path - **FIXED**: Links now properly converted to local paths
- Duplicate links appearing in output - **FIXED**: Regex pattern now correctly matches markdown links with nested brackets
- Docling may produce HTML links that need additional processing - **FIXED**: Anchor tags converted to markdown before Docling

### Fixed Issues (v0.4.0)
- Fixed regex pattern to correctly match markdown links with nested brackets (e.g., `[![alt](img_url)](link_url)`)
- Fixed duplicate link issue where both image link and text link appeared
- Fixed image URLs being incorrectly converted to local paths when they should remain as-is

### Test Status
- Tested successfully with `https://books.toscrape.com`
- 20+ pages crawled successfully
- Assets downloaded and properly referenced
- Depth crawling working correctly
- All links now correctly converted to local markdown paths

## Testing

### Test Websites
See `test-websites.md` for recommended test sites:
- **Books to Scrape** - Static e-commerce demo (primary test site)
- **Quotes to Scrape** - Dynamic content with pagination
- **Cyotek HTTP Crawler Test Site** - HTTP features testing
- **Scrape This Site** - Structured datasets
- **Web Scraper Test Sites** - Various layouts and dynamic loading

### Running Tests
```bash
uv run pytest
```

## Development

### Setting Up Development Environment
```bash
# Initialize project with uv
uv init

# Add dependencies
uv add docling selenium wget requests typer

# Install pre-commit hooks (if any)
uv run pre-commit install
```

### Code Quality
```bash
# Format with ruff
uv run ruff format

# Lint with ruff
uv run ruff check

# Type check with mypy (if configured)
uv run mypy src/
```

### Version Management
```bash
# Check current version
uv run mdcrawler version

# Update version (manually in pyproject.toml)
# Update version in src/mdcrawler/__init__.py
```

## Deployment

### Building Distribution
```bash
# Build wheel
uv build

# Install locally
uv pip install dist/mdcrawler-*.whl
```

### Publishing (if needed)
```bash
uv publish
```

## Configuration

### Project Settings (pyproject.toml)
```toml
[project]
name = "mdcrawler"
version = "0.7.0"
requires-python = ">=3.12"
dependencies = [
    "docling>=2.72.0",
    "selenium>=4.40.0",
    "wget>=3.2",
    "requests>=2.32.0",
]

[project.scripts]
mdcrawler = "mdcrawler.main:app"
```

## Future Enhancements

- [ ] Add support for JavaScript-based pagination
- [ ] Add retry logic for failed downloads
- [ ] Add progress indicator during crawling
- [ ] Add link validation after crawl
- [ ] Add support for compressed sitemap files (.xml.gz)

## Support & Maintenance

### Dependencies Management
All dependencies are managed via `uv`:
- View dependencies: `uv pip list`
- Update dependencies: `uv add <package>` or `uv remove <package>`
- Sync environment: `uv sync`

### Virtual Environment
The project uses uv's virtual environment management:
- Environment location: `.venv/` (managed by uv)
- No manual venv activation needed with `uv run`

## License

MIT
