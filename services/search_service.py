import re
from typing import Dict, Any, List, Optional, Tuple
from database.database import db

# Comprehensive brand normalization map (Electronics + Fashion & Lifestyle)
BRAND_MAP = {
    # Electronics Brands
    "apple": "Apple", "iphone": "Apple", "macbook": "Apple", "ipad": "Apple", "airpods": "Apple",
    "samsung": "Samsung", "galaxy": "Samsung",
    "oneplus": "OnePlus",
    "xiaomi": "Xiaomi", "mi": "Xiaomi",
    "redmi": "Redmi",
    "realme": "Realme",
    "vivo": "Vivo",
    "oppo": "Oppo",
    "motorola": "Motorola", "moto": "Motorola",
    "google": "Google Pixel", "google pixel": "Google Pixel", "pixel": "Google Pixel",
    "nothing": "Nothing",
    "iqoo": "iQOO",
    "poco": "Poco",
    "asus": "Asus", "asus rog": "Asus ROG", "rog": "Asus ROG",
    "sony": "Sony",
    "nokia": "Nokia",
    "infinix": "Infinix",
    "tecno": "Tecno",
    "hp": "HP",
    "dell": "Dell",
    "lenovo": "Lenovo", "lenovo legion": "Lenovo Legion", "legion": "Lenovo Legion",
    "acer": "Acer", "predator": "Acer",
    "msi": "MSI",
    "microsoft": "Microsoft", "surface": "Microsoft", "xbox": "Xbox",
    "razer": "Razer",
    "gigabyte": "Gigabyte",
    "jbl": "JBL",
    "bose": "Bose",
    "sennheiser": "Sennheiser",
    "boat": "Boat",
    "noise": "Noise",
    "skullcandy": "Skullcandy",
    "anker": "Anker", "soundcore": "Anker",
    "marshall": "Marshall",
    "garmin": "Garmin",
    "fitbit": "Fitbit",
    "amazfit": "Amazfit",
    "fire-boltt": "Fire-Boltt", "fireboltt": "Fire-Boltt",
    "canon": "Canon",
    "nikon": "Nikon",
    "fujifilm": "Fujifilm", "fuji": "Fujifilm",
    "panasonic": "Panasonic", "lumix": "Panasonic",
    "gopro": "GoPro",
    "dji": "DJI",
    "lg": "LG",
    "tcl": "TCL",
    "hisense": "Hisense",
    "benq": "BenQ",
    "playstation": "PlayStation", "ps5": "PlayStation", "ps4": "PlayStation", "sony playstation": "PlayStation",
    "nintendo": "Nintendo", "switch": "Nintendo",
    "valve": "Steam", "steam": "Steam", "steam deck": "Steam",
    "meta": "Meta", "quest": "Meta", "oculus": "Meta",
    "logitech": "Logitech",
    "keychron": "Keychron",
    "sandisk": "SanDisk",
    "wd": "WD", "western digital": "WD",
    "crucial": "Crucial", "micron": "Crucial",

    # Fashion, Footwear, Smart Rings & Luxury Brands
    "nike": "Nike", "air jordan": "Nike", "jordan": "Nike",
    "adidas": "Adidas", "ultraboost": "Adidas", "samba": "Adidas",
    "puma": "Puma",
    "new balance": "New Balance", "nb": "New Balance",
    "under armour": "Under Armour", "underarmour": "Under Armour",
    "converse": "Converse", "chuck taylor": "Converse",
    "the north face": "The North Face", "north face": "The North Face", "tnf": "The North Face",
    "levi's": "Levi's", "levis": "Levi's", "levi": "Levi's",
    "patagonia": "Patagonia",
    "lululemon": "Lululemon",
    "uniqlo": "Uniqlo",
    "zara": "Zara",
    "ray-ban": "Ray-Ban", "ray ban": "Ray-Ban", "rayban": "Ray-Ban",
    "oakley": "Oakley",
    "oura": "Oura", "oura ring": "Oura",
    "ultrahuman": "Ultrahuman",
    "peak design": "Peak Design",
    "nomatic": "Nomatic",
    "herschel": "Herschel",
    "casio": "Casio", "g-shock": "Casio", "gshock": "Casio",
    "seiko": "Seiko",
    "titan": "Titan",
    "tommy hilfiger": "Tommy Hilfiger", "tommy": "Tommy Hilfiger",
    "fossil": "Fossil"
}

