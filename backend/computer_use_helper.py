"""
Gemini Computer Use Helper - Automated Product Search
Uses Gemini 2.5 Computer Use with Playwright to automate websites browsing
"""

from playwright.sync_api import sync_playwright
from google import genai
from google.genai import types
from google.genai.types import Content, Part
import time
import re
import os

# Good viewport size with zoom out
W, H = 1600, 900
MODEL = "gemini-2.5-computer-use-preview-10-2025"

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not set")
client = genai.Client(api_key=API_KEY)


def print_status(message, style="info"):
    """Print formatted status messages with icons"""
    icons = {
        "header": "🚀",
        "info": "ℹ️ ",
        "success": "✅",
        "thinking": "💭",
        "action": "🎯",
        "error": "❌",
    }
    print(f"{icons.get(style, '  ')} {message}")


def detect_and_split_outfit(user_query):
    """
    Detect if query is for a complete outfit and break it down into items.
    Returns list of 3-4 items including shoes, or None if not an outfit query.
    """
    if not re.search(r'\boutfit\b', user_query, re.IGNORECASE):
        return None
    
    print_status("💭 I see you want a complete outfit! Let me break this down into key pieces...", "thinking")
    
    outfit_prompt = f"""The user wants an outfit. Break this down into 3-4 MAIN clothing items.

User request: "{user_query}"

CRITICAL RULES:
- Output EXACTLY 3-4 items (including shoes!)
- ALWAYS include shoes as the last item
- Match formality to context:
  * Formal/Interview/Business: Use "dress shirt", "dress pants", "blazer", "oxford shoes"
  * Casual: Use "t-shirt", "jeans", "sneakers", "polo"
  * Smart casual: Use "button shirt", "chinos", "loafers"
- NO accessories (belts, ties, scarves, bags, jewelry)
- Be specific and searchable
- Include gender when relevant
- Separate items with " | "

GOOD Examples:
- "outfit for job interview men" → "blazer men | dress shirt men | dress pants men | oxford shoes men"
- "casual summer outfit men" → "t-shirt men | shorts men | sneakers men"
- "business casual outfit" → "button shirt men | chinos men | loafers men"
- "party outfit women" → "blouse women | jeans women | heels women"

BAD Examples:
- "dress shirt | dress pants | dress shoes" for casual context ❌
- Only 2 items ❌
- No shoes ❌

Items (separated by |):"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=outfit_prompt
        )
        
        items_text = response.text.strip()
        items = [item.strip() for item in items_text.split('|')]
        items = items[:4]
        
        if len(items) < 3:
            return None
        
        print(f"   ✨ Perfect! I'll search for: {', '.join(items)}\n")
        return items
        
    except Exception:
        print(f"   ⚠️  I'll use your original query instead")
        return None


def refine_search_query(user_query):
    """Refine natural language query into concise search terms"""
    print(f"   💭 Let me make this more search-friendly...")
    
    refinement_prompt = f"""Convert to short search query (3-6 words):

"{user_query}"

Examples:
- "I need a black jacket for men" → "black jacket men"
- "Looking for wireless headphones" → "wireless headphones"

Query:"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=refinement_prompt
        )
        
        refined = response.text.strip().strip('"').strip("'")
        print(f"   ✨ I refined it to: '{refined}'\n")
        return refined
        
    except Exception:
        return user_query


def denorm(v: int, size: int) -> int:
    """Convert normalized coordinate (0-1000) to pixel coordinate"""
    return int(v / 1000 * size)


