import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import time
import random
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, use_selenium: bool = False):
        self.use_selenium = use_selenium
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt"""
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch('*', url)
        except Exception as e:
            logger.warning(f"Could not check robots.txt: {e}")
            return True  # Allow scraping if robots.txt is not accessible
    
    def get_page_content(self, url: str) -> Optional[str]:
        """Get page content using requests or selenium"""
        if not self.check_robots_txt(url):
            raise Exception("Scraping not allowed by robots.txt")
        
        if self.use_selenium:
            return self._get_content_with_selenium(url)
        else:
            return self._get_content_with_requests(url)
    
    def _get_content_with_requests(self, url: str) -> Optional[str]:
        """Get page content using requests"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching content with requests: {e}")
            return None
    
    def _get_content_with_selenium(self, url: str) -> Optional[str]:
        """Get page content using selenium for dynamic content"""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Add random delay to avoid detection
            time.sleep(random.uniform(1, 3))
            
            return driver.page_source
        except Exception as e:
            logger.error(f"Error fetching content with selenium: {e}")
            return None
        finally:
            if driver:
                driver.quit()
    
    def parse_content(self, content: str, selectors: Dict[str, str]) -> Dict[str, List[str]]:
        """Parse content using BeautifulSoup and CSS selectors"""
        soup = BeautifulSoup(content, 'html.parser')
        results = {}
        
        for field_name, selector in selectors.items():
            try:
                elements = soup.select(selector)
                results[field_name] = [elem.get_text(strip=True) for elem in elements]
            except Exception as e:
                logger.error(f"Error parsing selector '{selector}': {e}")
                results[field_name] = []
        
        return results
    
    def scrape_url(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Main scraping method"""
        try:
            content = self.get_page_content(url)
            if not content:
                return {"error": "Could not fetch page content"}
            
            data = self.parse_content(content, selectors)
            
            # Add metadata
            data["_metadata"] = {
                "url": url,
                "timestamp": time.time(),
                "scraped_fields": list(selectors.keys())
            }
            
            return data
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {"error": str(e)}