# Category keywords mapping (Electronics + Fashion)
CATEGORY_MAP = {
    # Electronics Categories
    "smartphone": ["smartphone", "smartphones", "phone", "phones", "mobile", "mobiles", "cellphone"],
    "laptop": ["laptop", "laptops", "notebook", "notebooks", "ultrabook", "macbook"],
    "tablet": ["tablet", "tablets", "ipad", "ipads", "tab", "tabs"],
    "headphone": ["headphone", "headphones", "over-ear", "on-ear", "headset"],
    "earbuds": ["earbuds", "earbud", "tws", "airpods", "in-ear", "earphones", "buds"],
    "smartwatch": ["smartwatch", "smartwatches", "smart watch", "fitness band", "fitness tracker", "tracker"],
    "camera": ["camera", "cameras", "dslr", "mirrorless", "vlog camera", "action camera", "action cam", "drone", "drones"],
    "tv": ["tv", "tvs", "television", "televisions", "smart tv", "oled tv", "qled tv"],
    "monitor": ["monitor", "monitors", "display", "displays", "screen", "screens"],
    "gaming": ["gaming", "console", "consoles", "ps5", "xbox", "nintendo switch", "handheld", "vr headset", "vr"],
    "accessories": ["accessory", "accessories", "mouse", "mice", "keyboard", "keyboards", "power bank", "charger"],
    "storage": ["storage", "ssd", "hdd", "hard drive", "external drive", "pen drive", "flash drive", "nvme"],

    # Fashion & Lifestyle Categories
    "footwear": ["footwear", "shoes", "shoe", "sneaker", "sneakers", "running shoes", "kicks", "loafers", "boots"],
    "apparel": ["apparel", "clothing", "clothes", "jacket", "jackets", "puffer", "hoodie", "hoodies", "trouser", "trousers", "pants", "pant", "parka", "overcoat", "coat", "denim", "shirt", "wear"],
    "eyewear": ["eyewear", "sunglasses", "sunglass", "smart glasses", "shades", "glasses", "spectacles", "aviators"],
    "smart_rings": ["smart ring", "smart rings", "ring", "rings", "health ring", "fitness ring", "oura ring"],
    "bags": ["bag", "bags", "backpack", "backpacks", "travel pack", "rucksack", "briefcase", "laptop bag"],
    "watches": ["analog watch", "mechanical watch", "automatic watch", "chronograph", "luxury watch", "diver watch", "dress watch"]
}

def normalize_text(text: str) -> str:
    return re.sub(r'[^\w\s]', ' ', text).lower().strip()

def detect_brand(query: str) -> Optional[str]:
    q = query.lower()
    # Check multi-word brands first
    for key in sorted(BRAND_MAP.keys(), key=len, reverse=True):
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, q):
            return BRAND_MAP[key]
    return None

def detect_category(query: str) -> Optional[str]:
    q = query.lower()
    for cat, synonyms in CATEGORY_MAP.items():
        for syn in synonyms:
            pattern = r'\b' + re.escape(syn) + r'\b'
            if re.search(pattern, q):
                return cat
    return None

def extract_budget(query: str) -> Tuple[Optional[float], Optional[float]]:
    q = query.lower()
    min_budget = None
    max_budget = None

    # Range: e.g. "between 30000 and 50000", "30k to 50k", "30000-50000"
    range_match = re.search(r'(?:between|from)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?\s*(?:to|and|-)\s*(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?', q)
    if range_match:
        val1 = float(range_match.group(1))
        unit1 = range_match.group(2)
        if unit1 in ['k', 'thousand']: val1 *= 1000
        elif unit1 in ['lakh', 'lac']: val1 *= 100000

        val2 = float(range_match.group(3))
        unit2 = range_match.group(4)
        if unit2 in ['k', 'thousand']: val2 *= 1000
        elif unit2 in ['lakh', 'lac']: val2 *= 100000

        min_budget = min(val1, val2)
        max_budget = max(val1, val2)
        return min_budget, max_budget

    # Under / below / less than / up to / max
    max_match = re.search(r'(?:under|below|less than|within|up to|max(?:imum)?|budget of)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?', q)
    if max_match:
        val = float(max_match.group(1))
        unit = max_match.group(2)
        if unit in ['k', 'thousand']: val *= 1000
        elif unit in ['lakh', 'lac']: val *= 100000
        max_budget = val

    # Above / more than / over / min
    min_match = re.search(r'(?:above|more than|over|at least|min(?:imum)?)\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|lakh|lac)?', q)
    if min_match:
        val = float(min_match.group(1))
        unit = min_match.group(2)
        if unit in ['k', 'thousand']: val *= 1000
        elif unit in ['lakh', 'lac']: val *= 100000
        min_budget = val

    return min_budget, max_budget

