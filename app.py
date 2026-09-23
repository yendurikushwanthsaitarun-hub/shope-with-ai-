import os
import sys
import re
import json
import uuid
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database.database import db
from services.search_service import search_service, detect_category, detect_brand, extract_budget
from services.nlp_service import nlp_service, NLPService
from services.gemini_service import gemini_service
from services.amazon_service import amazon_service
from services.recommendation_service import recommendation_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Session memory storage
SESSIONS = {}

def get_session(session_id: str) -> dict:
    if not session_id or session_id not in SESSIONS:
        new_id = session_id or str(uuid.uuid4())
        SESSIONS[new_id] = {
            "session_id": new_id,
            "category": None,
            "brand": None,
            "min_price": None,
            "max_price": None,
            "last_products": [],
            "selected_product": None,
            "history": []
        }
        return SESSIONS[new_id]
    return SESSIONS[session_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id') or str(uuid.uuid4())
        client_context = data.get('context') or {}

        if not user_message:
            return jsonify({
                "error": "Empty message",
                "reply": "How can I help you find products today?"
            }), 400

        session = get_session(session_id)
        msg_low = user_message.lower()

        # Merge client context into session
        if client_context.get('category'):
            session['category'] = client_context['category']
        if client_context.get('brand'):
            session['brand'] = client_context['brand']

        # --- TOPIC CHANGE DETECTION ---
        # "Actually I need a laptop", "Instead of phones show me headphones", "Actually I want shoes"
        if re.search(r'\b(actually|instead|rather|no wait|change topic|forget that|scratch that)\b', msg_low):
            new_cat = detect_category(user_message)
            new_brand = detect_brand(user_message)
            if new_cat:
                session['category'] = new_cat
                session['brand'] = new_brand
                session['selected_product'] = None
                session['min_price'] = None
                session['max_price'] = None

        # Step 1: NLP Intent & Entity recognition
        intent_data = nlp_service.analyze_intent(user_message, context=session)
        intent = intent_data.get('intent')
        entities = intent_data.get('entities', {})

        # Update session entities if extracted
        if entities.get('brand'):
            session['brand'] = entities['brand']
        if entities.get('category'):
            session['category'] = entities['category']
        if entities.get('min_budget') is not None:
            session['min_price'] = entities['min_budget']
        if entities.get('max_budget') is not None:
            session['max_price'] = entities['max_budget']

        # Handle Greeting
        if intent == NLPService.INTENT_GREETING:
            reply = (
                "Hello! I am your AI Personal Shopping Assistant for Electronics & Lifestyle Fashion. 📱💻🎧👟🧥\n\n"
                "I can help you discover, compare, and get specifications for smartphones, laptops, "
                "headphones, smartwatches, cameras, TVs, gaming gear, footwear, outerwear, and smart accessories.\n\n"
                "What are you looking for today?"
            )
            return jsonify({
                "session_id": session_id,
                "intent": intent,
                "reply": reply,
                "products": db.get_all_products()[:6],
                "action_buttons": [
                    {"label": "Best Laptops", "action": "browse_category", "category": "laptop"},
                    {"label": "Smartphones under ₹30,000", "action": "search_query", "query": "smartphones under 30000"},
                    {"label": "Trending Sneakers", "action": "browse_category", "category": "footwear"},
                    {"label": "ANC Headphones", "action": "search_query", "query": "noise cancelling headphones"}
                ]
            })

        # --- REFERENCE RESOLUTION: "the first one", "the second one", "compare the first two" ---
        last_prods = session.get('last_products', [])
        
        # Check "compare the first two" or "compare top 2"
        if re.search(r'\b(compare (?:the )?(?:first two|top 2|these two|both))\b', msg_low) and len(last_prods) >= 2:
            p1, p2 = last_prods[0], last_prods[1]
            return jsonify({
                "session_id": session_id,
                "intent": "COMPARE",
                "reply": f"Comparing **{p1['title']}** vs **{p2['title']}** side-by-side:",
                "products": [p1, p2],
                "comparison": True,
                "action_buttons": [
                    {"label": "Open Detailed Matrix", "action": "open_comparison_modal", "ids": [p1['id'], p2['id']]}
                ]
            })

        # Check ordinal reference: "the first one", "second", "third", "previous one"
        ordinal_idx = None
        if re.search(r'\b(?:the\s+)?first(?:\s+one|\s+product|\s+item|\s+phone|\s+laptop)?\b', msg_low):
            ordinal_idx = 0
        elif re.search(r'\b(?:the\s+)?second(?:\s+one|\s+product|\s+item|\s+phone|\s+laptop)?\b', msg_low):
            ordinal_idx = 1
        elif re.search(r'\b(?:the\s+)?third(?:\s+one|\s+product|\s+item|\s+phone|\s+laptop)?\b', msg_low):
            ordinal_idx = 2
        elif re.search(r'\b(?:the\s+)?fourth(?:\s+one|\s+product|\s+item|\s+phone|\s+laptop)?\b', msg_low):
            ordinal_idx = 3

        if ordinal_idx is not None and len(last_prods) > ordinal_idx:
            selected = last_prods[ordinal_idx]
            session['selected_product'] = selected
            similars = search_service.get_similar_products(selected, limit=3)
            reply = (
                f"You selected the **{selected['title']}** (₹{selected.get('price', 0):,}).\n\n"
                f"⭐ Rating: {selected.get('rating')}/5.0\n"
                f"📝 Description: {selected.get('description', '')}\n"
                f"✨ Key Highlights: {', '.join(selected.get('features', [])[:3])}\n\n"
                f"You can ask me about its specifications, pros & cons, or compare it with other models!"
            )
            return jsonify({
                "session_id": session_id,
                "intent": "SELECT_PRODUCT",
                "reply": reply,
                "target_product": selected,
                "products": [selected],
                "similar_products": similars,
                "action_buttons": [
                    {"label": "View Full Specs", "action": "open_details", "product_id": selected['id']},
                    {"label": "Show Cheaper Options", "action": "search_query", "query": f"cheaper than {selected['title']}"}
                ]
            })

        # --- CHEAPER ALTERNATIVES ---
        if re.search(r'\b(cheaper|cheaper options|cheaper alternative|lower price|budget friendly option)\b', msg_low):
            active = session.get('selected_product') or (last_prods[0] if last_prods else None)
            if active:
                current_price = active.get('price', 0)
                cat = active.get('category')
                brand = active.get('brand')
                all_candidates = db.get_all_products()
                cheaper = [
                    p for p in all_candidates
                    if p.get('id') != active.get('id')
                    and (p.get('category') == cat or p.get('brand') == brand)
                    and p.get('price', 0) < current_price
                ]
                cheaper.sort(key=lambda x: x.get('price', 0), reverse=True)
                if cheaper:
                    session['last_products'] = cheaper[:4]
                    return jsonify({
                        "session_id": session_id,
                        "intent": "CHEAPER_ALTERNATIVE",
                        "reply": f"Here are cheaper alternatives to **{active['title']}** (priced under ₹{current_price:,}):",
                        "products": cheaper[:4],
                        "similar_products": []
                    })

        # --- ATTRIBUTE INQUIRY ON SELECTED/CURRENT PRODUCT ---
        # "what is its RAM?", "what is its battery?", "is it good for gaming?"
        cur_prod = session.get('selected_product') or (last_prods[0] if len(last_prods) == 1 else None)
        if cur_prod and re.search(r'\b(its|it|the phone|the laptop|the shoe|the jacket|the watch|this product)\b', msg_low):
            specs = cur_prod.get('specs', {})
            # RAM
            if re.search(r'\b(ram|memory)\b', msg_low):
                ram_val = cur_prod.get('ram') or specs.get('ram') or specs.get('ram_storage') or "Not specified in product specs"
                return jsonify({
                    "session_id": session_id,
                    "reply": f"The **{cur_prod['title']}** has **{ram_val}**.",
                    "products": [cur_prod]
                })
            # Storage
            if re.search(r'\b(storage|rom|ssd|capacity)\b', msg_low):
                storage_val = cur_prod.get('storage') or specs.get('storage') or specs.get('ram_storage') or "Not specified in product specs"
                return jsonify({
                    "session_id": session_id,
                    "reply": f"The **{cur_prod['title']}** comes with **{storage_val}**.",
                    "products": [cur_prod]
                })
            # Battery
            if re.search(r'\b(battery|charging|battery life|mah)\b', msg_low):
                bat_val = cur_prod.get('battery') or specs.get('battery') or "Not specified in product specs"
                return jsonify({
                    "session_id": session_id,
                    "reply": f"The **{cur_prod['title']}** features **{bat_val}**.",
                    "products": [cur_prod]
                })
            # Processor / CPU
            if re.search(r'\b(processor|cpu|chipset|chip|gpu)\b', msg_low):
                proc_val = cur_prod.get('processor') or specs.get('processor') or "Not specified in product specs"
                return jsonify({
                    "session_id": session_id,
                    "reply": f"The **{cur_prod['title']}** is powered by **{proc_val}**.",
                    "products": [cur_prod]
                })
            # Material (Fashion)
            if re.search(r'\b(material|fabric|leather|cotton|textile)\b', msg_low):
                mat_val = specs.get('material') or "Not specified in product specs"
                return jsonify({
                    "session_id": session_id,
                    "reply": f"The **{cur_prod['title']}** is crafted with: **{mat_val}**.",
                    "products": [cur_prod]
                })
            # Good for gaming / college / running
            if re.search(r'\bgood for (\w+)\b', msg_low):
                m_uc = re.search(r'\bgood for (\w+)\b', msg_low).group(1)
                use_cases = [u.lower() for u in cur_prod.get('use_cases', [])]
                is_good = any(m_uc in u for u in use_cases)
                if is_good:
                    rep = f"Yes! The **{cur_prod['title']}** is well-suited for **{m_uc}**. Key strengths: {', '.join(cur_prod.get('pros', [])[:2])}."
                else:
                    rep = f"While the **{cur_prod['title']}** can handle general tasks, its primary designated use cases are: **{', '.join(cur_prod.get('use_cases', []))}**."
                return jsonify({
                    "session_id": session_id,
                    "reply": rep,
                    "products": [cur_prod]
                })

        # Handle Compare Intent
        if intent == NLPService.INTENT_COMPARE:
            item1_str = entities.get('item1', '')
            item2_str = entities.get('item2', '')

            # Search both products
            res1 = search_service.search(item1_str)
            res2 = search_service.search(item2_str)

            p1 = res1.get('target_product') or (res1.get('products')[0] if res1.get('products') else None)
            p2 = res2.get('target_product') or (res2.get('products')[0] if res2.get('products') else None)

            if p1 and p2:
                session['last_products'] = [p1, p2]
                return jsonify({
                    "session_id": session_id,
                    "intent": "COMPARE",
                    "reply": f"Comparing **{p1['title']}** vs **{p2['title']}**. Both products are loaded side-by-side in the comparison view below.",
                    "products": [p1, p2],
                    "comparison": True,
                    "action_buttons": [
                        {"label": "Open Detailed Matrix", "action": "open_comparison_modal", "ids": [p1['id'], p2['id']]}
                    ]
                })

        if intent == NLPService.INTENT_SIMILAR and session.get('last_products'):
            ref_product = session['last_products'][0]
            similars = search_service.get_similar_products(ref_product, limit=4)
            return jsonify({
                "session_id": session_id,
                "intent": "SHOW_SIMILAR",
                "reply": f"Here are products similar to **{ref_product['title']}** in price and features:",
                "products": similars,
                "similar_products": []
            })

        # Tiered Search Execution
        search_result = search_service.search(user_message, context=session)

        # Update session with search results
        if search_result.get('products'):
            session['last_products'] = search_result['products']
            if len(search_result['products']) == 1:
                session['selected_product'] = search_result['products'][0]
        if search_result.get('detected_brand'):
            session['brand'] = search_result['detected_brand']
        if search_result.get('detected_category'):
            session['category'] = search_result['detected_category']

        # Generate response with Gemini 2.5 Flash / Grounded Catalog Synthesis
        ai_response = gemini_service.generate_chat_response(
            user_message=user_message,
            search_result=search_result,
            conversation_history=session.get('history', []),
            context=session
        )

        # Update history
        session['history'].append({"role": "user", "text": user_message})
        session['history'].append({"role": "assistant", "text": ai_response.get('reply', '')})
        session['history'] = session['history'][-10:]

        return jsonify({
            "session_id": session_id,
            "intent": intent,
            "tier": search_result.get("tier"),
            "status": search_result.get("status"),
            "reply": ai_response.get("reply"),
            "products": ai_response.get("products", []),
            "target_product": ai_response.get("target_product"),
            "similar_products": ai_response.get("similar_products", []),
            "action_buttons": ai_response.get("action_buttons", []),
            "prompt_question": ai_response.get("prompt_question")
        })

    except Exception as e:
        logger.error(f"Error in /api/chat: {e}", exc_info=True)
        return jsonify({
            "error": str(e),
            "reply": "I encountered an error processing your request. Please try asking again!"
        }), 500

@app.route('/api/recommend', methods=['POST'])
def recommend_products():
    try:
        data = request.get_json() or {}
        category = data.get('category')
        brand = data.get('brand')
        max_budget = data.get('max_budget')
        min_budget = data.get('min_budget')
        target_features = data.get('features', [])
        use_case = data.get('use_case')
        department = data.get('department')
        weights = data.get('weights')
        limit = data.get('limit', 6)

        results = recommendation_service.recommend(
            category=category,
            brand=brand,
            max_budget=max_budget,
            min_budget=min_budget,
            target_features=target_features,
            use_case=use_case,
            department=department,
            weights=weights,
            limit=limit
        )
        return jsonify({
            "count": len(results),
            "products": results
        })
    except Exception as e:
        logger.error(f"Error in /api/recommend: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_products():
    query = request.args.get('q', '')
    category = request.args.get('category')
    brand = request.args.get('brand')
    department = request.args.get('department')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    results = db.filter_products(
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        query=query if query else None,
        department=department
    )

    return jsonify({
        "count": len(results),
        "products": results
    })

@app.route('/api/products', methods=['GET'])
def get_products():
    category = request.args.get('category')
    brand = request.args.get('brand')
    department = request.args.get('department')
    results = db.filter_products(category=category, brand=brand, department=department)
    return jsonify({
        "count": len(results),
        "products": results
    })

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = db.get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    similar = search_service.get_similar_products(product, limit=4)
    return jsonify({
        "product": product,
        "similar": similar
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    department = request.args.get('department')
    return jsonify({"categories": db.get_categories(department=department)})

@app.route('/api/brands', methods=['GET'])
def get_brands():
    category = request.args.get('category')
    department = request.args.get('department')
    return jsonify({"brands": db.get_brands(category=category, department=department)})

@app.route('/api/compare', methods=['POST'])
def compare_products():
    data = request.get_json() or {}
    product_ids = data.get('product_ids', [])
    if not product_ids:
        return jsonify({"error": "No product IDs provided"}), 400

    products = []
    for pid in product_ids:
        p = db.get_product_by_id(pid)
        if p:
            products.append(p)

    return jsonify({
        "count": len(products),
        "products": products
    })

@app.route('/api/similar/<product_id>', methods=['GET'])
def get_similar(product_id):
    product = db.get_product_by_id(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    similar = search_service.get_similar_products(product, limit=4)
    return jsonify({"similar": similar})

@app.route('/api/reset-session', methods=['POST'])
def reset_session():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    if session_id and session_id in SESSIONS:
        del SESSIONS[session_id]
    return jsonify({"status": "success", "message": "Session context reset"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
