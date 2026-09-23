import unittest
import json
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import db
from services.search_service import search_service, detect_brand, detect_category, extract_budget
from services.nlp_service import nlp_service, NLPService

class TestSearchAndAssistant(unittest.TestCase):
    def setUp(self):
        self.products = db.get_all_products()
        self.assertGreaterEqual(len(self.products), 100, "Database should contain 100+ products")

    def test_case_1_redmi_k51_missing_guard(self):
        """Test Case 1: 'I want Redmi K51' should politely say not found and suggest similar without hallucinating."""
        res = search_service.search("I want Redmi K51")
        self.assertEqual(res["tier"], "exact_model_not_found")
        self.assertEqual(res["status"], "not_found")
        self.assertIsNone(res["target_product"])
        self.assertIn("Sorry, Redmi K51 is not available", res["message"])
        self.assertEqual(res["searched_brand"], "Redmi")
        self.assertGreater(len(res["similar_products"]), 0)
        self.assertEqual(res["action_buttons"][0]["label"], "Show Similar Products")

    def test_case_2_brand_search_redmi(self):
        """Test Case 2: 'I want Redmi' should return Redmi products."""
        res = search_service.search("I want Redmi")
        self.assertEqual(res["status"], "found")
        self.assertEqual(res["detected_brand"], "Redmi")
        self.assertGreater(len(res["products"]), 0)
        for p in res["products"]:
            self.assertEqual(p["brand"], "Redmi")

    def test_case_3_brand_category_samsung_phones(self):
        """Test Case 3: 'I want Samsung phones' should return Samsung smartphones."""
        res = search_service.search("I want Samsung phones")
        self.assertEqual(res["status"], "found")
        self.assertEqual(res["detected_brand"], "Samsung")
        self.assertEqual(res["detected_category"], "smartphone")
        self.assertGreater(len(res["products"]), 0)
        for p in res["products"]:
            self.assertEqual(p["brand"], "Samsung")
            self.assertEqual(p["category"], "smartphone")

    def test_case_4_brand_category_hp_laptops(self):
        """Test Case 4: 'I want HP laptops' should return HP laptops."""
        res = search_service.search("I want HP laptops")
        self.assertEqual(res["status"], "found")
        self.assertEqual(res["detected_brand"], "HP")
        self.assertEqual(res["detected_category"], "laptop")
        self.assertGreater(len(res["products"]), 0)
        for p in res["products"]:
            self.assertEqual(p["brand"], "HP")
            self.assertEqual(p["category"], "laptop")

    def test_case_5_exact_model_galaxy_s24_ultra(self):
        """Test Case 5: Exact model search for 'Galaxy S24 Ultra'."""
        res = search_service.search("Tell me about Galaxy S24 Ultra")
        self.assertIn(res["tier"], ["exact_model", "brand_model"])
        self.assertIsNotNone(res["target_product"])
        self.assertEqual(res["target_product"]["model"], "Galaxy S24 Ultra")

    def test_case_6_exact_model_iphone_15_pro_max(self):
        """Test Case 6: Exact model search for 'iPhone 15 Pro Max'."""
        res = search_service.search("iPhone 15 Pro Max specs")
        self.assertIn(res["tier"], ["exact_model", "brand_model"])
        self.assertIsNotNone(res["target_product"])
        self.assertEqual(res["target_product"]["brand"], "Apple")

    def test_case_7_compare_nlp_intent(self):
        """Test Case 7: Intent recognition for compare query."""
        intent_res = nlp_service.analyze_intent("Compare Galaxy S24 Ultra and iPhone 15 Pro Max")
        self.assertEqual(intent_res["intent"], NLPService.INTENT_COMPARE)
        self.assertIn("Galaxy S24 Ultra", intent_res["entities"]["item1"].title())

    def test_case_8_budget_extraction(self):
        """Test Case 8: Budget range extraction."""
        min_p, max_p = extract_budget("smartphones under 30000")
        self.assertEqual(max_p, 30000.0)

        min_p, max_p = extract_budget("laptops between 50k and 80k")
        self.assertEqual(min_p, 50000.0)
        self.assertEqual(max_p, 80000.0)

    def test_case_9_category_budget_search(self):
        """Test Case 9: Category and budget search."""
        res = search_service.search("gaming laptops under 80000")
        self.assertEqual(res["status"], "found")
        self.assertGreater(len(res["products"]), 0)
        for p in res["products"]:
            self.assertEqual(p["category"], "laptop")
            self.assertLessEqual(p["price"], 80000)

    def test_case_10_headphones_anc(self):
        """Test Case 10: Headphones search with ANC keywords."""
        res = search_service.search("noise cancelling headphones")
        self.assertEqual(res["status"], "found")
        self.assertGreater(len(res["products"]), 0)
        for p in res["products"]:
            self.assertEqual(p["category"], "headphone")

    def test_case_11_context_followup(self):
        """Test Case 11: Context memory follow up."""
        context = {"category": "laptop", "brand": None}
        res = search_service.search("Show only Asus ones", context=context)
        self.assertEqual(res["status"], "found")
        self.assertEqual(res["detected_brand"], "Asus")
        for p in res["products"]:
            self.assertEqual(p["brand"], "Asus")
            self.assertEqual(p["category"], "laptop")

    def test_case_12_similar_products(self):
        """Test Case 12: Similar products generation."""
        p = db.get_product_by_id("SP001") # S24 Ultra
        similars = search_service.get_similar_products(p, limit=3)
        self.assertEqual(len(similars), 3)
        for sim in similars:
            self.assertNotEqual(sim["id"], "SP001")

if __name__ == '__main__':
    unittest.main()
