"""
AI Shopping Assistant 
Powered by Google Gemini 2.5 Computer Use, Gemini 2.5 Flash Image (Nano Banana), and Veo 3.1

Usage:
  export GEMINI_API_KEY='your-key'
  export GOOGLE_CLOUD_PROJECT='your-project'  # Optional, for Veo only
  python app.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import traceback
from google import genai

from computer_use_helper import search_with_criteria, add_to_cart_and_checkout

try:
    from vto_generator import generate_multi_product_tryon
    VTO_AVAILABLE = True
except ImportError:
    VTO_AVAILABLE = False
    print("⚠️  VTO module not found - virtual try-on disabled")

try:
    from video_generator import generate_fashion_video_veo
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False
    print("⚠️  Video module not found - video generation disabled")

app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)
else:
    client = None
    print("⚠️  GEMINI_API_KEY not set")


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API status and configuration"""
    return jsonify({
        "status": "healthy",
        "api_key_set": bool(GEMINI_API_KEY),
        "project_set": bool(GOOGLE_CLOUD_PROJECT),
        "timestamp": time.time(),
        "features": {
            "search": bool(GEMINI_API_KEY),
            "tryon": bool(GEMINI_API_KEY and VTO_AVAILABLE),
            "video": bool(GEMINI_API_KEY and GOOGLE_CLOUD_PROJECT and VIDEO_AVAILABLE)
        }
    })


