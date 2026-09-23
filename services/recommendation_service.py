from typing import Dict, Any, List, Optional
from database.database import db

class RecommendationService:
    def __init__(self, database=None):
        self.db = database or db
        self.default_weights = {
            "category": 0.30,
            "budget": 0.25,
            "feature": 0.20,
            "rating": 0.15,
            "brand": 0.10
        }

    def recommend(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        max_budget: Optional[float] = None,
        min_budget: Optional[float] = None,
        target_features: Optional[List[str]] = None,
        use_case: Optional[str] = None,
        department: Optional[str] = None,
        weights: Optional[Dict[str, float]] = None,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        w = {**self.default_weights, **(weights or {})}
        all_products = self.db.get_all_products()

        # Hard filters: department, hard budget constraint
        candidates = all_products
        if department:
            candidates = [p for p in candidates if p.get('department', 'electronics').lower() == department.lower()]

        if max_budget is not None:
            candidates = [p for p in candidates if p.get('price', 0) <= max_budget]
        if min_budget is not None:
            candidates = [p for p in candidates if p.get('price', 0) >= min_budget]

        if not candidates:
            return []

        scored = []
        features_to_check = [f.lower().strip() for f in (target_features or [])]
        if use_case:
            features_to_check.append(use_case.lower().strip())

        for p in candidates:
            # 1. Category match score (0 to 1)
            cat_score = 0.0
            if category:
                p_cat = p.get('category', '').lower().rstrip('s')
                req_cat = category.lower().rstrip('s')
                if p_cat == req_cat:
                    cat_score = 1.0
            else:
                cat_score = 0.5  # Neutral if no category requested

            # 2. Budget match score (0 to 1)
            # Products that optimize the user's budget range without exceeding it
            budget_score = 0.5
            p_price = p.get('price', 0)
            if max_budget and max_budget > 0:
                # Higher score for getting close to budget ceiling while under budget (best value for money)
                ratio = p_price / max_budget
                if 0.5 <= ratio <= 1.0:
                    budget_score = 0.7 + (ratio * 0.3)
                elif ratio < 0.5:
                    budget_score = 0.5 + (ratio * 0.4)
                else:
                    budget_score = 0.0

            # 3. Feature match score (0 to 1)
            feature_score = 0.0
            if features_to_check:
                searchable = f"{' '.join(p.get('features', []))} {' '.join(p.get('use_cases', []))} {p.get('description', '')}".lower()
                matches = sum(1 for feat in features_to_check if feat in searchable)
                feature_score = min(1.0, matches / max(1, len(features_to_check)))
            else:
                feature_score = 0.5  # Neutral

            # 4. Rating score (0 to 1) - Normalized from 0-5 to 0-1
            p_rating = float(p.get('rating', 4.0))
            rating_score = min(1.0, max(0.0, p_rating / 5.0))

            # 5. Brand match score (0 to 1)
            brand_score = 0.0
            if brand:
                if p.get('brand', '').lower() == brand.lower():
                    brand_score = 1.0
            else:
                brand_score = 0.5  # Neutral

            # Total weighted composite score
            total_score = (
                (w['category'] * cat_score) +
                (w['budget'] * budget_score) +
                (w['feature'] * feature_score) +
                (w['rating'] * rating_score) +
                (w['brand'] * brand_score)
            )

            p_copy = dict(p)
            p_copy['_rec_score'] = round(total_score * 100, 1)
            scored.append((total_score, p_copy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

recommendation_service = RecommendationService()
