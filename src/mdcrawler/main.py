"""Main CLI entry point"""

import typer
from pathlib import Path
from typing import Optional

from mdcrawler.crawler.web_crawler import crawl_website, WebCrawler

app = typer.Typer(help="Website to Markdown Converter")


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Starting URL to crawl"),
    output: str = typer.Option("mirror", "-o", "--output", help="Output directory"),
    max_pages: int = typer.Option(10, "-m", "--max-pages", help="Maximum number of pages to crawl"),
    depth: int = typer.Option(1, "-d", "--depth", help="Maximum depth to crawl (0 = unlimited)"),
    download_assets: bool = typer.Option(False, "--download-assets", help="Download images and assets"),
    use_sitemap: bool = typer.Option(False, "--use-sitemap", help="Use sitemap.xml if available to discover URLs"),
):
    """Crawl a website and convert pages to markdown"""
    print(f"Starting crawl of {url}")
    print(f"Output directory: {output}")
    print(f"Maximum pages: {max_pages}")
    print(f"Crawl depth: {depth}")
    print(f"Download assets: {download_assets}")
    print(f"Use sitemap: {use_sitemap}")
    print()
    
    crawl_website(url, output_dir=output, max_pages=max_pages, depth=depth, download_assets=download_assets, use_sitemap=use_sitemap)


@app.command()
def single_page(
    url: str = typer.Argument(..., help="URL of the page to convert"),
    output: str = typer.Option("page.md", "-o", "--output", help="Output markdown file"),
):
    """Convert a single page to markdown"""
    crawler = WebCrawler(output_dir="tmp")
    try:
        markdown = crawler.crawl_page(url)
        if markdown:
            Path(output).write_text(markdown, encoding="utf-8")
            print(f"Saved to {output}")
    finally:
        crawler.close()


@app.command()
def version():
    """Show version information"""
    from mdcrawler import __version__
    print(f"MD Crawler version {__version__}")


if __name__ == "__main__":
    app()
