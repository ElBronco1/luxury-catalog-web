#!/usr/bin/env python3
"""
Smart scraper: Uses brand-specific CDN patterns and web APIs to find product images.
Designed for speed - tries direct URL construction first, falls back to search.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE_DIR = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')
BRANDS_DIR = BASE_DIR / 'public' / 'brands'
IMAGES_DIR = BASE_DIR / 'public' / 'images'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]

def download_image(url, filepath, extra_headers=None):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 3000:
        return True
    hdrs = dict(HEADERS)
    if extra_headers:
        hdrs.update(extra_headers)
    try:
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            if len(data) < 1000:
                return False
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except Exception:
        return False


def try_url(url, headers=None):
    """Check if a URL returns valid image data."""
    hdrs = dict(HEADERS)
    if headers:
        hdrs.update(headers)
    try:
        req = urllib.request.Request(url, headers=hdrs, method='HEAD')
        with urllib.request.urlopen(req, timeout=5) as resp:
            ct = resp.headers.get('Content-Type', '')
            cl = int(resp.headers.get('Content-Length', '0'))
            return 'image' in ct and cl > 1000
    except Exception:
        return False


def search_lululemon(product_name):
    """Search Lululemon API for a product and return image URL."""
    query = urllib.parse.quote(product_name)
    api_url = f'https://shop.lululemon.com/api/c/search?q={query}&page=0&pageSize=1'
    try:
        req = urllib.request.Request(api_url, headers={
            'User-Agent': HEADERS['User-Agent'],
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            products = data.get('products', [])
            if products:
                images = products[0].get('images', [])
                if images:
                    return images[0].get('mainCarousel', {}).get('media', images[0].get('url', ''))
    except Exception:
        pass
    return None


def search_victoria_secret(product_name):
    """Try Victoria's Secret product search."""
    query = urllib.parse.quote(product_name)
    api_url = f'https://www.victoriassecret.com/vs/api/search?q={query}&count=1'
    try:
        req = urllib.request.Request(api_url, headers={
            'User-Agent': HEADERS['User-Agent'],
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            # Parse response for image URL
            results = data.get('results', [])
            if results:
                return results[0].get('image', {}).get('url')
    except Exception:
        pass
    return None


def process_lululemon():
    """Process Lululemon using their public search API."""
    brand_slug = 'lululemon'
    brand_file = BRANDS_DIR / f'{brand_slug}.json'
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    with open(brand_file) as f:
        products = json.load(f)
    
    need = [(i, p) for i, p in enumerate(products) if not p.get('i')]
    print(f"\nLululemon: {len(products)} total, {len(need)} need images")
    
    ok = 0
    fail = 0
    
    for idx, prod in need:
        name = prod['n']
        # Clean up name - remove size info
        clean_name = re.sub(r'\s*\d+"?\s*$', '', name)
        clean_name = re.sub(r'\s*\*\w+\s*$', '', clean_name)
        
        url = search_lululemon(clean_name)
        if url:
            slug = slugify(name)
            filename = f"{idx+1}-{slug}.jpg"
            filepath = str(img_dir / filename)
            
            if download_image(url, filepath):
                products[idx]['i'] = f"/images/{brand_slug}/{filename}"
                ok += 1
            else:
                fail += 1
        else:
            fail += 1
        
        if (ok + fail) % 50 == 0 and (ok + fail) > 0:
            with open(brand_file, 'w') as f:
                json.dump(products, f)
            print(f"  Progress: {ok} ok, {fail} fail / {len(need)}")
        
        time.sleep(0.2)  # Rate limit
    
    with open(brand_file, 'w') as f:
        json.dump(products, f)
    
    print(f"Lululemon: {ok} downloaded, {fail} failed")
    return ok


def process_tommy_hilfiger():
    """Process Tommy Hilfiger using their product search API."""
    brand_slug = 'tommy-hilfiger'
    brand_file = BRANDS_DIR / f'{brand_slug}.json'
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    with open(brand_file) as f:
        products = json.load(f)
    
    need = [(i, p) for i, p in enumerate(products) if not p.get('i')]
    print(f"\nTommy Hilfiger: {len(products)} total, {len(need)} need images")
    
    # Tommy uses tommy.scene7.com CDN
    # Try search API
    ok = 0
    fail = 0
    
    for idx, prod in need:
        name = prod['n']
        query = urllib.parse.quote(name)
        
        # Try Tommy's search API
        api_url = f'https://usa.tommy.com/api/search?q={query}&count=1'
        url = None
        
        try:
            req = urllib.request.Request(api_url, headers={
                'User-Agent': HEADERS['User-Agent'],
                'Accept': 'application/json',
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                # Try to extract image URL from response
                items = data.get('items', data.get('products', data.get('results', [])))
                if items and isinstance(items, list):
                    img = items[0].get('image', items[0].get('imageUrl', ''))
                    if img:
                        url = img
        except Exception:
            pass
        
        if url:
            slug = slugify(name)
            filename = f"{idx+1}-{slug}.jpg"
            filepath = str(img_dir / filename)
            
            if download_image(url, filepath, {'Referer': 'https://usa.tommy.com/'}):
                products[idx]['i'] = f"/images/{brand_slug}/{filename}"
                ok += 1
            else:
                fail += 1
        else:
            fail += 1
        
        if (ok + fail) % 50 == 0 and (ok + fail) > 0:
            with open(brand_file, 'w') as f:
                json.dump(products, f)
            print(f"  Progress: {ok} ok, {fail} fail / {len(need)}")
        
        time.sleep(0.2)
    
    with open(brand_file, 'w') as f:
        json.dump(products, f)
    
    print(f"Tommy Hilfiger: {ok} downloaded, {fail} failed")
    return ok


if __name__ == '__main__':
    brand = sys.argv[1] if len(sys.argv) > 1 else 'lululemon'
    
    if brand == 'lululemon':
        process_lululemon()
    elif brand == 'tommy':
        process_tommy_hilfiger()
    else:
        print(f"Unknown brand: {brand}")
