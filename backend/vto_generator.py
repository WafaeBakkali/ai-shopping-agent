"""
Virtual Try-On Generator using Gemini 2.5 Flash Image (Nano Banana)

"""

import base64
import requests
from google.genai import types
from PIL import Image
from io import BytesIO


def download_image(url, timeout=10):
    """Download image from URL and return bytes"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.content
        return None
    except Exception:
        return None


def create_product_collage(product_images_bytes, max_size=1200):

    if len(product_images_bytes) == 0:
        return None
    
    if len(product_images_bytes) == 1:
        return product_images_bytes[0]
    
    print(f"\n🖼️  Creating collage from {len(product_images_bytes)} items (aspect ratios preserved)...")
    
    images = []
    for img_bytes in product_images_bytes:
        try:
            img = Image.open(BytesIO(img_bytes))
            if img.mode != 'RGB':
                img = img.convert('RGB')
            images.append(img)
        except Exception as e:
            print(f"   ⚠️  Failed to open image: {e}")
            continue
    
    if len(images) == 0:
        return None
    
    num_images = len(images)
    
    # Layout based on number of items
    if num_images == 2:
        cols = 2
        rows = 1
    elif num_images == 3:
        # Special layout: 1 large left, 2 stacked right
        cols = 2
        rows = 2
    elif num_images == 4:
        cols = 2
        rows = 2
    else:
        # 5+ items: 3 columns
        cols = 3
        rows = (num_images + 2) // 3
    
    # Calculate dimensions
    cell_width = max_size // cols
    cell_height = max_size // rows
    
    # Create white background collage
    collage_width = cell_width * cols
    collage_height = cell_height * rows
    collage = Image.new('RGB', (collage_width, collage_height), 'white')
    
    def resize_and_center(img, target_width, target_height):
        """Resize image to fit within target size while maintaining aspect ratio"""
        # Calculate scaling to fit within cell
        img_aspect = img.width / img.height
        target_aspect = target_width / target_height
        
        if img_aspect > target_aspect:
            # Image is wider - fit to width
            new_width = target_width
            new_height = int(target_width / img_aspect)
        else:
            # Image is taller - fit to height
            new_height = target_height
            new_width = int(target_height * img_aspect)
        
        # Resize maintaining aspect ratio
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create white cell
        cell = Image.new('RGB', (target_width, target_height), 'white')
        
        # Center image in cell
        paste_x = (target_width - new_width) // 2
        paste_y = (target_height - new_height) // 2
        cell.paste(img_resized, (paste_x, paste_y))
        
        return cell
    
    # Special layout for 3 items
    if num_images == 3:
        # Item 1: Left side (full height) - ASPECT RATIO PRESERVED
        cell1 = resize_and_center(images[0], cell_width, collage_height)
        collage.paste(cell1, (0, 0))
        
        # Item 2: Top right - ASPECT RATIO PRESERVED
        cell2 = resize_and_center(images[1], cell_width, cell_height)
        collage.paste(cell2, (cell_width, 0))
        
        # Item 3: Bottom right - ASPECT RATIO PRESERVED
        cell3 = resize_and_center(images[2], cell_width, cell_height)
        collage.paste(cell3, (cell_width, cell_height))
    else:
        # Standard grid layout - ALL ASPECT RATIOS PRESERVED
        for idx, img in enumerate(images):
            row = idx // cols
            col = idx % cols
            
            # Resize maintaining aspect ratio
            cell = resize_and_center(img, cell_width, cell_height)
            
            # Calculate position
            x = col * cell_width
            y = row * cell_height
            
            # Paste cell
            collage.paste(cell, (x, y))
    
    # Convert to bytes
    output = BytesIO()
    collage.save(output, format='JPEG', quality=95)
    collage_bytes = output.getvalue()
    
    print(f"   ✓ Collage created: {collage_width}x{collage_height}px")
    print(f"   ✓ Layout: {rows} rows × {cols} cols")
    print(f"   ✓ All aspect ratios preserved (no stretching)")
    
    # Save debug copy
    try:
        debug_path = "/tmp/vto_collage_simple.jpg"
        with open(debug_path, "wb") as f:
            f.write(collage_bytes)
        print(f"   📁 Debug: Saved to {debug_path}")
    except Exception:
        pass
    
    return collage_bytes


def generate_multi_product_tryon(user_photo_base64, products, gemini_client):
    """
    Generate virtual try-on with simple approach
    
    Args:
        user_photo_base64: Base64 encoded user photo
        products: List of product dicts with name, price, image_url
        gemini_client: Initialized Gemini client
        
    Returns:
        str: Base64 encoded result image as data URL
    """
    if not gemini_client:
        raise ValueError("Gemini client not initialized")
    
    print(f"\n{'='*70}")
    print(f"🍌 VIRTUAL TRY-ON (Nano Banana)")
    print(f"{'='*70}")
    print(f"Items to try on: {len(products)}")
    
    # Decode user photo
    try:
        user_photo_bytes = base64.b64decode(
            user_photo_base64.split(',')[1] if ',' in user_photo_base64 else user_photo_base64
        )
        print(f"✓ User photo decoded ({len(user_photo_bytes)} bytes)")
    except Exception as e:
        raise ValueError(f"Failed to decode user photo: {e}")
    
    # Build product list
    product_details = []
    has_shoes = False
    
    for i, product in enumerate(products, 1):
        name = product['name']
        product_details.append(f"{i}. {name}")
        print(f"   {i}. {name[:60]}...")
        
        if any(word in name.lower() for word in ['shoe', 'shoes', 'sneaker', 'boot', 'loafer', 'heel', 'sandal']):
            has_shoes = True
            print(f"      👟 Shoes detected")
    
    products_text = "\n".join(product_details)
    num_items = len(products)
    needs_collage = len(products) > 2
    
    # Download product images
    print(f"\n📸 Downloading product images...")
    product_images_bytes = []
    
    for i, product in enumerate(products, 1):
        image_url = product.get('image_url') or product.get('image')
        if image_url and image_url.startswith('http'):
            image_bytes = download_image(image_url, timeout=15)
            if image_bytes:
                product_images_bytes.append(image_bytes)
                print(f"   {i}/{num_items}: ✓ Downloaded")
            else:
                print(f"   {i}/{num_items}: ✗ Failed")
    
    if len(product_images_bytes) == 0:
        raise Exception("No product images downloaded")
    
    # Create collage if needed
    if needs_collage:
        print(f"\n🎨 Creating simple grid collage for {len(product_images_bytes)} items...")
        collage_bytes = create_product_collage(product_images_bytes)
        if collage_bytes:
            product_images_bytes = [collage_bytes]
            print(f"   ✓ Using grid collage")
    
    if needs_collage:
        # Multiple items with collage
        prompt = "Generate a picture of the person in the first image wearing all the clothes shown in the collage photo (second image)."
    
    elif len(products) == 2:
        # Two items
        prompt = "Generate a picture of the person in the first image wearing the clothes shown in the second and third images."
    
    else:
        # Single item
        prompt = "Generate a picture of the person in the first image wearing the clothing item shown in the second image."
    
    model = "gemini-2.5-flash-image"
    
    parts = [
        types.Part.from_text(text=prompt),
        types.Part.from_bytes(data=user_photo_bytes, mime_type="image/jpeg"),
    ]
    
    # Add product images (max 2 to stay within 3-image limit)
    images_to_add = min(len(product_images_bytes), 2)
    for i in range(images_to_add):
        parts.append(types.Part.from_bytes(
            data=product_images_bytes[i], 
            mime_type="image/jpeg"
        ))
    
    print(f"📤 SENDING TO NANO BANANA")
    
    # Create content
    contents = [types.Content(role="user", parts=parts)]
    
    # Configure
    config = types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
        temperature=0.1,  # Low for consistency
    )
    
    result_images = []
    
    print(f"\n🎨 Generating with Nano Banana...")
    
    try:
        # Stream response
        for chunk in gemini_client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config
        ):
            if (chunk.candidates is None or 
                chunk.candidates[0].content is None or 
                chunk.candidates[0].content.parts is None):
                continue
            
            part = chunk.candidates[0].content.parts[0]
            
            # Check for image data
            if part.inline_data and part.inline_data.data:
                image_base64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                mime_type = part.inline_data.mime_type
                result_images.append(f"data:{mime_type};base64,{image_base64}")
                print("   ✓ Image chunk received")
            
            # Also print any text
            if hasattr(part, 'text') and part.text:
                print(f"   📝 Text: {part.text[:100]}")
                
    except Exception as e:
        print(f"   ❌ Generation error: {e}")
        raise
    
    print(f"{'='*70}")
    
    if result_images:
        print(f"✅ SUCCESS! Generated {len(result_images)} image(s)")
        print(f"{'='*70}\n")
        
        # Return first image
        return result_images[0]
    else:
        print(f"❌ FAILED - No image generated")
        print(f"{'='*70}\n")
        raise Exception("No image generated by Nano Banana")


if __name__ == "__main__":
    print("Virtual Try-On Generator - SIMPLE VERSION")
