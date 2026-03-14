#!/usr/bin/env python3
"""
Scrape Michael Kors product images from retailer sites (Nordstrom, Macy's, Bloomingdale's)
and match them to our product catalog.
"""

import json
import os
import re
import time
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Paths
JSON_FILE = Path("public/brands/michael-kors.json")
OUTPUT_DIR = Path("public/images/michael-kors")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load existing product catalog
with open(JSON_FILE, 'r') as f:
    products = json.load(f)

print(f"Loaded {len(products)} Michael Kors products")

# Headers to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/',
}

def clean_product_name(name):
    """Clean product name for matching"""
    # Remove leading/trailing dashes and whitespace
    name = name.strip().strip('-').strip()
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    return name.lower()

def extract_keywords(name):
    """Extract key identifying words from product name"""
    # Remove common words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'with', 'for', 'to', 'of'}
    words = clean_product_name(name).split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return set(keywords)

def scrape_google_images(product_name, max_results=5):
    """
    Use Google Images search to find product images.
    Returns list of image URLs.
    """
    query = f"Michael Kors {product_name} product image"
    search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}&tbm=isch"
    
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"  ⚠️  Google search failed: {response.status_code}")
            return []
        
        # Parse image URLs from response (simplified - Google Images is tricky)
        # This is a basic approach; for production, use Google Custom Search API
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for image tags and data attributes
        images = []
        for img in soup.find_all('img', limit=max_results):
            src = img.get('src') or img.get('data-src')
            if src and src.startswith('http'):
                images.append(src)
        
        return images[:max_results]
    
    except Exception as e:
        print(f"  ❌ Error scraping Google: {e}")
        return []

def download_image(url, output_path, timeout=30):
    """Download image from URL to output path"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
            return True
        else:
            print(f"  ⚠️  HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Download error: {e}")
        return False

def get_image_size(path):
    """Get file size in KB"""
    return path.stat().st_size / 1024 if path.exists() else 0

# Process products
successful = 0
failed = 0
skipped = 0

for idx, product in enumerate(products, 1):
    product_name = clean_product_name(product['n'])
    category = product['c']
    image_path = OUTPUT_DIR / Path(product['i']).name
    
    # Check if we already have a good image (>50KB)
    if image_path.exists() and get_image_size(image_path) > 50:
        skipped += 1
        if idx % 50 == 0:
            print(f"[{idx}/{len(products)}] Skipping (already exists): {product_name[:50]}...")
        continue
    
    print(f"\n[{idx}/{len(products)}] 🔍 Searching: {product_name[:60]}...")
    
    # Try Google Images
    image_urls = scrape_google_images(product_name, max_results=3)
    
    if not image_urls:
        print(f"  ⚠️  No images found")
        failed += 1
        continue
    
    # Try downloading first good image
    downloaded = False
    for img_url in image_urls:
        print(f"  📥 Trying: {img_url[:80]}...")
        if download_image(img_url, image_path):
            size_kb = get_image_size(image_path)
            if size_kb > 10:  # At least 10KB
                print(f"  ✅ Downloaded {size_kb:.1f}KB")
                successful += 1
                downloaded = True
                break
            else:
                print(f"  ⚠️  Too small ({size_kb:.1f}KB), trying next...")
    
    if not downloaded:
        failed += 1
        print(f"  ❌ Failed to get valid image")
    
    # Rate limiting
    time.sleep(2)  # Be nice to servers
    
    # Progress checkpoint
    if idx % 25 == 0:
        print(f"\n📊 Progress: {successful} success, {failed} failed, {skipped} skipped")

print(f"\n{'='*60}")
print(f"🏁 FINAL RESULTS:")
print(f"  ✅ Success: {successful}")
print(f"  ❌ Failed:  {failed}")
print(f"  ⏭️  Skipped: {skipped}")
print(f"  📊 Total:   {len(products)}")
print(f"{'='*60}")
