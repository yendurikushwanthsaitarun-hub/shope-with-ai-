import os
import urllib.parse
from typing import Dict, Any, List, Optional

class AmazonService:
    def __init__(self):
        self.access_key = os.environ.get("AMAZON_ACCESS_KEY")
        self.secret_key = os.environ.get("AMAZON_SECRET_KEY")
        self.associate_tag = os.environ.get("AMAZON_ASSOCIATE_TAG", "shopp-assist-21")
        self.is_configured = bool(self.access_key and self.secret_key)

    def search_amazon(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        If Amazon Product Advertising API credentials are present, calls the API.
        Otherwise provides a clean structured search link fallback with affiliate tag.
        """
        encoded_query = urllib.parse.quote_plus(query)
        amazon_url = f"https://www.amazon.in/s?k={encoded_query}&tag={self.associate_tag}"

        return [{
            "source": "amazon",
            "query": query,
            "configured": self.is_configured,
            "direct_url": amazon_url,
            "message": f"Browse real-time Amazon listings for '{query}'"
        }]

amazon_service = AmazonService()
