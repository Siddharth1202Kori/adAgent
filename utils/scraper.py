import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


def _clean_url(url: str) -> str:
    """Strip tracking parameters (gclid, utm_*, fbclid, etc.) from URLs."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    tracking_prefixes = ('utm_', 'gclid', 'gbraid', 'gad_', 'fbclid', 'dclid', 'msclkid')
    cleaned = {k: v for k, v in params.items() if not any(k.startswith(p) for p in tracking_prefixes)}
    cleaned_query = urlencode(cleaned, doseq=True)
    return urlunparse(parsed._replace(query=cleaned_query))


def scrape_landing_page(url: str) -> str:
    """
    Fetches and parses existing landing page HTML cleanly, converting DOM into actionable text chunks.
    Uses realistic browser headers to avoid bot detection.
    """
    url = _clean_url(url)

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()

        # Force UTF-8 decoding
        response.encoding = response.apparent_encoding or 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove non-content elements
        for tag in soup(['script', 'style', 'noscript', 'meta', 'link', 'svg', 'iframe']):
            tag.decompose()

        # Extract text with newlines
        text = soup.get_text(separator='\n')

        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        # Check for binary garbage — if more than 10% non-ASCII, the content is likely encoded
        if text:
            non_ascii = sum(1 for c in text[:1000] if ord(c) > 127)
            if non_ascii > 100:
                print(f"Warning: Scraped content from {url} appears to be binary/encoded ({non_ascii} non-ASCII chars in first 1000)")
                return ""

        if len(text) < 50:
            return ""

        # Truncate very long pages to avoid token limits
        if len(text) > 15000:
            text = text[:15000]

        return text
    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        return ""

def fetch_raw_html(url: str) -> str:
    """Fetches the raw, unparsed HTML of the landing page."""
    url = _clean_url(url)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text
    except Exception as e:
        print(f"Error fetching raw HTML for {url}: {str(e)}")
        return ""
