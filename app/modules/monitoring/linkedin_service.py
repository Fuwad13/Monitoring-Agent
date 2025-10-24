import hashlib
import json
import logging
import threading
import time
from typing import Dict, Optional

from linkedin_scraper import Company, Person, actions
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from app.core.config import settings

logger = logging.getLogger(__name__)


class LinkedInDriverManager:
    
    _instance = None
    _lock = threading.Lock()
    _driver: Optional[webdriver.Chrome] = None
    _authenticated = False
    _last_used = 0
    _timeout = 300
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_driver(self) -> webdriver.Chrome:
        with self._lock:
            current_time = time.time()
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    # Check if driver exists and is still valid
                    if self._driver is None or self._is_driver_stale():
                        logger.info(f"🚀 Creating new Chrome driver instance (attempt {attempt + 1})")
                        self._create_driver()
                    
                    # Check if we need to re-authenticate (timeout or new driver)
                    if not self._authenticated or (current_time - self._last_used) > self._timeout:
                        logger.info("🔐 Authenticating with LinkedIn")
                        self._authenticate()
                    
                    # Test that driver is working
                    self._driver.current_url
                    
                    self._last_used = current_time
                    return self._driver
                    
                except Exception as e:
                    logger.error(f"❌ Driver creation/auth failed (attempt {attempt + 1}): {e}")
                    if attempt < max_retries - 1:
                        logger.info("⏱️ Retrying driver creation...")
                        time.sleep(2)
                        continue
                    else:
                        logger.error("❌ All driver creation attempts failed")
                        raise
    
    def _create_driver(self):
        try:
            if self._driver:
                logger.info("🧹 Closing old driver instance")
                self._driver.quit()
        except Exception as e:
            logger.warning(f"⚠️ Error closing old driver: {e}")
        finally:
            self._driver = None
            self._authenticated = False
        
        try:
            service = ChromeService(executable_path=settings.CHROME_DRIVER_PATH)
            options = ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            self._driver = webdriver.Chrome(service=service, options=options)
            self._driver.implicitly_wait(10)
            self._authenticated = False
            logger.info("✅ Chrome driver created successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to create Chrome driver: {e}")
            self._driver = None
            self._authenticated = False
            raise
    
    def _authenticate(self):
        """Authenticate with LinkedIn"""
        try:
            actions.login(
                driver=self._driver,
                email=settings.LNKDIN_EMAIL,
                password=settings.LNKDIN_PASSWORD,
            )
            # self._driver.get("https://www.linkedin.com")
            # with open(settings.LNKDIN_COOKIES_PATH, "r") as f:
            #     cookies = json.load(f)
            
            # for cookie in cookies:
            #     if 'sameSite' in cookie and cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
            #         del cookie['sameSite']
                
            #     if 'expiry' in cookie:
            #         try:
            #             cookie['expiry'] = int(cookie['expiry'])
            #         except:
            #             del cookie['expiry']
                
            #     self._driver.add_cookie(cookie)

            # # Refresh the page to apply cookies
            # self._driver.refresh()
            self._authenticated = True
            logger.info("✅ LinkedIn authentication successful")
        except Exception as e:
            logger.error(f"❌ LinkedIn authentication failed: {e}")
            self._authenticated = False
            raise
    
    def _is_driver_stale(self) -> bool:
        if self._driver is None:
            return True
            
        try:
            self._driver.current_url
            self._driver.title
            return False
        except Exception as e:
            logger.warning(f"⚠️ Driver appears stale: {e}")
            return True
    
    def cleanup(self):
        with self._lock:
            if self._driver:
                try:
                    self._driver.quit()
                    logger.info("🧹 Driver cleanup completed")
                except Exception as e:
                    logger.warning(f"⚠️ Error during driver cleanup: {e}")
                finally:
                    self._driver = None
                    self._authenticated = False


class LinkedInService:

    def __init__(self):
        self.driver_manager = LinkedInDriverManager()
        logger.info("🔗 LinkedIn service initialized with managed driver")

    def scrape_profile(self, profile_url: str) -> Dict[str, str]:
        logger.info(f"👤 Scraping LinkedIn profile: {profile_url}")

        max_retries = 2
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Scraping attempt {attempt + 1} of {max_retries}")
                
                driver = self.driver_manager.get_driver()
                
                person = Person(profile_url, driver=driver, scrape=False)
                person.scrape()

                person_str = str(person)
                logger.info("✅ Profile scraped successfully")
                logger.info(f"📋 Raw person object: {person_str}")

                content_hash = self._hash_content(person_str)
                logger.info(f"🔑 Content hash: {content_hash}")

                return {
                    "title": f"LinkedIn Profile - {profile_url}",
                    "content": person_str,
                    "content_hash": content_hash,
                }

            except Exception as e:
                logger.error(f"❌ Scraping attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    logger.info("⏱️ Retrying profile scraping...")
                    self.driver_manager._driver = None
                    time.sleep(3)
                    continue
                else:
                    logger.error("❌ All scraping attempts failed")
                    return {
                        "error": f"LinkedIn profile scraping failed: {str(e)}",
                        "content": "",
                        "content_hash": "",
                    }

    def scrape_company(self, company_url: str) -> Dict[str, str]:
        logger.info(f"🏢 Scraping LinkedIn company: {company_url}")

        max_retries = 2
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Company scraping attempt {attempt + 1} of {max_retries}")
                
                # Get the managed driver instance
                driver = self.driver_manager.get_driver()
                
                # Create company with the managed driver
                company = Company(company_url, driver=driver)

                company_str = str(company)
                logger.info("✅ Company scraped successfully")
                logger.info(f"📋 Raw company object: {company_str}")

                content_hash = self._hash_content(company_str)
                logger.info(f"🔑 Content hash: {content_hash}")

                return {
                    "title": f"LinkedIn Company - {company_url}",
                    "content": company_str,
                    "content_hash": content_hash,
                }

            except Exception as e:
                logger.error(f"❌ Company scraping attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    logger.info("⏱️ Retrying company scraping...")
                    self.driver_manager._driver = None
                    time.sleep(3)
                    continue
                else:
                    logger.error("❌ All company scraping attempts failed")
                    return {
                        "error": f"LinkedIn company scraping failed: {str(e)}",
                        "content": "",
                        "content_hash": "",
                    }

    def _hash_content(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()
    
    def refresh_driver(self):
        logger.info("🔄 Force refreshing driver instance")
        self.driver_manager._driver = None
        self.driver_manager._authenticated = False
    
    def cleanup(self):
        logger.info("🧹 Cleaning up LinkedIn service resources")
        self.driver_manager.cleanup()
    
    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass
