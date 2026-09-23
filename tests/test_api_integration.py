import unittest
import json
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from services.gemini_service import gemini_service

class TestAPIIntegration(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_products(self):
        res = self.client.get('/api/products')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertGreaterEqual(data['count'], 100)

    def test_redmi_k51_chat(self):
        res = self.client.post('/api/chat', json={"message": "I want Redmi K51"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['tier'], 'exact_model_not_found')
        self.assertIn('Sorry, Redmi K51 is not available', data['reply'])
        self.assertGreater(len(data['similar_products']), 0)
        self.assertEqual(data['action_buttons'][0]['label'], 'Show Similar Products')

    @patch.object(gemini_service, 'client', None)
    def test_brand_search_redmi(self):
        res = self.client.post('/api/chat', json={"message": "I want Redmi"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'found')
        self.assertGreater(len(data['products']), 0)
        for p in data['products']:
            self.assertEqual(p['brand'], 'Redmi')

    @patch.object(gemini_service, 'client', None)
    def test_brand_category_samsung_phones(self):
        res = self.client.post('/api/chat', json={"message": "I want Samsung phones"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'found')
        self.assertGreater(len(data['products']), 0)
        for p in data['products']:
            self.assertEqual(p['brand'], 'Samsung')
            self.assertEqual(p['category'], 'smartphone')

    @patch.object(gemini_service, 'client', None)
    def test_brand_category_hp_laptops(self):
        res = self.client.post('/api/chat', json={"message": "I want HP laptops"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'found')
        self.assertGreater(len(data['products']), 0)
        for p in data['products']:
            self.assertEqual(p['brand'], 'HP')
            self.assertEqual(p['category'], 'laptop')

    def test_compare_endpoint(self):
        res = self.client.post('/api/compare', json={"product_ids": ["SP001", "SP003"]})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['count'], 2)

    def test_categories_and_brands(self):
        res_cat = self.client.get('/api/categories')
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn('smartphone', res_cat.get_json()['categories'])

        res_brands = self.client.get('/api/brands?category=laptop')
        self.assertEqual(res_brands.status_code, 200)
        brands = res_brands.get_json()['brands']
        self.assertIn('HP', brands)
        self.assertIn('Apple', brands)

if __name__ == '__main__':
    unittest.main()