def execute_actions(candidate, page, viewport=(W, H), show_narration=False):
    """
    Execute computer use actions from Gemini response.
    Returns results, function calls, and parts for creating responses.
    """
    width, height = viewport
    results = []
    function_calls = []
    parts_with_fc = []
    
    for part in candidate.content.parts:
        fc = getattr(part, "function_call", None)
        if not fc:
            continue
        
        function_calls.append(fc)
        parts_with_fc.append(part)
        name = fc.name
        args = fc.args or {}
        
        if show_narration:
            if name == 'navigate':
                print(f"      🌐 I'm navigating to Amazon...")
            elif name == 'click_at':
                print(f"      👆 I'm clicking on an element...")
            elif name == 'type_text_at':
                text = args.get('text', '')
                print(f"      ⌨️  I'm typing: '{text}'")
            elif name == 'scroll_document':
                print(f"      📜 I'm scrolling to see more products...")
            elif name == 'wait_5_seconds':
                print(f"      ⏳ I'm waiting for the page to load...")
        
        try:
            # Bring page to front for visibility
            try:
                page.bring_to_front()
            except Exception:
                pass
                
            if name == "open_web_browser":
                pass
                
            elif name == "navigate":
                url = args.get("url", "")
                page.goto(url, timeout=30000)
                time.sleep(0.3)
                
            elif name == "search":
                page.goto("https://www.google.com", timeout=30000)
                time.sleep(0.3)
                
            elif name == "click_at":
                x = denorm(args["x"], width)
                y = denorm(args["y"], height)
                page.mouse.click(x, y)
                time.sleep(0.4)
                
            elif name == "hover_at":
                x = denorm(args["x"], width)
                y = denorm(args["y"], height)
                page.mouse.move(x, y)
                time.sleep(0.2)
                
            elif name == "type_text_at":
                x = denorm(args["x"], width)
                y = denorm(args["y"], height)
                text = args.get("text", "")
                press_enter = args.get("press_enter", True)
                clear_before = args.get("clear_before_typing", True)
                
                page.mouse.click(x, y)
                time.sleep(0.3)
                
                if clear_before:
                    page.keyboard.press("Control+A")
                    time.sleep(0.1)
                    page.keyboard.press("Backspace")
                    time.sleep(0.2)
                
                # Type character by character for visibility
                for char in text:
                    page.keyboard.press(char)
                    time.sleep(0.08)
                
                if press_enter:
                    time.sleep(0.4)
                    page.keyboard.press("Enter")
                    time.sleep(0.5)
                    
            elif name == "scroll_document":
                direction = args.get("direction", "down")
                # Smooth scroll for visibility
                total_delta = 800 if direction == "down" else -800
                steps = 4
                for _ in range(steps):
                    page.mouse.wheel(0, total_delta // steps)
                    time.sleep(0.12)
                time.sleep(0.2)
                
            elif name == "scroll_at":
                x = denorm(args.get("x", 500), width)
                y = denorm(args.get("y", 500), height)
                direction = args.get("direction", "down")
                magnitude = args.get("magnitude", 800)
                scroll_amount = denorm(magnitude, height)
                
                page.mouse.move(x, y)
                time.sleep(0.1)
                
                # Smooth scroll in steps
                steps = 4
                for _ in range(steps):
                    if direction == "down":
                        page.mouse.wheel(0, scroll_amount // steps)
                    elif direction == "up":
                        page.mouse.wheel(0, -(scroll_amount // steps))
                    elif direction == "right":
                        page.mouse.wheel(scroll_amount // steps, 0)
                    elif direction == "left":
                        page.mouse.wheel(-(scroll_amount // steps), 0)
                    time.sleep(0.12)
                time.sleep(0.2)
                    
            elif name == "wait_5_seconds":
                time.sleep(3)
                
            elif name == "go_back":
                page.go_back()
                time.sleep(0.4)
                
            elif name == "go_forward":
                page.go_forward()
                time.sleep(0.4)
                
            elif name == "key_combination":
                keys = args.get("keys", "")
                page.keyboard.press(keys)
                time.sleep(0.3)
                
            elif name == "drag_and_drop":
                x = denorm(args["x"], width)
                y = denorm(args["y"], height)
                dest_x = denorm(args["destination_x"], width)
                dest_y = denorm(args["destination_y"], height)
                
                page.mouse.move(x, y)
                time.sleep(0.2)
                page.mouse.down()
                time.sleep(0.3)
                page.mouse.move(dest_x, dest_y)
                time.sleep(0.3)
                page.mouse.up()
                time.sleep(0.2)
                
            else:
                results.append((name, {"error": f"Unknown: {name}"}))
                continue
            
            try:
                page.wait_for_load_state("domcontentloaded", timeout=2000)
                time.sleep(0.2)
            except Exception:
                time.sleep(0.3)
            
            results.append((name, {}))
            
        except Exception as e:
            results.append((name, {"error": str(e)}))
    
    return results, function_calls, parts_with_fc


def create_function_responses(page, results, function_calls, parts_with_fc):
    """Create function response objects for Gemini from action results"""
    screenshot = page.screenshot(type="png")
    current_url = page.url
    
    function_responses = []
    for (name, result), fc, part in zip(results, function_calls, parts_with_fc):
        response_data = {"url": current_url, **result}
        
        # Get function call ID
        fc_id = getattr(fc, 'id', None)
        
        # Check for safety decision in BOTH places
        # 1. Check in function_call.args
        fc_args = getattr(fc, 'args', {}) or {}
        has_safety_decision_in_args = 'safety_decision' in fc_args
        
        # 2. Check in part.safety_ratings
        part_safety_ratings = getattr(part, 'safety_ratings', None)
        
        # If there's a safety decision anywhere, add acknowledgement to response
        if has_safety_decision_in_args or part_safety_ratings:
            response_data['safety_acknowledgement'] = 'true'
        
        # Build the FunctionResponse
        fr_kwargs = {
            'name': name,
            'response': response_data,
            'parts': [types.FunctionResponsePart(
                inline_data=types.FunctionResponseBlob(
                    mime_type="image/png",
                    data=screenshot
                )
            )]
        }
        
        # Add ID if present
        if fc_id:
            fr_kwargs['id'] = fc_id
        
        # Add safety_ratings if present
        if part_safety_ratings:
            fr_kwargs['safety_ratings'] = part_safety_ratings
        
        # Create the FunctionResponse
        function_response = types.FunctionResponse(**fr_kwargs)
        function_responses.append(function_response)
    
    return function_responses, screenshot
    
    return function_responses, screenshot


def extract_max_price(query):
    """Extract maximum price from query (e.g., 'under 300 euros' → 300)"""
    patterns = [
        r'under\s*\$?\€?(\d+)',
        r'below\s*\$?\€?(\d+)',
        r'less\s*than\s*\$?\€?(\d+)',
        r'max\s*\$?\€?(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return None


def parse_multiple_items(query):
    """Parse query for multiple items separated by 'and', '&', or ','"""
    items = []
    parts = re.split(r'\s+and\s+|\s+AND\s+|&|,', query, flags=re.IGNORECASE)
    
    for part in parts:
        part = part.strip()
        if part:
            items.append(part)
    
    if len(items) <= 1:
        return [query]
    
    return items


def scrape_amazon_results(page, max_items=10, max_price=None):
    """
    Scrape product information from Amazon.fr search results page.
    Returns list of product dictionaries with name, price, URL, and image.
    """
    products = []
    
    try:
        page.wait_for_selector('[data-component-type="s-search-result"]', timeout=5000)
        items = page.query_selector_all('[data-component-type="s-search-result"]')
        
        for item in items:
            if len(products) >= max_items:
                break
                
            try:
                # Extract title
                title = None
                for selector in ['h2 a span', 'h2 span', 'h2']:
                    elem = item.query_selector(selector)
                    if elem:
                        title = elem.inner_text().strip()
                        if title:
                            break
                
                if not title:
                    continue
                
                # Extract price
                price = None
                price_value = None
                for selector in ['.a-price .a-offscreen', '.a-price-whole', 'span.a-price', '.a-color-price']:
                    elem = item.query_selector(selector)
                    if elem:
                        price_text = elem.inner_text().strip()
                        if price_text:
                            price = price_text
                            price_match = re.search(r'[\d\s]+[.,]?\d*', price.replace('\xa0', ''))
                            if price_match:
                                try:
                                    price_str = price_match.group().replace(' ', '').replace(',', '.')
                                    price_value = float(price_str)
                                except Exception:
                                    pass
                            break
                
                if not price:
                    continue
                
                # Filter by max price
                if max_price and price_value:
                    if price_value > max_price:
                        continue
                
                # Extract product link
                link = ""
                link_elem = item.query_selector('h2 a, a.a-link-normal')
                if link_elem:
                    link = link_elem.get_attribute('href') or ""
                    if link and not link.startswith('http'):
                        link = f"https://www.amazon.fr{link}"
                
                # Extract image URL
                image_url = ""
                img_elem = item.query_selector('img')
                if img_elem:
                    image_url = (
                        img_elem.get_attribute('data-old-hires') or
                        img_elem.get_attribute('data-a-hires') or
                        img_elem.get_attribute('src') or
                        ""
                    )
                    
                    # Convert to high-res image
                    if image_url and ('images-na.ssl-images-amazon.com' in image_url or 'm.media-amazon.com' in image_url):
                        match = re.search(r'/images/I/([A-Za-z0-9+_-]+)', image_url)
                        if match:
                            image_id = match.group(1)
                            image_url = f"https://m.media-amazon.com/images/I/{image_id}._SL1500_.jpg"
                
                if not image_url:
                    image_url = "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=600"
                
                products.append({
                    "name": title,
                    "price": price,
                    "product_url": link,
                    "image_url": image_url,
                    "rating": ""
                })
                
            except Exception:
                continue
        
    except Exception:
        pass
    
    return products


def search_with_criteria(criteria, websites=None, max_turns=10, enable_query_refinement=True):
    """
    Main search function using Gemini Computer Use to automate Amazon.fr browsing.
    
    Args:
        criteria: Search query as string or list with 'prompt' key
        websites: Not used (for future multi-site support)
        max_turns: Maximum interaction turns with Gemini
        enable_query_refinement: Whether to refine natural language queries
        
    Returns:
        List of product dictionaries
    """
    # Parse query
    if isinstance(criteria, list) and len(criteria) > 0:
        query = criteria[0].get('prompt', '')
    elif isinstance(criteria, str):
        query = criteria
    else:
        query = "popular items"
    
    print("\n" + "="*60)
    print(f"🎯 Your Request: {query}")
    print(f"🤖 Gemini Computer Use is starting...")
    print("="*60 + "\n")
    
    # Detect and split outfit queries
    outfit_items = detect_and_split_outfit(query)
    
    if outfit_items:
        items_to_search = outfit_items
        print(f"   ✅ I've identified {len(items_to_search)} key pieces for your outfit\n")
    else:
        if enable_query_refinement:
            query = refine_search_query(query)
        items_to_search = parse_multiple_items(query)
    
    if len(items_to_search) > 1:
        print(f"   📋 I need to search for {len(items_to_search)} items separately\n")
    
    all_products = []
    playwright = None
    browser = None
    
    try:
        print("   🌐 I'm launching the browser...")
        playwright = sync_playwright().start()
        
        # Simple browser launch without fullscreen flags
        browser = playwright.chromium.launch(
            headless=False,
            slow_mo=80,
            args=[
                '--disable-blink-features=AutomationControlled',
                f'--window-size={W},{H}'
            ]
        )
        
        # Explicit viewport with zoom out
        context = browser.new_context(
            viewport={'width': W, 'height': H},
            device_scale_factor=0.8,  # Zoom out to 80% to see more content
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            bypass_csp=True,
            ignore_https_errors=True
        )
        page = context.new_page()
        
        print("   ✅ Browser ready!\n")
        
        # Search for each item
        for item_index, item_query in enumerate(items_to_search, 1):
            if len(items_to_search) > 1:
                print(f"   📍 Item {item_index}/{len(items_to_search)}: {item_query}")
                print(f"   💭 I'm going to Amazon.fr to find this...")
            
            page.goto("https://www.amazon.fr/?language=fr_FR&currency=EUR", timeout=30000)
            time.sleep(0.5)
            
            # Only reset scroll position
            try:
                page.evaluate("window.scrollTo(0, 0);")
                time.sleep(0.2)
            except Exception:
                pass
            
            # Accept cookies
            try:
                cookie_button = page.query_selector('#sp-cc-accept')
                if cookie_button:
                    print("   🍪 I'm accepting cookies...")
                    cookie_button.click()
                    time.sleep(0.5)
            except Exception:
                pass
            
            screenshot = page.screenshot(type="png")
            
            # Extract price filter
            max_price = extract_max_price(item_query)
            search_terms = item_query
            
            if max_price:
                print(f"   💰 I'll filter for items under {max_price}€")
                search_terms = re.sub(r'under\s*\$?\d+', '', search_terms, flags=re.IGNORECASE)
                search_terms = re.sub(r'below\s*\$?\d+', '', search_terms, flags=re.IGNORECASE)
                search_terms = re.sub(r'(euro|euros|dollar|dollars)', '', search_terms, flags=re.IGNORECASE)
                search_terms = ' '.join(search_terms.split())
            
            print(f"   🔍 I'm searching for: '{search_terms}'")
            
            # Create goal for Gemini Computer Use
            goal = f"""Search Amazon.fr for "{search_terms}".

Steps:
1. Click search box
2. Type: "{search_terms}"
3. Press Enter
4. Wait 3 seconds
5. Scroll down twice
6. Say "Done"

Page is at top - search box visible."""
            
            contents = [
                Content(
                    role="user",
                    parts=[
                        Part(text=goal),
                        Part.from_bytes(data=screenshot, mime_type="image/png")
                    ]
                )
            ]
            
            config = types.GenerateContentConfig(
                tools=[types.Tool(computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER
                ))],
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="BLOCK_ONLY_HIGH"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="BLOCK_ONLY_HIGH"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="BLOCK_ONLY_HIGH"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="BLOCK_ONLY_HIGH"
                    ),
                ]
            )
            
            # Interaction loop with Gemini
            for turn in range(max_turns):
                try:
                    response = client.models.generate_content(
                        model=MODEL,
                        contents=contents,
                        config=config
                    )
                except Exception as e:
                    print(f"      ⚠️  API Error: {str(e)}")
                    if "safety" in str(e).lower():
                        print("      I detected a safety issue - I'll continue with what I have...")
                        break
                    raise
                
                candidate = response.candidates[0]
                contents.append(candidate.content)
                
                function_calls = [p.function_call for p in candidate.content.parts if getattr(p, "function_call", None)]
                
                if not function_calls:
                    break
                
                results, fcs, parts = execute_actions(candidate, page, (W, H), show_narration=True)
                function_responses, screenshot = create_function_responses(page, results, fcs, parts)
                
                contents.append(
                    Content(
                        role="user",
                        parts=[Part(function_response=fr) for fr in function_responses]
                    )
                )
            
            # Scrape results
            print(f"   🎯 I'm extracting product information...")
            products_per_item = 5
            products = scrape_amazon_results(page, max_items=products_per_item, max_price=max_price)
            
            if products:
                print(f"      ✅ Found {len(products)} great options!\n")
                all_products.extend(products)
            else:
                print(f"      ⚠️  Hmm, didn't find any products for this item\n")
        
        print("="*60)
        print(f"✅ All done! I found {len(all_products)} products total")
        print("="*60 + "\n")
        
        if not all_products:
            print("   💡 No products found, showing sample data...")
            all_products = [
                {"name": "Sample Product", "price": "49,99 €", "product_url": "https://amazon.fr", 
                 "image_url": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=400", "rating": ""}
            ]
        
        time.sleep(1)
        return all_products
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
        
    finally:
        if browser:
            print("   🧹 I'm closing the browser...")
            browser.close()
        if playwright:
            playwright.stop()


def add_to_cart_and_checkout(items, user_info):
    """Placeholder checkout function for demo purposes"""
    return {
        "success": True,
        "message": f"Processed {len(items)} items",
        "order_id": f"ORD-{int(time.time())}",
        "items": items,
        "user": user_info
    }


if __name__ == "__main__":
    query = "I need an outfit for a job interview under 250 euros"
    products = search_with_criteria(
        criteria=[{"prompt": query}],
        max_turns=10,
        enable_query_refinement=True
    )
    print(f"\n✅ Found {len(products)} products")