class SearchService:
    def __init__(self, database=None):
        self.db = database or db

    def search(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes tiered search strategy:
        1. Exact Model Search
        2. Brand + Model Search
        3. Brand + Category Search
        4. Category + Keyword Search
        5. Similar Product Search (or prompt when exact model not found)
        6. No Result Response
        """
        raw_query = query.strip()
        clean_q = normalize_text(raw_query)

        detected_brand = detect_brand(raw_query)
        detected_category = detect_category(raw_query)
        min_price, max_price = extract_budget(raw_query)

        # Context inheritance if follow-up
        if context:
            if not detected_brand and context.get('brand'):
                detected_brand = context.get('brand')
            if not detected_category and context.get('category'):
                detected_category = context.get('category')
            if min_price is None and context.get('min_price'):
                min_price = context.get('min_price')
            if max_price is None and context.get('max_price'):
                max_price = context.get('max_price')

        all_products = self.db.get_all_products()

        # Step 1: Detect if user explicitly asked for a specific model name
        # Examples: "Redmi K51", "Galaxy S24 Ultra", "iPhone 15", "Sony WH-1000XM5"
        # We check if a specific model pattern was targeted
        model_query = self._extract_candidate_model(raw_query, detected_brand, detected_category)

        # TIER 1: EXACT MODEL SEARCH
        if model_query:
            exact_match = self._find_exact_model(model_query, detected_brand, all_products)
            if exact_match:
                return {
                    "tier": "exact_model",
                    "status": "found",
                    "query": raw_query,
                    "target_product": exact_match,
                    "products": [exact_match],
                    "similar_products": self.get_similar_products(exact_match, limit=4),
                    "message": f"Found exact match: {exact_match['title']}.",
                    "detected_brand": detected_brand or exact_match.get('brand'),
                    "detected_category": detected_category or exact_match.get('category')
                }
            elif detected_brand:
                # User asked for a specific brand + model that DOES NOT EXIST (e.g. "Redmi K51")
                # VERY IMPORTANT: As per requirement 2:
                # "DO NOT automatically replace an exact requested product with another product."
                # Reply: "Sorry, Redmi K51 is not available in our current product database."
                # Then provide: "Would you like to see similar Redmi smartphones?"
                # Buttons: [Show Similar Products], [Search Again]
                brand_prods = [p for p in all_products if p.get('brand', '').lower() == detected_brand.lower()]
                target_cat = detected_category or (brand_prods[0].get('category') if brand_prods else 'electronics')

                # Similar candidates from that brand
                similars = [p for p in brand_prods if not detected_category or p.get('category', '').lower() == detected_category.lower()][:4]
                if not similars:
                    similars = [p for p in all_products if p.get('category', '').lower() == target_cat.lower()][:4]

                # Format model display (e.g. "K51", "S24 Ultra")
                cand_clean = model_query.strip()
                if len(cand_clean) <= 4 and re.search(r'\d', cand_clean):
                    disp_model = cand_clean.upper()
                else:
                    disp_model = ' '.join(w.upper() if (len(w) <= 3 and re.search(r'\d', w)) else w.title() for w in cand_clean.split())

                formatted_searched = f"{detected_brand} {disp_model}".strip()

                return {
                    "tier": "exact_model_not_found",
                    "status": "not_found",
                    "query": raw_query,
                    "searched_model": formatted_searched,
                    "searched_brand": detected_brand,
                    "searched_category": target_cat,
                    "target_product": None,
                    "products": [],
                    "similar_products": similars,
                    "message": f"Sorry, {formatted_searched} is not available in our current product database.",
                    "prompt_question": f"Would you like to see similar {detected_brand} {target_cat}s?",
                    "action_buttons": [
                        {"label": "Show Similar Products", "action": "show_similar", "brand": detected_brand, "category": target_cat},
                        {"label": "Search Again", "action": "search_again"}
                    ]
                }

        # TIER 2: BRAND + MODEL SEARCH (Loose/Fuzzy search for model under brand)
        if detected_brand and model_query:
            brand_products = [p for p in all_products if p.get('brand', '').lower() == detected_brand.lower()]
            for p in brand_products:
                if model_query.lower() in p.get('model', '').lower() or model_query.lower() in p.get('title', '').lower():
                    return {
                        "tier": "brand_model",
                        "status": "found",
                        "query": raw_query,
                        "target_product": p,
                        "products": [p],
                        "similar_products": self.get_similar_products(p, limit=4),
                        "message": f"Found {p['title']}.",
                        "detected_brand": detected_brand,
                        "detected_category": p.get('category')
                    }

        # TIER 3: BRAND + CATEGORY SEARCH OR BRAND SEARCH
        # User says: "I want Redmi", "I want Samsung phones", "I want HP laptops"
        if detected_brand:
            matches = [p for p in all_products if p.get('brand', '').lower() == detected_brand.lower()]
            if detected_category:
                matches = [p for p in matches if p.get('category', '').lower().rstrip('s') == detected_category.lower().rstrip('s')]
            if min_price is not None:
                matches = [p for p in matches if p.get('price', 0) >= min_price]
            if max_price is not None:
                matches = [p for p in matches if p.get('price', 0) <= max_price]

            if matches:
                cat_label = f" {detected_category}s" if detected_category else " products"
                return {
                    "tier": "brand_category",
                    "status": "found",
                    "query": raw_query,
                    "products": matches,
                    "target_product": matches[0] if len(matches) == 1 else None,
                    "similar_products": [],
                    "message": f"Here are the {detected_brand}{cat_label} available in our catalog ({len(matches)} options).",
                    "detected_brand": detected_brand,
                    "detected_category": detected_category
                }

        # TIER 4: CATEGORY + KEYWORD SEARCH (Budget, specs, use cases)
        # e.g., "gaming laptops under 80000", "smartphones with 120hz display", "anc headphones"
        tier4_candidates = all_products
        if detected_category:
            tier4_candidates = [p for p in tier4_candidates if p.get('category', '').lower().rstrip('s') == detected_category.lower().rstrip('s')]
        if detected_brand:
            tier4_candidates = [p for p in tier4_candidates if p.get('brand', '').lower() == detected_brand.lower()]

        if min_price is not None:
            tier4_candidates = [p for p in tier4_candidates if p.get('price', 0) >= min_price]
        if max_price is not None:
            tier4_candidates = [p for p in tier4_candidates if p.get('price', 0) <= max_price]

        # Score by search terms
        stop_words = {
            'i', 'want', 'need', 'show', 'me', 'the', 'best', 'good', 'a', 'an', 'for', 'with', 'under', 'below',
            'in', 'to', 'of', 'and', 'or', 'tell', 'about', 'recommend', 'buy', 'price', 'rupees', 'rs', 'inr', 'k', 'thousand', 'lakh'
        }
        for cat_syns in CATEGORY_MAP.values():
            for syn in cat_syns:
                for token in syn.split():
                    stop_words.add(token.lower())
        if detected_brand:
            for token in detected_brand.lower().split():
                stop_words.add(token)

        q_tokens = [w for w in clean_q.split() if w not in stop_words and len(w) > 1 and not re.match(r'^\d+$', w)]

        scored_candidates = []
        for p in tier4_candidates:
            if not q_tokens:
                scored_candidates.append((1, p))
                continue

            searchable = f"{p.get('title', '')} {p.get('brand', '')} {p.get('model', '')} {p.get('description', '')} {' '.join(p.get('features', []))} {' '.join(p.get('use_cases', []))}".lower()
            score = 0
            for tok in q_tokens:
                if tok in p.get('model', '').lower():
                    score += 5
                elif tok in p.get('title', '').lower():
                    score += 4
                elif tok in p.get('brand', '').lower():
                    score += 3
                elif tok in searchable:
                    score += 1

            if score > 0:
                scored_candidates.append((score, p))

        scored_candidates.sort(key=lambda x: (x[0], x[1].get('rating', 0)), reverse=True)
        tier4_results = [p for _, p in scored_candidates]

        if tier4_results:
            msg = f"Found {len(tier4_results)} matching products"
            if detected_brand:
                msg += f" from {detected_brand}"
            if detected_category:
                msg += f" in {detected_category.title()}s"
            if max_price:
                msg += f" under ₹{int(max_price):,}"
            return {
                "tier": "category_keyword",
                "status": "found",
                "query": raw_query,
                "products": tier4_results,
                "target_product": tier4_results[0] if len(tier4_results) == 1 else None,
                "similar_products": [],
                "message": msg + ".",
                "detected_brand": detected_brand,
                "detected_category": detected_category
            }

        # If user explicitly specified a budget and NO products exist within that budget:
        # As per requirement 9: "Do not show ₹20,000 or ₹40,000 products. If no matching product exists:
        # 'Sorry, I couldn't find a Redmi phone under ₹10,000 in the current database.' Then offer: [Increase Budget] [Show Similar Products]"
        if max_price is not None:
            brand_label = f"{detected_brand} " if detected_brand else ""
            cat_label = f"{detected_category} " if detected_category else "product "
            if cat_label.endswith('s '):
                cat_label = cat_label[:-2] + " "
            # Similar products outside the budget offered only as opt-in suggestion
            similar_pool = [p for p in all_products if (detected_brand and p.get('brand', '').lower() == detected_brand.lower()) or (detected_category and p.get('category', '').lower().rstrip('s') == detected_category.lower().rstrip('s'))]
            similar_pool.sort(key=lambda x: x.get('price', 0))
            return {
                "tier": "budget_not_met",
                "status": "not_found",
                "query": raw_query,
                "products": [],
                "target_product": None,
                "similar_products": similar_pool[:4],
                "message": f"Sorry, I couldn't find a {brand_label}{cat_label}under ₹{int(max_price):,} in the current product database.",
                "prompt_question": f"Would you like to increase your budget or view similar products?",
                "action_buttons": [
                    {"label": "Increase Budget", "action": "increase_budget", "current_budget": max_price},
                    {"label": "Show Similar Products", "action": "show_similar_category", "category": detected_category or "electronics"}
                ],
                "detected_brand": detected_brand,
                "detected_category": detected_category
            }

        # TIER 5: SIMILAR PRODUCT SEARCH (Fallback if category is known and no budget was violated)
        if detected_category:
            fallback_category_prods = [p for p in all_products if p.get('category', '').lower().rstrip('s') == detected_category.lower().rstrip('s')]
            if fallback_category_prods:
                fallback_category_prods.sort(key=lambda x: x.get('rating', 0), reverse=True)
                return {
                    "tier": "similar_products",
                    "status": "partial_match",
                    "query": raw_query,
                    "products": fallback_category_prods[:6],
                    "target_product": None,
                    "similar_products": [],
                    "message": f"We couldn't find exact matches for your filters, but here are our top-rated {detected_category}s.",
                    "detected_brand": detected_brand,
                    "detected_category": detected_category
                }

        # TIER 6: NO RESULT RESPONSE
        return {
            "tier": "no_results",
            "status": "not_found",
            "query": raw_query,
            "products": [],
            "target_product": None,
            "similar_products": all_products[:4],
            "message": "We couldn't find any products matching your query in our current database.",
            "prompt_question": "Would you like to browse popular electronics categories or popular brands?",
            "action_buttons": [
                {"label": "Smartphones", "action": "browse_category", "category": "smartphone"},
                {"label": "Laptops", "action": "browse_category", "category": "laptop"},
                {"label": "Headphones", "action": "browse_category", "category": "headphone"},
                {"label": "Search Again", "action": "search_again"}
            ]
        }

    def _extract_candidate_model(self, raw_query: str, brand: Optional[str], category: Optional[str]) -> Optional[str]:
        """Isolates the candidate model part from user sentence."""
        q = raw_query.lower()
        # Remove common introductory and filler phrases
        prefixes = [
            "can you tell me about", "tell me about", "can you show me", "show only", "show me", "i want", "i need", "give me",
            "what about", "how is", "specs of", "price of", "details of", "information about",
            "do you have", "is there", "search for", "looking for", "find me", "buy"
        ]
        for p in sorted(prefixes, key=len, reverse=True):
            pattern = r'^\s*' + re.escape(p) + r'\b'
            q = re.sub(pattern, '', q).strip()

        # Remove brand name if present
        if brand:
            b_low = brand.lower()
            q = re.sub(r'\b' + re.escape(b_low) + r'\b', '', q).strip()

        # Remove category synonyms
        for cat_syns in CATEGORY_MAP.values():
            for syn in cat_syns:
                q = re.sub(r'\b' + re.escape(syn) + r'\b', '', q).strip()

        # Remove generic attribute words, budget words, and pronouns
        stopwords = [
            "noise cancelling", "noise cancellation", "anc", "wireless", "bluetooth",
            "gaming", "budget", "cheap", "best", "top", "good", "phone", "phones",
            "laptop", "laptops", "ones", "one", "please", "now", "only", "under", "below",
            "between", "from", "for", "with", "a", "an", "the", "in", "to", "of", "and",
            "specs", "spec", "specifications", "specification", "details", "price", "review", "reviews",
            "rupees", "rs", "inr", "thousand", "lakh"
        ]
        for sw in sorted(stopwords, key=len, reverse=True):
            q = re.sub(r'\b' + re.escape(sw) + r'\b', '', q, flags=re.IGNORECASE).strip()

        # Clean excess punctuation
        q = re.sub(r'[^\w\s\-\+]', '', q).strip()

        # Remove pure budget representations like "10k", "20k", "10000", "50000"
        q_no_budget = re.sub(r'\b\d+\s*k\b', '', q, flags=re.IGNORECASE).strip()
        q_no_budget = re.sub(r'^\d{4,7}$', '', q_no_budget).strip()
        if not q_no_budget:
            return None
        q = q_no_budget

        # Consider it a model candidate if it contains digits, explicit model naming words, or specific named models
        if q:
            # If it is only pure digits without letter prefixes/suffixes, it is not a model (unless paired with brand)
            if re.match(r'^\d+$', q) and not brand:
                return None

            has_digits = bool(re.search(r'\d+', q))
            has_model_word = bool(re.search(r'\b(ultra|pro|plus|max|mini|lite|fold|flip|fe|air|se|prime|edge|neo|samba|jordan|nuptse|wayfarer|mudmaster|diver|chrono|classic|runner|pilot)\b', q))
            # If brand is explicitly specified and user typed 2+ character word that isn't just generic
            if brand and len(q) >= 2 and q not in ['buy', 'show', 'all', 'any']:
                return q
            if has_digits or has_model_word:
                return q
        return None

    def _find_exact_model(self, model_candidate: str, brand: Optional[str], all_products: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        cand_norm = normalize_text(model_candidate)
        cand_compact = re.sub(r'\s+', '', cand_norm)

        # Sort products by model length descending so "Galaxy S24 Ultra" is checked before "Galaxy S24"
        sorted_products = sorted(all_products, key=lambda x: len(x.get('model', '')), reverse=True)

        for p in sorted_products:
            if brand and p.get('brand', '').lower() != brand.lower():
                continue

            p_model_norm = normalize_text(p.get('model', ''))
            p_model_compact = re.sub(r'\s+', '', p_model_norm)

            # Direct compact match (e.g. "s24ultra" == "s24ultra" or "k51" == "k51")
            if cand_compact == p_model_compact:
                return p

            # Match model candidate inside model with word boundary
            # e.g. "s24 ultra" in "galaxy s24 ultra"
            pattern = r'\b' + re.escape(cand_norm) + r'\b'
            if re.search(pattern, p_model_norm):
                return p

        return None

    def get_similar_products(self, product: Dict[str, Any], limit: int = 4) -> List[Dict[str, Any]]:
        category = product.get('category')
        brand = product.get('brand')
        price = product.get('price', 0)
        prod_id = product.get('id')

        all_products = self.db.get_all_products()
        candidates = [p for p in all_products if p.get('id') != prod_id]

        def similarity_score(p):
            score = 0
            if p.get('category') == category:
                score += 50
            if p.get('brand') == brand:
                score += 25
            p_price = p.get('price', 0)
            if price > 0 and p_price > 0:
                diff_ratio = abs(p_price - price) / price
                if diff_ratio < 0.2:
                    score += 30
                elif diff_ratio < 0.4:
                    score += 20
                elif diff_ratio < 0.6:
                    score += 10
            score += p.get('rating', 0) * 2
            return score

        candidates.sort(key=similarity_score, reverse=True)
        return candidates[:limit]

search_service = SearchService()
