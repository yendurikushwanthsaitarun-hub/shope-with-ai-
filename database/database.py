import json
import os
import re
from typing import List, Dict, Any, Optional

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'products.json')
FALLBACK_DATA_PATH = '/data/products.json'

class ProductDatabase:
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or DATA_PATH
        if not os.path.exists(self.data_path) and os.path.exists(FALLBACK_DATA_PATH):
            self.data_path = FALLBACK_DATA_PATH
        self.products: List[Dict[str, Any]] = []
        self.load_data()

    def load_data(self) -> None:
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.products = json.load(f)
        else:
            self.products = []

    def get_all_products(self) -> List[Dict[str, Any]]:
        return self.products

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        for p in self.products:
            if p.get('id', '').lower() == product_id.lower():
                return p
        return None

    def get_brands(self, category: Optional[str] = None, department: Optional[str] = None) -> List[str]:
        brands = set()
        for p in self.products:
            if department and p.get('department', '').lower() != department.lower():
                continue
            if not category or p.get('category', '').lower() == category.lower():
                b = p.get('brand')
                if b:
                    brands.add(b)
        return sorted(list(brands))

    def get_categories(self, department: Optional[str] = None) -> List[str]:
        cats = set()
        for p in self.products:
            if department and p.get('department', '').lower() != department.lower():
                continue
            c = p.get('category')
            if c:
                cats.add(c)
        return sorted(list(cats))

    def filter_products(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        query: Optional[str] = None,
        use_case: Optional[str] = None,
        department: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        results = self.products

        if department:
            dep_norm = department.lower().strip()
            results = [p for p in results if p.get('department', 'electronics').lower() == dep_norm]

        if category:
            cat_norm = category.lower().rstrip('s')
            results = [p for p in results if p.get('category', '').lower().rstrip('s') == cat_norm]

        if brand:
            b_norm = brand.lower().strip()
            results = [p for p in results if p.get('brand', '').lower() == b_norm]

        if min_price is not None:
            results = [p for p in results if p.get('price', 0) >= min_price]

        if max_price is not None:
            results = [p for p in results if p.get('price', 0) <= max_price]

        if use_case:
            u_norm = use_case.lower().strip()
            results = [p for p in results if any(u_norm in uc.lower() for uc in p.get('use_cases', []))]

        if query:
            q_terms = [t.lower() for t in query.split() if len(t) > 1]
            scored = []
            for p in results:
                specs_text = ' '.join(str(v) for v in p.get('specs', {}).values())
                haystack = f"{p.get('title', '')} {p.get('brand', '')} {p.get('model', '')} {p.get('category', '')} {p.get('department', '')} {p.get('description', '')} {' '.join(p.get('features', []))} {specs_text}".lower()
                matches = sum(1 for term in q_terms if term in haystack)
                if matches > 0:
                    scored.append((matches, p))
            scored.sort(key=lambda x: x[0], reverse=True)
            results = [p for _, p in scored]

        return results

db = ProductDatabase()
