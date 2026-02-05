"""Web crawler that converts websites to markdown"""

import re
import hashlib
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Set, Dict, Optional, List
from io import BytesIO
from urllib.parse import urljoin, urlparse
from html.parser import HTMLParser

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.datamodel.pipeline_options import ConvertPipelineOptions, ThreadedPdfPipelineOptions


class ImageExtractor(HTMLParser):
    """Extract image URLs from HTML"""
    def __init__(self):
        super().__init__()
        self.images = []
    
    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            for name, value in attrs:
                if name == 'src':
                    self.images.append(value)


class WebCrawler:
    """Crawls a website and converts pages to markdown with local links"""
    
    def __init__(self, output_dir: str = "mirror", max_pages: int = 10, depth: int = 1, download_assets: bool = False, use_sitemap: bool = False):
        self.output_dir = Path(output_dir)
        self.visited: Set[str] = set()
        self.url_to_path: Dict[str, str] = {}
        self.domain = ""
        self.max_pages = max_pages
        self.depth = depth
        self.download_assets = download_assets
        self.use_sitemap = use_sitemap
        self.assets_dir = self.output_dir / "assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.image_map: Dict[str, str] = {}  # Maps original image URLs to local paths
        
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
    
    def _download_asset(self, asset_url: str) -> Optional[str]:
        """Download an asset and return local relative path"""
        if not self.download_assets:
            return asset_url
            
        try:
            parsed = urlparse(asset_url)
            asset_name = parsed.path.split('/')[-1] or "asset"
            
            if not asset_name:
                return None
                
            safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', asset_name)
            safe_name = re.sub(r'_+', '_', safe_name)
            
            asset_dir = self.assets_dir
            asset_dir.mkdir(parents=True, exist_ok=True)
            local_path = asset_dir / safe_name
            
            if not local_path.exists():
                response = requests.get(asset_url, timeout=10)
                response.raise_for_status()
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                    
            relative_path = local_path.relative_to(self.output_dir)
            return str(relative_path)
            
        except Exception as e:
            print(f"Error downloading {asset_url}: {e}")
            return asset_url
    
    def _normalize_url(self, base_url: str, link: str) -> Optional[str]:
        """Normalize a link relative to base URL, keeping .html extension for internal lookup"""
        try:
            normalized = urljoin(base_url, link)
            parsed = urlparse(normalized)
            
            if parsed.scheme not in ('http', 'https'):
                return None
                
            if self.domain and parsed.netloc != self.domain:
                return None
                
            fragment_removed = normalized.split('#')[0]
            # Keep .html for internal lookup - convert to .md later for output
            return fragment_removed
        except Exception:
            return None
    
    def _normalize_for_output(self, url: str) -> str:
        """Normalize URL for output - convert .html to .md and fix paths"""
        if not url:
            return url
        # Convert .html to .md
        if url.endswith('.html'):
            url = url[:-5] + '.md'
        # Convert /index.md to _index_html.md for consistency
        if url.endswith('/index.md'):
            url = url[:-9] + '_index_html.md'
        return url
    
    def _extract_image_urls(self, html_content: str) -> list:
        """Extract image URLs from HTML content"""
        extractor = ImageExtractor()
        extractor.feed(html_content)
        return extractor.images
    
    def _download_images(self, html_content: str, base_url: str) -> Dict[str, str]:
        """Download images from HTML content and return mapping to local paths"""
        image_urls = self._extract_image_urls(html_content)
        image_mapping = {}
        
        for img_url in image_urls:
            # Convert relative URL to absolute
            full_url = urljoin(base_url, img_url)
            
            # Download the image
            local_path = self._download_asset(full_url)
            
            if local_path and local_path != full_url:
                print(f"Downloaded: {full_url} -> {local_path}")
                image_mapping[full_url] = local_path
                
        return image_mapping
    
    def _replace_image_refs_in_markdown(self, markdown: str, image_mapping: Dict[str, str]) -> str:
        """Replace image URLs in markdown with local paths"""
        def replace_img(match):
            alt_text = match.group(1)
            img_url = match.group(2)
            
            # Parse the URL
            parsed = urlparse(img_url)
            img_filename = parsed.path.split('/')[-1]
            
            # Check if this image was downloaded (match by filename)
            for orig_url, local_path in image_mapping.items():
                if orig_url.endswith(img_filename):
                    return f"![{alt_text}]({local_path})"
            
            return match.group(0)
        
        # Match markdown image syntax: ![alt](url)
        return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_img, markdown)
    
    def _fix_local_links(self, markdown: str, base_url: str) -> str:
        """Fix markdown links to be local, excluding image-only references"""
        def replace_link(match):
            link_text = match.group(1)
            link_url = match.group(2)
            
            # Skip if this is an image reference
            if link_text.startswith('!'):
                return match.group(0)
            
            # For relative links, resolve them first then convert to safe filename
            if not link_url.startswith('http'):
                # Resolve relative URL to absolute
                resolved_url = urljoin(base_url, link_url)
                # Normalize and convert to safe filename
                normalized = self._normalize_url(base_url, resolved_url)
                if not normalized:
                    return match.group(0)
                
                if normalized in self.url_to_path:
                    local_path = self.url_to_path[normalized]
                    return f"[{link_text}]({local_path})"
                
                filename = self._make_safe_filename(normalized)
                self.url_to_path[normalized] = filename
                return f"[{link_text}]({filename})"
            
            # Normalize the URL
            normalized = self._normalize_url(base_url, link_url)
            
            if not normalized:
                return match.group(0)
            
            # Check if we have this URL in our mapping
            if normalized in self.url_to_path:
                local_path = self.url_to_path[normalized]
                return f"[{link_text}]({local_path})"
            
            # Generate the filename for this URL
            filename = self._make_safe_filename(normalized)
            self.url_to_path[normalized] = filename
            
            return f"[{link_text}]({filename})"
        
        # Match markdown links: [text](url)
        # Use a non-greedy pattern that handles nested brackets and stops at whitespace or end
        result = re.sub(r'\[([^\]]*(?:\][^\]]*)*?)\]\(([^)]+?)\)(?=\s|$)', replace_link, markdown)
        return result
    

    def _fix_html_links(self, markdown: str, base_url: str) -> str:
        """Fix HTML links in markdown output (Docling may produce HTML links)"""
        def replace_html_link(match):
            href = match.group(1)
            link_text = match.group(2)
            
            # Normalize the URL
            normalized = self._normalize_url(base_url, href)
            
            if not normalized:
                return match.group(0)
            
            # Check if we have this URL in our mapping
            if normalized in self.url_to_path:
                local_path = self.url_to_path[normalized]
                return f"[{link_text}]({local_path})"
            
            # Generate the filename for this URL
            filename = self._make_safe_filename(normalized)
            self.url_to_path[normalized] = filename
            
            return f"[{link_text}]({filename})"
        
        # Match HTML anchor links: <a href="url">text</a>
        # Use re.DOTALL to match multi-line content, and capture everything between tags as link text
        return re.sub(r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>', replace_html_link, markdown, flags=re.IGNORECASE | re.DOTALL)
    
    def _replace_html_extensions(self, markdown: str) -> str:
        """Replace .html paths with .md in markdown links"""
        # This method is no longer needed - links are properly converted by _fix_local_links
        # and _make_safe_filename which correctly convert to _html.md format
        # Keeping minimal implementation to avoid double-conversion
        return markdown
    
    def _convert_to_markdown(self, html_content: str, url: str) -> str:
        """Convert HTML content to markdown using Docling with referenced images"""
        try:
            # Pre-process HTML to convert img and anchor tags to markdown syntax
            processed_html = self._convert_img_tags_to_markdown(html_content, url)
            processed_html = self._convert_anchor_tags_to_markdown(processed_html, url)
            
            stream = DocumentStream(name=url.split('/')[-1] or "index.html", stream=BytesIO(processed_html.encode('utf-8')))
            result = self.converter.convert(stream)
            
            if result.document:
                # Export to markdown
                markdown = result.document.export_to_markdown()
                if markdown:
                    # Post-process to replace HTML links with markdown links
                    markdown = self._fix_html_links(markdown, url)
                    # Post-process to replace .html with .md in paths
                    markdown = self._replace_html_extensions(markdown)
                    return markdown
                    
            return html_content
            
        except Exception as e:
            print(f"Error converting {url}: {e}")
            return "# Error converting content\n\n[Original HTML content could not be parsed]"
    
    def _convert_img_tags_to_markdown(self, html_content: str, base_url: str) -> str:
        """Convert HTML img tags to markdown image syntax"""
        def replace_img_tag(match):
            img_tag = match.group(0)
            # Extract alt text
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag)
            alt_text = alt_match.group(1) if alt_match else "image"
            
            # Extract src
            src_match = re.search(r'src=["\']([^"\']*)["\']', img_tag)
            if src_match:
                img_src = src_match.group(1)
                full_url = urljoin(base_url, img_src)
                return f"![{alt_text}]({full_url})"
            
            return match.group(0)
        
        # Match img tags with src attribute
        return re.sub(r'<img[^>]*src=["\'][^"\']*["\'][^>]*>', replace_img_tag, html_content, flags=re.IGNORECASE)
    
    def _convert_anchor_tags_to_markdown(self, html_content: str, base_url: str) -> str:
        """Convert HTML anchor tags to markdown links"""
        def replace_anchor_tag(match):
            anchor_tag = match.group(0)
            # Extract text content (between opening and closing tags)
            text_match = re.search(r'>([^<]*)</a>', anchor_tag, re.IGNORECASE)
            link_text = text_match.group(1).strip() if text_match else "link"
            
            # Extract href
            href_match = re.search(r'href=["\']([^"\']*)["\']', anchor_tag)
            if href_match:
                href = href_match.group(1)
                full_url = urljoin(base_url, href)
                return f"[{link_text}]({full_url})"
            
            return match.group(0)
        
        # Match anchor tags with href attribute (including multi-line content)
        return re.sub(r'<a[^>]*href=["\'][^"\']*["\'][^>]*>.*?</a>', replace_anchor_tag, html_content, flags=re.IGNORECASE | re.DOTALL)
    
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
            
            # Download images and build mapping
            image_mapping = {}
            if self.download_assets:
                image_mapping = self._download_images(page_source, url)
            
            markdown = self._convert_to_markdown(page_source, url)
            
            # Replace image references in markdown with local paths
            if self.download_assets and image_mapping:
                markdown = self._replace_image_refs_in_markdown(markdown, image_mapping)
            
            filename = self._make_safe_filename(url)
            self.url_to_path[url] = filename
            
            md_path = self.output_dir / filename
            md_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Fix any remaining links to be local paths
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
    
    def _parse_sitemap(self, sitemap_url: str) -> List[str]:
        """Parse sitemap.xml or sitemap_index.xml and extract URLs"""
        urls = []
        
        try:
            response = requests.get(sitemap_url, timeout=10)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Check if it's a sitemap index
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Try namespace first, then without namespace
            sitemap_nodes = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap') or root.findall('.//sitemap')
            
            if sitemap_nodes:
                # It's a sitemap index - recursively parse each sitemap
                for sitemap in sitemap_nodes:
                    loc = sitemap.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc') or sitemap.find('.//loc')
                    if loc is not None and loc.text:
                        urls.extend(self._parse_sitemap(loc.text))
            else:
                # It's a regular sitemap - extract URLs
                url_nodes = root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url') or root.findall('.//url')
                
                for url_elem in url_nodes:
                    loc = url_elem.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc') or url_elem.find('.//loc')
                    if loc is not None and loc.text:
                        normalized = self._normalize_url(sitemap_url, loc.text)
                        if normalized:
                            urls.append(normalized)
            
        except Exception as e:
            print(f"Error parsing sitemap {sitemap_url}: {e}")
            
        return urls
    
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
    
    def _get_sitemap_url(self, start_url: str) -> Optional[str]:
        """Check for sitemap.xml and sitemap_index.xml at common locations"""
        parsed = urlparse(start_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        sitemap_locations = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemap_index.xml.gz",
        ]
        
        for sitemap_url in sitemap_locations:
            try:
                response = requests.head(sitemap_url, timeout=5)
                if response.status_code == 200:
                    print(f"Found sitemap: {sitemap_url}")
                    return sitemap_url
            except Exception:
                continue
                
        return None
    
    def crawl(self, start_url: str, max_pages: int = None):
        """Crawl website starting from start_url"""
        if max_pages is None:
            max_pages = self.max_pages
            
        parsed = urlparse(start_url)
        self.domain = parsed.netloc
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track depth for each URL: {url: depth_level}
        url_depths = {}
        to_visit: List[str] = []
        pages_crawled = 0
        
        # Optional: Use sitemap to get initial URLs
        if self.use_sitemap:
            sitemap_url = self._get_sitemap_url(start_url)
            if sitemap_url:
                sitemap_urls = self._parse_sitemap(sitemap_url)
                print(f"Discovered {len(sitemap_urls)} URLs from sitemap")
                
                # Add sitemap URLs to queue
                for url in sitemap_urls:
                    if url not in url_depths:
                        url_depths[url] = 0
                        to_visit.append(url)
        
        # Always add the start URL (even if using sitemap, for depth tracking)
        if start_url not in url_depths:
            url_depths[start_url] = 0
            to_visit.append(start_url)
        
        while to_visit and pages_crawled < max_pages:
            url = to_visit.pop(0)
            
            if url in self.visited:
                continue
                
            # Check depth limit (0 = unlimited)
            current_depth = url_depths.get(url, 0)
            if self.depth > 0 and current_depth >= self.depth:
                continue
                
            self.crawl_page(url)
            pages_crawled += 1
            
            if pages_crawled >= max_pages:
                break
                
            new_links = self.extract_links(url)
            
            for link in new_links:
                if link not in self.visited and link not in to_visit:
                    to_visit.append(link)
                    url_depths[link] = current_depth + 1
                    
        print(f"\nCrawl complete!")
        print(f"Pages crawled: {pages_crawled}")
        print(f"Output directory: {self.output_dir}")
        
    def close(self):
        """Cleanup resources"""
        self.driver.quit()


def crawl_website(start_url: str, output_dir: str = "mirror", max_pages: int = 10, depth: int = 1, download_assets: bool = False, use_sitemap: bool = False):
    """ Convenience function to crawl a website """
    crawler = WebCrawler(output_dir, max_pages=max_pages, depth=depth, download_assets=download_assets, use_sitemap=use_sitemap)
    try:
        crawler.crawl(start_url)
    finally:
        crawler.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m mdcrawler.crawler.web_crawler <url> [max_pages] [depth]")
        sys.exit(1)
        
    start_url = sys.argv[1]
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    depth = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    crawl_website(start_url, output_dir="mirror", max_pages=max_pages, depth=depth)
