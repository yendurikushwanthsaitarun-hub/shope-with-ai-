import re
from typing import Dict, Any, List, Optional
from services.search_service import detect_brand, detect_category, extract_budget

class NLPService:
    INTENT_COMPARE = "COMPARE"
    INTENT_EXACT_PRODUCT = "EXACT_PRODUCT"
    INTENT_BRAND_SEARCH = "BRAND_SEARCH"
    INTENT_CATEGORY_SEARCH = "CATEGORY_SEARCH"
    INTENT_RECOMMENDATION = "RECOMMENDATION"
    INTENT_FILTER = "FILTER"
    INTENT_SIMILAR = "SHOW_SIMILAR"
    INTENT_GREETING = "GREETING"
    INTENT_HELP = "HELP"
    INTENT_GENERAL = "GENERAL"

    def analyze_intent(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        msg = message.strip()
        msg_low = msg.lower()

        # Check Greeting
        if re.match(r'^(hi|hello|hey|greetings|good morning|good evening|namaste|sup|yo)\b', msg_low):
            return {
                "intent": self.INTENT_GREETING,
                "confidence": 0.95,
                "entities": {}
            }

        # Check Help
        if re.search(r'\b(help|how does this work|what can you do|features|guide)\b', msg_low):
            return {
                "intent": self.INTENT_HELP,
                "confidence": 0.9,
                "entities": {}
            }

        # Check Show Similar
        if re.search(r'\b(similar|alternatives|show similar|like this|other options|related)\b', msg_low):
            return {
                "intent": self.INTENT_SIMILAR,
                "confidence": 0.9,
                "entities": {}
            }

        # Check Compare Intent
        # "compare X and Y", "X vs Y", "difference between X and Y"
        vs_match = re.search(r'(.+?)\s+(?:vs\.?|versus|compared to|against)\s+(.+)', msg_low)
        compare_match = re.search(r'(?:compare|comparison between)\s+(.+?)\s+(?:and|with)\s+(.+)', msg_low)

        if vs_match or compare_match:
            match = vs_match or compare_match
            prod1 = match.group(1).replace("compare", "").strip()
            prod2 = match.group(2).strip()
            return {
                "intent": self.INTENT_COMPARE,
                "confidence": 0.95,
                "entities": {
                    "item1": prod1,
                    "item2": prod2
                }
            }

        # Extract entities
        brand = detect_brand(msg)
        category = detect_category(msg)
        min_budget, max_budget = extract_budget(msg)

        # Recommendation intent
        # "recommend a laptop for coding", "best smartphone for photography", "which should i buy"
        if re.search(r'\b(recommend|suggestion|best|which|top rated|good for|advice)\b', msg_low):
            use_case = self._extract_use_case(msg_low)
            return {
                "intent": self.INTENT_RECOMMENDATION,
                "confidence": 0.85,
                "entities": {
                    "brand": brand,
                    "category": category,
                    "min_budget": min_budget,
                    "max_budget": max_budget,
                    "use_case": use_case
                }
            }

        # Check Filter follow-up
        if context and (min_budget is not None or max_budget is not None or (brand and not category)):
            if re.search(r'\b(only|show only|filter|within|just|under|cheaper|expensive)\b', msg_low):
                return {
                    "intent": self.INTENT_FILTER,
                    "confidence": 0.85,
                    "entities": {
                        "brand": brand,
                        "min_budget": min_budget,
                        "max_budget": max_budget
                    }
                }

        # Brand search
        # "I want Redmi", "Samsung phones", "HP laptops"
        if brand and not self._has_specific_model_number(msg_low):
            return {
                "intent": self.INTENT_BRAND_SEARCH,
                "confidence": 0.9,
                "entities": {
                    "brand": brand,
                    "category": category,
                    "min_budget": min_budget,
                    "max_budget": max_budget
                }
            }

        # Category search
        if category and not self._has_specific_model_number(msg_low):
            return {
                "intent": self.INTENT_CATEGORY_SEARCH,
                "confidence": 0.85,
                "entities": {
                    "brand": brand,
                    "category": category,
                    "min_budget": min_budget,
                    "max_budget": max_budget
                }
            }

        # Default to exact product inquiry
        return {
            "intent": self.INTENT_EXACT_PRODUCT,
            "confidence": 0.75,
            "entities": {
                "brand": brand,
                "category": category,
                "min_budget": min_budget,
                "max_budget": max_budget
            }
        }

    def _has_specific_model_number(self, text: str) -> bool:
        # Check if text contains digits or typical model designations (e.g. k51, s24, 15, m3, pro max, g7)
        return bool(re.search(r'\b(?:\w*\d+\w*|pro\s*max|ultra|plus|mini|air|elite)\b', text))

    def _extract_use_case(self, text: str) -> Optional[str]:
        use_cases = [
            "gaming", "photography", "camera", "battery", "coding", "programming",
            "student", "office", "travel", "video editing", "drawing", "vlog",
            "audiophile", "bass", "fitness", "running", "gym",
            "streetwear", "winter", "casual", "formal", "outdoor", "lifestyle",
            "sneakerhead", "marathon", "sleep tracking", "sleep"
        ]
        for uc in use_cases:
            if uc in text:
                return uc
        return None

nlp_service = NLPService()
