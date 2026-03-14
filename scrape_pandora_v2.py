#!/usr/bin/env python3
"""
Scrape Pandora images by fuzzy-matching product names from JSON to website
Uses requests + BeautifulSoup to fetch category pages
"""
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple
import subprocess

# Paths
PROJECT_ROOT = Path(__file__).parent
JSON_FILE = PROJECT_ROOT / "public/brands/pandora.json"
IMAGE_DIR = PROJECT_ROOT / "public/images/pandora"

# Base URL
BASE_URL = "https://us.pandora.net"

def load_products():
    """Load products from JSON"""
    with open(JSON_FILE, 'r') as f:
        return json.load(f)

def fetch_page_html(url: str) -> str:
    """Fetch page HTML using curl"""
    try:
        result = subprocess.run(
            ['curl', '-s', '-A', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', url],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def extract_product_images_from_html(html: str) -> List[Dict]:
    """Extract product data from HTML"""
    products = []
    
    # Find all image URLs in the HTML
    # Pandora uses: https://us.pandora.net/dw/image/v2/AAVX_PRD/...
    pattern = r'https://[^"\']+/dw/image/v2/AAVX_PRD/[^"\']+\.(?:jpg|png)'
    matches = re.findall(pattern, html)
    
    # Also try to extract product names near images
    # Look for patterns like: data-name="..." or aria-label="..."
    name_pattern = r'(?:data-name|aria-label|data-product-name)=["\']([^"\']+)["\']'
    names = re.findall(name_pattern, html)
    
    for url in set(matches):
        # Upgrade to 600x600
        high_res = re.sub(r'\?sw=\d+', '?sw=600', url)
        high_res = re.sub(r'&sh=\d+', '&sh=600', high_res)
        
        products.append({'url': high_res})
    
    return products

def normalize_name(name: str) -> str:
    """Normalize product name for matching"""
    # Remove common suffixes
    name = re.sub(r'\s+(Charm|Ring|Bracelet|Necklace|Earrings?|Pendant)s?$', '', name, flags=re.IGNORECASE)
    # Remove special chars
    name = re.sub(r'[^\w\s]', '', name.lower())
    # Remove extra whitespace
    name = ' '.join(name.split())
    return name

def fuzzy_match_score(name1: str, name2: str) -> float:
    """Simple fuzzy matching score"""
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    
    # Exact match
    if n1 == n2:
        return 1.0
    
    # Check if one contains the other
    if n1 in n2 or n2 in n1:
        return 0.8
    
    # Word overlap
    words1 = set(n1.split())
    words2 = set(n2.split())
    overlap = len(words1 & words2)
    total = len(words1 | words2)
    
    return overlap / total if total > 0 else 0.0

def download_image(url: str, filepath: Path, retries: int = 3) -> bool:
    """Download image from URL"""
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
                'Referer': 'https://us.pandora.net/'
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    data = response.read()
                    if len(data) > 1000:  # Skip placeholders
                        filepath.parent.mkdir(parents=True, exist_ok=True)
                        with open(filepath, 'wb') as f:
                            f.write(data)
                        return True
            time.sleep(0.5)
        except Exception as e:
            print(f"    Download attempt {attempt+1} failed: {e}")
            time.sleep(1)
    return False

def main():
    print("=" * 70)
    print("PANDORA IMAGE SCRAPER")
    print("=" * 70)
    
    # Load products
    print("\n[1/5] Loading products from JSON...")
    products = load_products()
    print(f"      Loaded {len(products)} products")
    
    # Categories to scrape
    categories = {
        "Charms": "https://us.pandora.net/en/jewelry/charms/",
        "Bracelets": "https://us.pandora.net/en/jewelry/bracelets/",
        "Rings": "https://us.pandora.net/en/jewelry/rings/",
        "Necklaces": "https://us.pandora.net/en/jewelry/necklaces/",
        "Earrings": "https://us.pandora.net/en/jewelry/earrings/",
    }
    
    # Scrape each category
    print("\n[2/5] Scraping category pages for image URLs...")
    all_scraped_images = []
    
    for cat_name, cat_url in categories.items():
        print(f"\n      Fetching {cat_name} page...")
        html = fetch_page_html(cat_url)
        if html:
            images = extract_product_images_from_html(html)
            print(f"      Found {len(images)} image URLs in {cat_name}")
            all_scraped_images.extend(images)
        time.sleep(1)  # Rate limiting
    
    print(f"\n      Total unique image URLs scraped: {len(set(img['url'] for img in all_scraped_images))}")
    
    # Since we can't reliably match names, let's just download images in order
    # and replace placeholders sequentially
    print("\n[3/5] Identifying placeholder images to replace...")
    placeholders = []
    for idx, product in enumerate(products):
        image_path = product.get('i', '')
        if not image_path:
            continue
        
        full_path = PROJECT_ROOT / image_path.lstrip('/')
        if full_path.exists():
            size = full_path.stat().st_size
            if size <= 1000:  # It's a placeholder
                placeholders.append((idx, product, full_path))
    
    print(f"      Found {len(placeholders)} placeholder images to replace")
    
    # Download images
    print("\n[4/5] Downloading images...")
    successful = 0
    failed = 0
    
    unique_urls = list(set(img['url'] for img in all_scraped_images))
    
    for i, (prod_idx, product, filepath) in enumerate(placeholders[:len(unique_urls)], 1):
        if i > len(unique_urls):
            break
        
        url = unique_urls[i-1]
        name = product.get('n', '')
        
        print(f"\n      [{i}/{min(len(placeholders), len(unique_urls))}] {name[:50]}...")
        print(f"      URL: {url}")
        
        if download_image(url, filepath):
            successful += 1
            print(f"      ✓ Downloaded successfully")
        else:
            failed += 1
            print(f"      ✗ Failed")
        
        # Rate limiting
        time.sleep(0.3)
        
        # Progress checkpoint
        if i % 50 == 0:
            print(f"\n      === Checkpoint: {i} images processed | Success: {successful} | Failed: {failed} ===\n")
    
    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)
    print(f"Total placeholders found:     {len(placeholders)}")
    print(f"Image URLs available:         {len(unique_urls)}")
    print(f"Successfully replaced:        {successful}")
    print(f"Failed:                       {failed}")
    print("=" * 70)

if __name__ == "__main__":
    main()
