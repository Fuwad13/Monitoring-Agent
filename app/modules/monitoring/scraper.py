import requests
from bs4 import BeautifulSoup
from typing import Dict
import hashlib
import logging
import os
from datetime import datetime
from .linkedin_service import LinkedInService

logger = logging.getLogger(__name__)


class ScraperService:

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        self.linkedin_service = None
    
    def _get_linkedin_service(self):
        if self.linkedin_service is None:
            logger.info("🔗 Initializing LinkedIn service")
            self.linkedin_service = LinkedInService()
        return self.linkedin_service

    def scrape_url(self, url: str, target_type: str) -> Dict[str, str]:
        logger.info(f"🌐 Starting scrape for URL: {url} (type: {target_type})")

        if target_type == "linkedin_profile":
            logger.info("🔗 Using LinkedIn service for profile scraping")
            return self._get_linkedin_service().scrape_profile(url)
        elif target_type == "linkedin_company":
            logger.info("🔗 Using LinkedIn service for company scraping")
            return self._get_linkedin_service().scrape_company(url)

        logger.info("🌐 Using regular HTTP scraping")
        return self._scrape_regular_website(url, target_type)

    def _scrape_regular_website(self, url: str, target_type: str) -> Dict[str, str]:
        try:
            logger.info(f"📡 Making HTTP request to {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            logger.info(
                f"✅ HTTP request successful - Status: {response.status_code}, Content-Length: {len(response.content)}"
            )

            html_preview = (
                response.text[:1000].replace("\n", "\\n").replace("\r", "\\r")
            )
            logger.debug(f"🔍 Raw HTML preview (first 1000 chars): {html_preview}")
            logger.debug(f"📄 Response headers: {dict(response.headers)}")
            logger.debug(f"🌐 Final URL after redirects: {response.url}")

            self._save_debug_html(url, response.text, target_type)

            parsers = ["lxml", "html.parser", "html5lib"]
            soup = None

            for parser in parsers:
                try:
                    logger.info(f"🔍 Trying parser: {parser}")
                    soup = BeautifulSoup(response.content, parser)
                    logger.info(f"✅ Successfully parsed with {parser}")
                    break
                except Exception as e:
                    logger.warning(f"⚠️  Parser {parser} failed: {e}")
                    continue

            if soup is None:
                logger.error("❌ All parsers failed")
                return {
                    "error": "Failed to parse HTML with any available parser",
                    "content": "",
                }

            return self._extract_website_content(soup)

        except Exception as e:
            logger.error(f"❌ Scraping failed: {str(e)}")
            return {"error": str(e), "content": ""}

    def _extract_website_content(self, soup: BeautifulSoup) -> Dict[str, str]:
        logger.info("🔍 Extracting generic website content")

        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        title = soup.find("title")
        title_text = title.get_text() if title else ""
        logger.info(f"📄 Page title: {title_text[:100]}...")

        # Get main content
        text = soup.get_text(separator=" ", strip=True)
        logger.info(f"📝 Extracted text length: {len(text)} characters")

        content_preview = text[:500].replace("\n", "\\n").replace("\r", "\\r")
        logger.debug(f"📋 Extracted text preview (first 500 chars): {content_preview}")

        logger.debug(f"🏷️  Found {len(soup.find_all('div'))} div elements")
        logger.debug(f"🏷️  Found {len(soup.find_all('h1'))} h1 elements")
        logger.debug(f"🏷️  Found {len(soup.find_all('h2'))} h2 elements")
        logger.debug(f"🏷️  Found {len(soup.find_all('p'))} paragraph elements")

        result = {
            "title": title_text,
            "content": text[:10000],
            "content_hash": self._hash_content(text),
        }
        logger.info(
            f"✅ Website content extraction completed - hash: {result['content_hash']}"
        )
        return result

    def _hash_content(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def _save_debug_html(self, url: str, html_content: str, target_type: str) -> None:
        try:
            if logger.isEnabledFor(logging.DEBUG):
                debug_dir = "debug_html"
                os.makedirs(debug_dir, exist_ok=True)

                safe_url = (
                    url.replace("://", "_")
                    .replace("/", "_")
                    .replace("?", "_")
                    .replace("&", "_")
                )
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = (
                    f"{debug_dir}/scraped_{target_type}_{safe_url}_{timestamp}.html"
                )

                with open(filename, "w", encoding="utf-8") as f:
                    f.write(html_content)

                logger.debug(f"💾 Debug HTML saved to: {filename}")
        except Exception as e:
            logger.warning(f"⚠️  Could not save debug HTML: {e}")
