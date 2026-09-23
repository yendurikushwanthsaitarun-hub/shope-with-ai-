import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                from google.genai import types
                # Configure client with valid deadline (minimum allowed is 10s)
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(timeout=20000)
                )
            except Exception as e:
                logger.warning(f"Failed to initialize google.genai: {e}")

    def generate_chat_response(
        self,
        user_message: str,
        search_result: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes the search results, product catalog data, and user query into an engaging,
        accurate assistant response using Gemini 2.5 Flash, with a deterministic fallback.
        """
        tier = search_result.get("tier")
        status = search_result.get("status")
        products = search_result.get("products", [])
        target_product = search_result.get("target_product")
        similar_products = search_result.get("similar_products", [])
        searched_model = search_result.get("searched_model")
        searched_brand = search_result.get("searched_brand")

        # Specific rule for requested missing exact product (e.g. Redmi K51)
        if tier == "exact_model_not_found":
            brand = searched_brand or "this brand"
            target_cat = search_result.get("searched_category", "smartphones")
            default_reply = (
                f"Sorry, {searched_model} is not available in our current product database.\n\n"
                f"Would you like to see similar {brand} {target_cat}s?"
            )
            return {
                "reply": default_reply,
                "products": [],
                "similar_products": similar_products,
                "action_buttons": search_result.get("action_buttons", []),
                "prompt_question": search_result.get("prompt_question")
            }

        # If Gemini client is not configured or fails, provide high quality deterministic template
        if not self.client:
            return self._build_deterministic_reply(search_result, user_message)

        try:
            # Build prompt with catalog ground truth to prevent hallucination
            catalog_summary = []
            for p in products[:5]:
                specs_dict = dict(p.get("specs") or {})
                if not specs_dict:
                    for k in ["processor", "ram", "storage", "display", "battery", "camera", "material", "fit", "gender", "sizes", "color"]:
                        if p.get(k):
                            specs_dict[k] = p.get(k)

                catalog_summary.append({
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "brand": p.get("brand"),
                    "model": p.get("model"),
                    "category": p.get("category"),
                    "department": p.get("department", "electronics"),
                    "price": f"₹{p.get('price', 0):,}",
                    "rating": p.get("rating"),
                    "specs": specs_dict,
                    "features": p.get("features", []),
                    "pros": p.get("pros", []),
                    "cons": p.get("cons", []),
                    "use_cases": p.get("use_cases", [])
                })

            system_instruction = (
                "You are an expert, friendly AI Personal Shopping Assistant for Electronics, Techwear, Footwear & Lifestyle Fashion. "
                "CRITICAL RULES:\n"
                "1. Strictly use ONLY the provided product catalog information. Never invent fake products, models, prices, or specifications.\n"
                "2. If a specific product model requested by the user is missing from the database, do NOT substitute another product as if it was the requested one. "
                "Politely state that it is not available in our current product database and offer similar alternatives.\n"
                "3. When products are available, highlight key strengths, price in INR (₹), and who it is best suited for in clear, concise points.\n"
                "4. Keep your answer conversational, helpful, and under 150 words.\n"
                "5. Always be polite, warm, and objective."
            )

            prompt = (
                f"User Question: {user_message}\n\n"
                f"Search Context:\n"
                f"- Tier: {tier}\n"
                f"- Status: {status}\n"
                f"- Searched Brand: {searched_brand}\n"
                f"- Available Catalog Products:\n{json.dumps(catalog_summary, indent=2)}\n\n"
                f"Provide a helpful shopping assistant response tailored to the user."
            )

            # Try standard recommended models supported by current API
            chosen_model = 'gemini-3.6-flash'
            try:
                response = self.client.models.generate_content(
                    model=chosen_model,
                    contents=prompt,
                    config={
                        'system_instruction': system_instruction,
                        'temperature': 0.3
                    }
                )
            except Exception:
                # Fallback to gemini-3.5-flash
                response = self.client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=prompt,
                    config={
                        'system_instruction': system_instruction,
                        'temperature': 0.3
                    }
                )

            text_reply = response.text.strip()
            return {
                "reply": text_reply,
                "products": products,
                "target_product": target_product,
                "similar_products": similar_products,
                "action_buttons": search_result.get("action_buttons", [])
            }

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._build_deterministic_reply(search_result, user_message)

    def _build_deterministic_reply(self, search_result: Dict[str, Any], user_message: str) -> Dict[str, Any]:
        tier = search_result.get("tier")
        products = search_result.get("products", [])
        target = search_result.get("target_product")
        brand = search_result.get("detected_brand")
        cat = search_result.get("detected_category")

        if target:
            reply = (
                f"Here is the **{target.get('title')}** (₹{target.get('price', 0):,}).\n\n"
                f"⭐ Rating: {target.get('rating')}/5.0\n"
                f"✨ Key Highlights: {', '.join(target.get('features', [])[:3])}\n"
                f"👍 Best for: {', '.join(target.get('use_cases', [])[:3])}\n\n"
                f"Would you like to see detailed specifications or compare it with another model?"
            )
            return {
                "reply": reply,
                "products": [target],
                "target_product": target,
                "similar_products": search_result.get("similar_products", []),
                "action_buttons": [
                    {"label": f"Compare {target.get('model')}", "action": "compare", "product_id": target.get('id')},
                    {"label": "Show Similar Products", "action": "show_similar", "product_id": target.get('id')}
                ]
            }

        if products:
            reply = f"I found **{len(products)} options**"
            if brand:
                reply += f" from **{brand}**"
            if cat:
                reply += f" in **{cat.title()}s**"
            reply += ":\n\n"
            for p in products[:4]:
                reply += f"• **{p.get('title')}** — ₹{p.get('price', 0):,} ({p.get('rating')}⭐)\n"
            reply += "\nYou can select any item below to view full specifications, compare models, or filter further by budget!"

            return {
                "reply": reply,
                "products": products,
                "target_product": None,
                "similar_products": [],
                "action_buttons": [
                    {"label": "Filter by Price", "action": "filter_price"},
                    {"label": "Compare Top 2", "action": "compare_top", "ids": [p['id'] for p in products[:2]]}
                ]
            }

        return {
            "reply": search_result.get("message", "We couldn't find an exact match in our product catalog. Try searching for a specific brand like Samsung, Apple, HP, or a category like Laptops, Smartphones, or Headphones!"),
            "products": [],
            "target_product": None,
            "similar_products": search_result.get("similar_products", []),
            "action_buttons": search_result.get("action_buttons", [])
        }

gemini_service = GeminiService()