@app.route('/api/search', methods=['POST', 'OPTIONS'])
def search_products():
    """Basic product search endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        query = data.get('query') or data.get('prompt', '')
        
        if not query:
            return jsonify({"error": "Query required", "products": []}), 400
        
        print(f"\n🚀 Starting search for: '{query}'")
        
        products = search_with_criteria(
            criteria=[{"prompt": query}],
            max_turns=15,
            enable_query_refinement=True
        )
        
        return jsonify({
            "products": products,
            "count": len(products),
            "query": query,
            "store": "Amazon.fr"
        }), 200
        
    except Exception as e:
        print(f"\n❌ Search error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "products": []}), 500


@app.route('/api/advanced-search', methods=['POST', 'OPTIONS'])
def advanced_search():
    """Advanced product search with price and category filters"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        query = data.get('prompt') or data.get('query', '')
        max_price = data.get('max_price')
        category = data.get('category')
        
        if not query:
            return jsonify({"error": "Query required", "products": []}), 400
        
        enhanced_query = query
        if max_price:
            enhanced_query += f" under {max_price} euros"
        if category:
            enhanced_query += f" in {category}"
        
        print(f"\n🔍 Enhanced query: '{enhanced_query}'")
        
        products = search_with_criteria(
            criteria=[{"prompt": enhanced_query}],
            max_turns=15,
            enable_query_refinement=True
        )
        
        return jsonify({
            "products": products,
            "count": len(products),
            "query": enhanced_query,
            "original_query": query,
            "store": "Amazon.fr"
        }), 200
        
    except Exception as e:
        print(f"\n❌ Advanced search error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "products": []}), 500


@app.route('/api/checkout', methods=['POST', 'OPTIONS'])
def checkout():
    """Process checkout for selected items"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        items = data.get('items', [])
        user_info = data.get('user_info', {})
        
        if not items:
            return jsonify({"error": "No items"}), 400
        
        print(f"\n🛒 Processing checkout for {len(items)} items")
        result = add_to_cart_and_checkout(items, user_info)
        return jsonify(result), 200
        
    except Exception as e:
        print(f"❌ Checkout error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/tryon', methods=['POST', 'OPTIONS'])
def virtual_tryon():
    """
    Virtual try-on endpoint using Gemini 2.5 Flash Image (Nano Banana)
    
    Accepts a user photo and list of products, returns AI-generated
    image of the user wearing the selected items.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if not VTO_AVAILABLE:
            return jsonify({
                "error": "Try-on not available",
                "message": "Please ensure vto_generator.py is in the same directory",
                "success": False
            }), 500
        
        data = request.get_json()
        user_photo = data.get('user_photo')
        items = data.get('items', [])
        
        if not user_photo:
            return jsonify({"error": "Missing user_photo"}), 400
        
        if not items or len(items) == 0:
            return jsonify({"error": "No items provided"}), 400
        
        if not client:
            return jsonify({"error": "Gemini API key not configured"}), 500
        
        print(f"\n🎨 Generating virtual try-on for {len(items)} items")
        
        result_image = generate_multi_product_tryon(
            user_photo_base64=user_photo,
            products=items,
            gemini_client=client
        )
        
        return jsonify({
            "result_image": result_image,
            "items_count": len(items),
            "success": True,
            "message": "Virtual try-on generated with Gemini 2.5 Flash Image (Nano Banana)"
        }), 200
            
    except Exception as e:
        print(f"❌ Try-on error: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500


@app.route('/api/generate-video', methods=['POST', 'OPTIONS'])
def generate_video():
    """
    Veo 3 video generation from virtual try-on result
    
    Takes the virtual try-on result and creates a professional fashion
    showcase video with camera rotation.
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if not VIDEO_AVAILABLE:
            return jsonify({
                "error": "Video generation not available",
                "message": "Please ensure video_generator.py is in the same directory",
                "success": False
            }), 500
        
        data = request.get_json()
        tryon_result = data.get('user_photo')
        items = data.get('items', [])
        
        if not tryon_result or not items:
            return jsonify({
                "error": "Missing try-on result or items", 
                "success": False
            }), 400
        
        if not GOOGLE_CLOUD_PROJECT:
            return jsonify({
                "error": "GOOGLE_CLOUD_PROJECT environment variable not set",
                "message": "Please set: export GOOGLE_CLOUD_PROJECT='your-project-id'",
                "success": False
            }), 500
        
        print(f"\n🎬 Generating Veo 3 video from virtual try-on result")
        print(f"   Input: Try-on result with {len(items)} items")
        
        video_data_url = generate_fashion_video_veo(
            user_photo_base64=tryon_result,
            products=items,
            project_id=GOOGLE_CLOUD_PROJECT,
            location="us-central1"
        )
        
        return jsonify({
            "video_url": video_data_url,
            "success": True,
            "message": "Veo 3 video generated successfully",
            "items_count": len(items)
        }), 200
            
    except Exception as e:
        print(f"❌ Video generation error: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500


def print_startup_banner():
    """Print startup banner with configuration status"""
    print("\n" + "="*70)
    print("  🤖 AI Shopping Assistant")
    print("  Created by Wafae Bakkali")
    print("="*70)
    print()
    print("🌟 POWERED BY:")
    print("  • Google Gemini 2.5 Computer Use - Automated browsing")
    print("  • Gemini 2.5 Flash Image (Nano Banana) - Virtual try-on" + (" ✅" if VTO_AVAILABLE else " ❌"))
    print("  • Veo 3 - Video generation" + (" ✅" if VIDEO_AVAILABLE else " ❌"))
    print()
    print("🔑 CONFIGURATION:")
    
    if GEMINI_API_KEY:
        print("  ✅ GEMINI_API_KEY: Set")
    else:
        print("  ❌ GEMINI_API_KEY: NOT SET")
        print("     Export it: export GEMINI_API_KEY='your-key'")
    
    if GOOGLE_CLOUD_PROJECT:
        print(f"  ✅ GOOGLE_CLOUD_PROJECT: {GOOGLE_CLOUD_PROJECT}")
    else:
        print("  ⚠️  GOOGLE_CLOUD_PROJECT: NOT SET")
        print("     (Only needed for Veo video generation)")
    
    print()
    print("📦 DEPENDENCIES:")
    dependencies_ok = True
    
    try:
        import flask
        print("  ✅ flask")
    except ImportError:
        print("  ❌ flask - Run: pip install flask")
        dependencies_ok = False
    
    try:
        import flask_cors
        print("  ✅ flask-cors")
    except ImportError:
        print("  ❌ flask-cors - Run: pip install flask-cors")
        dependencies_ok = False
    
    try:
        from google import genai
        print("  ✅ google-genai")
    except ImportError:
        print("  ❌ google-genai - Run: pip install google-generativeai")
        dependencies_ok = False
    
    try:
        from playwright.sync_api import sync_playwright
        print("  ✅ playwright")
    except ImportError:
        print("  ❌ playwright - Run: pip install playwright && playwright install")
        dependencies_ok = False
    
    print()
    print("📚 OPTIONAL MODULES:")
    if VTO_AVAILABLE:
        print("  ✅ vto_generator.py")
    else:
        print("  ⚠️  vto_generator.py not found (virtual try-on disabled)")
    
    if VIDEO_AVAILABLE:
        print("  ✅ video_generator.py")
    else:
        print("  ⚠️  video_generator.py not found (video generation disabled)")
    
    print()
    
    if not dependencies_ok:
        print("⚠️  Some dependencies missing! Install them first.")
        print()
    
    print("="*70)
    print("🚀 Starting Flask server on http://localhost:5000")
    print("="*70 + "\n")


if __name__ == '__main__':
    print_startup_banner()
    
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    app.run(
        debug=debug_mode,
        host='0.0.0.0',
        port=5000,
        threaded=True
    )
