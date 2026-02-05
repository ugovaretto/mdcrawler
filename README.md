# MD Crawler v0.7.0

A web crawler that converts websites to markdown format, creating a local mirror with properly linked pages.

## Features

- **Headless browser crawling** using Selenium
- **Advanced markdown conversion** with Docling
- **Local link conversion** - internal links to local markdown paths
- **Domain restriction** - stays within target website
- **CLI interface** with Typer
- **Depth control** - crawl specific depth levels from starting URL
- **Asset downloading** - images and files to `assets/` subdirectory with proper markdown references
- **Sitemap parsing** - discover URLs from sitemap.xml for better crawl coverage

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
| `--use-sitemap` | Use sitemap.xml to discover URLs |

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

# Use sitemap.xml for discovery
uv run mdcrawler crawl https://example.com --use-sitemap
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

## Progress Summary

### Version 0.7.0
- Added `--use-sitemap` option to discover URLs from sitemap.xml files
- Implemented sitemap parsing for better crawl coverage
- Sitemap support is optional (default: disabled) for backward compatibility

### Version 0.6.0
- Fixed markdown link format issue where links had incorrect `_html_md.md` suffix
- Fixed `_replace_html_extensions` method that was causing double-conversion of paths
- Updated `_fix_local_links` to properly handle relative links by resolving them first
- Added call to `_fix_html_links` in conversion flow to handle HTML links from Docling
- Fixed `_fix_html_links` regex to handle multi-line content correctly
- Updated `_normalize_for_output` to only convert `/index.html` to `_index_html.md`
- Added `version` CLI command to show version information

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

### Version 0.2.1
- Fixed image download functionality
- Updated README with download-assets feature

### Version 0.2.0
- Implemented image and asset downloading functionality

### Version 0.1.0
- Initial implementation of web crawler
- HTML to markdown conversion using Docling

## License

MIT
