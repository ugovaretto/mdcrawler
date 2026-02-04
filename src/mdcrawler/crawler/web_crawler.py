"""Web crawler that converts websites to markdown"""

import re
import hashlib
import time
from pathlib import Path
from typing import Set, Dict, Optional
from io import BytesIO
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream


class WebCrawler:
    """Crawls a website and converts pages to markdown with local links"""
    
    def __init__(self, output_dir: str = "mirror"):
        self.output_dir = Path(output_dir)
        self.visited: Set[str] = set()
        self.url_to_path: Dict[str, str] = {}
        self.domain = ""
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=options)
        self.converter = DocumentConverter()
        
    def _make_safe_filename(self, url: str) -> str:
        """Convert URL to safe filename"""
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        if not path or path.endswith('/'):
            path = path + "index"
            
        if not path:
            path = "index"
            
        safe_path = re.sub(r'[^a-zA-Z0-9_\-]', '_', path)
        safe_path = re.sub(r'_+', '_', safe_path)
        
        if safe_path.startswith('_'):
            safe_path = safe_path[1:]
        if not safe_path:
            safe_path = "index"
            
        if parsed.query:
            query_hash = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
            safe_path = f"{safe_path}_{query_hash}"
            
        return f"{safe_path}.md"
    
    def _normalize_url(self, base_url: str, link: str) -> Optional[str]:
        """Normalize a link relative to base URL"""
        try:
            normalized = urljoin(base_url, link)
            parsed = urlparse(normalized)
            
            if parsed.scheme not in ('http', 'https'):
                return None
                
            if self.domain and parsed.netloc != self.domain:
                return None
                
            fragment_removed = normalized.split('#')[0]
            return fragment_removed
        except Exception:
            return None
    
    def _convert_to_markdown(self, html_content: str, url: str) -> str:
        """Convert HTML content to markdown using Docling"""
        try:
            stream = DocumentStream(name=url.split('/')[-1] or "index.html", stream=BytesIO(html_content.encode('utf-8')))
            result = self.converter.convert(stream)
            
            if result.document:
                markdown = result.document.export_to_markdown()
                if markdown:
                    return markdown
                    
            return html_content
            
        except Exception as e:
            print(f"Error converting {url}: {e}")
            return "# Error converting content\n\n[Original HTML content could not be parsed]"
    
    def _fix_local_links(self, markdown: str, base_url: str) -> str:
        """Fix markdown links to be local"""
        def replace_link(match):
            link_text = match.group(1)
            url = match.group(2)
            
            normalized = self._normalize_url(base_url, url)
            
            if normalized and normalized in self.url_to_path:
                local_path = self.url_to_path[normalized]
                return f"[{link_text}]({local_path})"
            elif normalized:
                filename = self._make_safe_filename(normalized)
                self.url_to_path[normalized] = filename
                return f"[{link_text}]({filename})"
            else:
                return match.group(0)
        
        return re.sub(r'\[([^\]]*)\]\(([^)]+)\)', replace_link, markdown)
    
    def crawl_page(self, url: str) -> Optional[str]:
        """Crawl a single page and return markdown"""
        if url in self.visited:
            return None
            
        self.visited.add(url)
        print(f"Crawling: {url}")
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            
            page_source = self.driver.page_source
            markdown = self._convert_to_markdown(page_source, url)
            
            filename = self._make_safe_filename(url)
            self.url_to_path[url] = filename
            
            md_path = self.output_dir / filename
            md_path.parent.mkdir(parents=True, exist_ok=True)
            
            markdown = self._fix_local_links(markdown, url)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# [{url}]({url})\n\n")
                f.write(f"**Source URL:** {url}\n\n")
                f.write("---\n\n")
                f.write(markdown)
                
            return markdown
            
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None
    
    def extract_links(self, url: str) -> Set[str]:
        """Extract all links from a page"""
        links = set()
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(1)
            
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            
            for elem in elements:
                try:
                    href = elem.get_attribute("href")
                    if href:
                        normalized = self._normalize_url(url, href)
                        if normalized:
                            links.add(normalized)
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"Error extracting links from {url}: {e}")
            
        return links
    
    def crawl(self, start_url: str, max_pages: int = 10):
        """Crawl website starting from start_url"""
        parsed = urlparse(start_url)
        self.domain = parsed.netloc
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        to_visit = [start_url]
        pages_crawled = 0
        
        while to_visit and pages_crawled < max_pages:
            url = to_visit.pop(0)
            
            if url in self.visited:
                continue
                
            self.crawl_page(url)
            pages_crawled += 1
            
            if pages_crawled >= max_pages:
                break
                
            new_links = self.extract_links(url)
            
            for link in new_links:
                if link not in self.visited and link not in to_visit:
                    to_visit.append(link)
                    
        print(f"\nCrawl complete!")
        print(f"Pages crawled: {pages_crawled}")
        print(f"Output directory: {self.output_dir}")
        
    def close(self):
        """Cleanup resources"""
        self.driver.quit()


def crawl_website(start_url: str, output_dir: str = "mirror", max_pages: int = 10):
    """ Convenience function to crawl a website """
    crawler = WebCrawler(output_dir)
    try:
        crawler.crawl(start_url, max_pages)
    finally:
        crawler.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m mdcrawler.crawler.web_crawler <url> [max_pages]")
        sys.exit(1)
        
    start_url = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    crawl_website(start_url, output_dir="mirror", max_pages=max_pages)
