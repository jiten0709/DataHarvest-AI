import os
from dotenv import load_dotenv
load_dotenv('../.env')

from selenium.webdriver import Remote, ChromeOptions  
from selenium.webdriver.chromium.remote_connection import ChromiumRemoteConnection  
from bs4 import BeautifulSoup
from logging_config import scraper_logger
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
import time
from typing import Optional, List
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

SBR_WEBDRIVER = os.getenv("SBR_WEBDRIVER")

class WebScraper:
    def __init__(self):
        self.logger = scraper_logger
        
    def scrape_website(self, website_uri: str, timeout: int = 30) -> Optional[str]:
        """
        Scrape a website with enhanced error handling and logging
        """
        start_time = time.time()
        self.logger.info(f"Starting scrape for: {website_uri}")
        
        try:
            self.logger.info("Connecting to Browser API...")
            sbr_connection = ChromiumRemoteConnection(SBR_WEBDRIVER, 'goog', 'chrome')
            
            with Remote(sbr_connection, options=self._get_chrome_options()) as driver:
                self.logger.info("Connected successfully! Navigating to website...")
                
                # Set timeouts
                driver.set_page_load_timeout(timeout)
                driver.implicitly_wait(10)
                
                # Navigate to website
                driver.get(website_uri)
                
                # Handle captcha
                self._handle_captcha(driver)
                
                # Wait for page to load completely
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                self.logger.info("Page loaded successfully! Extracting content...")
                html_content = driver.page_source
                
                elapsed_time = time.time() - start_time
                self.logger.info(f"Scraping completed in {elapsed_time:.2f} seconds")
                self.logger.info(f"HTML content size: {len(html_content)} characters")
                
                return html_content
                
        except TimeoutException:
            self.logger.error(f"Timeout occurred while scraping {website_uri}")
            return None
        except WebDriverException as e:
            self.logger.error(f"WebDriver error: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during scraping: {str(e)}")
            return None
        
    def _get_chrome_options(self) -> ChromeOptions:
        """Configure Chrome options for optimal scraping"""
        options = ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        return options
    
    def _handle_captcha(self, driver) -> None:
        """Handle captcha detection and solving"""
        try:
            solve_captcha = driver.execute(
                'executeCdpCommand',
                {
                    'cmd': 'Captcha.waitForSolve',
                    'params': {'detectTimeout': 10000},
                }
            )
            status = solve_captcha.get('value', {}).get('status', 'unknown')
            self.logger.info(f"Captcha solve status: {status}")
        except Exception as e:
            self.logger.warning(f"Captcha handling failed: {str(e)}")

    def extract_body_content(self, html_content: str) -> str:
        """Extract body content from HTML with logging"""
        if not html_content:
            self.logger.warning("No HTML content provided")
            return ""
        
        try:
            self.logger.info("Extracting body content from HTML")
            soup = BeautifulSoup(html_content, 'html.parser')
            body_content = soup.body
            
            if body_content:
                result = str(body_content)
                self.logger.info(f"Body content extracted: {len(result)} characters")
                return result
            else:
                self.logger.warning("No body tag found in HTML")
                return ""
                
        except Exception as e:
            self.logger.error(f"Error extracting body content: {str(e)}")
            return ""
    
    def clean_body_content(self, body_content: str) -> str:
        """Clean body content by removing scripts, styles, and formatting text"""
        if not body_content:
            self.logger.warning("No body content provided for cleaning")
            return ""
        
        try:
            self.logger.info("Cleaning body content...")
            soup = BeautifulSoup(body_content, 'html.parser')

            # Remove script and style elements
            for script_or_style in soup(['script', 'style', 'noscript']):
                script_or_style.extract()

            # Get text content
            cleaned_content = soup.get_text(separator='\n')
            
            # Clean up whitespace
            cleaned_content = '\n'.join(
                line.strip() for line in cleaned_content.splitlines() if line.strip()
            )
            
            self.logger.info(f"Content cleaned: {len(cleaned_content)} characters")
            return cleaned_content
            
        except Exception as e:
            self.logger.error(f"Error cleaning content: {str(e)}")
            return ""
    
    def split_dom_content(self, dom_content: str, max_length: int = 6000) -> List[str]:
        """Split DOM content into chunks with logging"""
        if not dom_content:
            self.logger.warning("No DOM content provided for splitting")
            return []
        
        chunks = [
            dom_content[i:i + max_length] 
            for i in range(0, len(dom_content), max_length)
        ]
        
        self.logger.info(f"Content split into {len(chunks)} chunks of max {max_length} characters")
        return chunks

# Create instance for backward compatibility
scraper = WebScraper()
scrape_website = scraper.scrape_website
extract_body_content = scraper.extract_body_content
clean_body_content = scraper.clean_body_content
split_dom_content = scraper.split_dom_content