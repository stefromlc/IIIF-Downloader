"""
IIIF High-Resolution Image Downloader
-------------------------------------

Downloads ultra high-resolution images from IIIF-compatible servers
and stitches image tiles into a single full-resolution image.
Supports digital archives, historical maps, manuscripts, artwork,
and other large-scale archival imagery.
"""

import os
import re
import math
import io
import sys
import gc
import time
import urllib3
from PIL import Image
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Suppress InsecureRequestWarning if we bypass SSL verification
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Lift the Pillow bomb protection limit for massive map images
Image.MAX_IMAGE_PIXELS = None

# Constants
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


def setup_session(map_id):
    """Sets up a robust requests session with retries and precise headers."""
    session = requests.Session()
    
    # Adding an exact Referer header and standard browser accepts
    session.headers.update({
        'User-Agent': USER_AGENT,
        'Referer': f'https://maps.nls.uk/view/{map_id}',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8'
    })
    
    # Configure retry strategy for rate limits (429) or server hiccups
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def extract_map_id(url):
    """Extracts the numerical map ID from the NLS viewer URL."""
    match = re.search(r'/view/(\d+)', url)
    if not match:
        raise ValueError("Could not find a valid map ID in the URL. Ensure it looks like: https://maps.nls.uk/view/245959203")
    return match.group(1)


def get_map_metadata(session, map_id):
    """Fetches the IIIF info.json metadata to get exact map dimensions and safe tile sizes."""
    folder = map_id[:5]
    info_url = f"https://map-view.nls.uk/iiif/2/{folder}%2F{map_id}/info.json"
    
    print(f"Fetching metadata from: {info_url}")
    
    try:
        response = session.get(info_url, verify=False, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        width = data.get('width')
        height = data.get('height')
        
        if not width or not height:
            raise ValueError("info.json did not contain width/height data.")
            
        # Dynamically read the server's native tile size (usually 256 or 512).
        # This prevents 403 "Area Too Large" errors caused by requesting huge chunks.
        chunk_size = 512 # Safe fallback
        if 'tiles' in data and len(data['tiles']) > 0:
            chunk_size = data['tiles'][0].get('width', 512)
            
        return width, height, folder, chunk_size
        
    except requests.exceptions.RequestException as e:
        print(f"\nError fetching metadata: {e}")
        print("Check if the URL is correct or if the map requires special permissions.")
        sys.exit(1)


def download_and_stitch(session, map_id, folder, total_width, total_height, chunk_size, output_filename):
    """Downloads tiles in chunks and stitches them into a final Pillow Image."""
    print(f"\nInitializing blank canvas of {total_width}x{total_height} pixels...")
    # Create blank canvas (RGB)
    canvas = Image.new('RGB', (total_width, total_height))
    
    # Calculate grid size
    cols = math.ceil(total_width / chunk_size)
    rows = math.ceil(total_height / chunk_size)
    total_chunks = cols * rows
    current_chunk = 1
    
    size_param = "full"
    
    print(f"Server preferred tile size is {chunk_size}x{chunk_size}.")
    print(f"Starting download ({total_chunks} chunks)...")
    
    for y in range(0, total_height, chunk_size):
        for x in range(0, total_width, chunk_size):
            w = min(chunk_size, total_width - x)
            h = min(chunk_size, total_height - y)
            
            # Print progress bar
            percent = (current_chunk / total_chunks) * 100
            sys.stdout.write(f"\rDownloading chunk {current_chunk}/{total_chunks} [{percent:.1f}%] (X:{x} Y:{y})")
            sys.stdout.flush()
            
            # Construct tile URL
            tile_url = f"https://map-view.nls.uk/iiif/2/{folder}%2F{map_id}/{x},{y},{w},{h}/{size_param}/0/default.jpg"
            
            try:
                response = session.get(tile_url, verify=False, timeout=15)
                
                # Fallback logic for IIIF 3.0 or strict servers
                if response.status_code in [400, 403, 404] and size_param == "full":
                    size_param = "max"
                    tile_url = f"https://map-view.nls.uk/iiif/2/{folder}%2F{map_id}/{x},{y},{w},{h}/{size_param}/0/default.jpg"
                    response = session.get(tile_url, verify=False, timeout=15)
                
                response.raise_for_status()
                
                # Open image chunk and paste it onto the canvas
                img_chunk = Image.open(io.BytesIO(response.content))
                canvas.paste(img_chunk, (x, y))
                
                # Free memory
                img_chunk.close()
                del response
                gc.collect()
                
            except Exception as e:
                print(f"\nFailed to download chunk at {x},{y}. Error: {e}")
                print(f"URL that failed: {tile_url}")
                print("Continuing with next chunk, but there will be a blank spot in the final image.")
            
            current_chunk += 1
            # Add a tiny delay to be polite to the archival server and avoid rate-limiting
            time.sleep(0.05)
            
    print("\n\nDownload complete! Saving high-resolution image to disk...")
    # Save the result
    try:
        canvas.save(output_filename, quality=95)
        print(f"Success! Image saved as: {output_filename}")
    except Exception as e:
        print(f"Error saving image: {e}")
    finally:
        canvas.close()


def main():
    print("="*50)
    print("   NLS High-Resolution Map Downloader")
    print("="*50)
    
    url = input("Enter NLS Map URL (e.g., https://maps.nls.uk/view/245959203): ").strip()
    
    try:
        map_id = extract_map_id(url)
    except ValueError as e:
        print(e)
        sys.exit(1)
        
    print(f"Extracted Map ID: {map_id}")
    
    session = setup_session(map_id)
    
    # 1. Fetch Metadata and ideal chunk size
    width, height, folder, chunk_size = get_map_metadata(session, map_id)
    print(f"Map Dimensions: {width} x {height} pixels (Total: {(width*height)/1000000:.1f} Megapixels)")
    
    # 2. Setup output filename
    default_filename = f"NLS_Map_{map_id}.jpg"
    out_filename = input(f"Enter output filename [default: {default_filename}]: ").strip()
    if not out_filename:
        out_filename = default_filename
        
    # Ensure standard extension
    if not out_filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        out_filename += '.jpg'
        
    # 3. Process Download and Stitch
    download_and_stitch(session, map_id, folder, width, height, chunk_size, out_filename)


if __name__ == "__main__":
    main()
    #python map-downloader.py

    