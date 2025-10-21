"""
Video Generator using Veo 3.1
Creates 360° product showcase videos with camera rotation

"""

import base64
import time
import tempfile
import os
from google import genai
from google.genai import types


def generate_fashion_video_veo(user_photo_base64, products, project_id, location="us-central1"):
    """
    Generate professional product showcase video with Veo 3.1
    
    Args:
        user_photo_base64 (str): Base64 data URL of virtual try-on result
        products (list): List of product dicts with 'name', 'price', 'image_url'
        project_id (str): Google Cloud project ID
        location (str): GCP region (default: "us-central1")
        
    Returns:
        str: Base64 data URL of the generated MP4 video
        
    Raises:
        ValueError: If inputs are invalid or missing
        Exception: If video generation fails
    """
    print(f"\n{'='*80}")
    print(f"🎬 VEO 3.1 VIDEO GENERATION")
    print(f"{'='*80}")
    print(f"📍 Project: {project_id}")
    print(f"📍 Location: {location}")
    print(f"👔 Outfit items: {len(products)}")
    
    # Validate inputs
    if not user_photo_base64:
        raise ValueError("user_photo_base64 is required")
    if not products or len(products) == 0:
        raise ValueError("products list is required and must not be empty")
    if not project_id:
        raise ValueError("project_id is required")
    
    # Initialize Vertex AI client
    try:
        client = genai.Client(vertexai=True, project=project_id, location=location)
        print("✅ Vertex AI client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Vertex AI client")
        print(f"   Error: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Install: pip install google-genai")
        print(f"   2. Authenticate: gcloud auth application-default login")
        print(f"   3. Set project: gcloud config set project {project_id}")
        print(f"   4. Enable Vertex AI API:")
        print(f"      https://console.cloud.google.com/apis/library/aiplatform.googleapis.com")
        raise
    
    # Decode and save try-on image to temp file
    temp_path = None
    try:
        # Handle data URL format
        if ',' in user_photo_base64:
            image_data = user_photo_base64.split(',')[1]
        else:
            image_data = user_photo_base64
        
        tryon_image_bytes = base64.b64decode(image_data)
        print(f"✅ Image decoded ({len(tryon_image_bytes):,} bytes = {len(tryon_image_bytes)/1024:.1f} KB)")
        
        # Save to temporary file (required by Veo API)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        temp_file.write(tryon_image_bytes)
        temp_file.close()
        temp_path = temp_file.name
        print(f"✅ Saved to temp file: {temp_path}")
        
    except Exception as e:
        print(f"❌ Failed to process image: {e}")
        raise ValueError(f"Failed to decode image: {e}")
    
    # Analyze outfit components
    product_names = [p.get('name', 'Unknown item') for p in products]
    print(f"\n👔 Outfit Components:")
    for i, name in enumerate(product_names, 1):
        display_name = name[:70] + "..." if len(name) > 70 else name
        print(f"   {i}. {display_name}")
    
    # Detect shoes for camera movement decision
    shoe_keywords = ['shoe', 'shoes', 'sneaker', 'boot', 'loafer', 'heel', 'sandal', 'slipper']
    has_shoes = any(
        keyword in name.lower() 
        for name in product_names 
        for keyword in shoe_keywords
    )
    
    camera_type = "360° full rotation" if has_shoes else "180° rotation"
    print(f"\n📸 Camera Movement: {camera_type}")
    if has_shoes:
        print(f"   👟 Shoes detected → Full body view with 360° rotation")
    else:
        print(f"   👕 No shoes → Upper body focus with 180° rotation")
    
    # Build product list for prompt
    product_list = "\n".join(f"- {name[:40]}" for name in product_names)
    
    # Create optimized prompt for Veo 3.1
    if has_shoes:
        # Full outfit with shoes - 360° rotation
        prompt = f"""Professional product showcase video with smooth 360-degree camera rotation.

SUBJECT: Person wearing complete outfit consisting of {len(products)} items:
{product_list}

CAMERA MOVEMENT:
- Start: Front view of person
- Action: Smooth 360-degree clockwise rotation around person
- End: Return to front view
- Style: Continuous, fluid motion throughout
- No cuts or jumps

VISUAL STYLE:
- Framing: Full body shot (head to toe visible)
- Pose: Person stands still in natural, confident pose
- Lighting: Professional studio lighting, even and flattering
- Background: Clean, minimal background (solid or softly blurred)
- Quality: High-quality e-commerce style

TECHNICAL:
- Camera moves, person remains stationary
- Show all sides: front, left side, back, right side, front"""
    
    else:
        # Upper body outfit - 180° rotation
        prompt = f"""Professional product showcase video with smooth camera rotation.

SUBJECT: Person wearing stylish outfit consisting of {len(products)} items:
{product_list}

CAMERA MOVEMENT:
- Start: Front view of person
- Action: Smooth 180-degree rotation around person
- Path: Front → Side → Back → Side → Front
- Style: Continuous, fluid motion
- No cuts or jumps

VISUAL STYLE:
- Framing: Upper body and mid-section focus
- Pose: Person stands still in natural, confident pose
- Lighting: Professional studio lighting
- Background: Clean, minimal
- Quality: High-quality e-commerce style

TECHNICAL:
- Camera moves, person remains stationary
- Show front, side profiles, and back"""
    
    
    # Generate video with Veo 3.1
    print(f"\n🎬 Starting Veo 3.1 video generation...")
    print(f"   🎥 Using try-on result as starting frame")
    
    try:
        # Load image from temp file
        tryon_image = types.Image.from_file(location=temp_path)
        print(f"   ✅ Image loaded for Veo 3.1")
        
        # Start video generation operation
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt,
            image=tryon_image,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                number_of_videos=1,
                duration_seconds=8,
                resolution="1080p",
                person_generation="allow_adult",
                enhance_prompt=True,
                generate_audio=True,
            ),
        )
        
        print(f"   ✅ Operation started: {operation.name}")
        print(f"   ⏳ Waiting for completion...")
        
        # Poll for completion with progress indicator
        start_time = time.time()
        last_update = start_time
        
        while not operation.done:
            current_time = time.time()
            elapsed = int(current_time - start_time)
            
            # Update every 10 seconds
            if current_time - last_update >= 10:
                minutes = elapsed // 60
                seconds = elapsed % 60
                print(f"   ⏳ Processing... {minutes}m {seconds}s elapsed")
                last_update = current_time
            
            time.sleep(10)
            operation = client.operations.get(operation)
        
        elapsed_total = int(time.time() - start_time)
        minutes = elapsed_total // 60
        seconds = elapsed_total % 60
        print(f"\n   ✅ Generation complete in {minutes}m {seconds}s")
        
        # Extract video from operation result
        if not operation.response:
            raise Exception("Operation completed but no response received")
        
        # Check that result exists
        if not operation.result:
            raise Exception("Operation completed but result is None - video generation may have failed")
        
        # Check that generated_videos attribute exists
        if not hasattr(operation.result, 'generated_videos'):
            raise Exception("Operation result has no generated_videos attribute")
        
        # Check that generated_videos is not None before checking length
        if operation.result.generated_videos is None:
            raise Exception("Generated videos is None - generation may have been blocked or failed")
        
        # Check that generated_videos list is not empty
        if len(operation.result.generated_videos) == 0:
            raise Exception("No videos in operation result - generation may have been blocked or failed")
        
        # Extract the first video
        video_bytes = operation.result.generated_videos[0].video.video_bytes
        
        # Convert to base64 data URL
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        video_data_url = f"data:video/mp4;base64,{video_base64}"
        
        # Success summary
        video_size_mb = len(video_bytes) / 1024 / 1024
        print(f"\n{'='*80}")
        print(f"✅ SUCCESS! Video generated")
        
        return video_data_url
        
    except Exception as e:
        print(f"\n❌ Video generation failed")
        print(f"   Error: {str(e)}")
        print(f"\n💡 Troubleshooting:")
        print(f"   • Verify Vertex AI API is enabled:")
        print(f"     https://console.cloud.google.com/apis/library/aiplatform.googleapis.com")
        print(f"   • Check Veo 3.1 access for project: {project_id}")
        print(f"   • Verify billing is enabled:")
        print(f"     https://console.cloud.google.com/billing")
        print(f"   • Check quota limits:")
        print(f"     https://console.cloud.google.com/iam-admin/quotas")
        print(f"   • Ensure try-on image is valid and not corrupted")
        print(f"   • Try with a different region (location parameter)")
        raise
        
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                print(f"🧹 Cleaned up temp file")
            except Exception as e:
                print(f"⚠️  Warning: Could not delete temp file: {e}")


if __name__ == "__main__":
    print("Veo 3.1 Video Generator")
    print()
    print("="*80)
