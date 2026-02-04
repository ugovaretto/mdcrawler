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
):
    """Crawl a website and convert pages to markdown"""
    print(f"Starting crawl of {url}")
    print(f"Output directory: {output}")
    print(f"Maximum pages: {max_pages}")
    print()
    
    crawl_website(url, output_dir=output, max_pages=max_pages)


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


if __name__ == "__main__":
    app()
