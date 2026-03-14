#!/usr/bin/env python3
"""
Automated image scraper for luxury catalog brands.
Uses requests + BeautifulSoup for brands that allow it,
and falls back to placeholder image generation for blocked brands.

Approach: For each brand, tries to find product images via:
1. Direct CDN URL construction (if pattern known)
2. Site search/API 
3. Product page scraping
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
import ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Disable SSL verification for some CDNs
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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

def download_image(url, filepath, referer=None):
    """Download image. Returns True on success."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 3000:
        return True
    hdrs = dict(HEADERS)
    if referer:
        hdrs['Referer'] = referer
    try:
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            data = resp.read()
            if len(data) < 1500:
                return False
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except Exception:
        return False


def process_ulta_from_cache(cache_file):
    """Process Ulta products using a pre-built cache."""
    brand_slug = 'ulta'
    with open(BRANDS_DIR / f'{brand_slug}.json') as f:
        products = json.load(f)
    with open(cache_file) as f:
        cache = json.load(f)
    
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    need = [(i, p) for i, p in enumerate(products) if not p.get('i')]
    print(f"\nUlta: {len(products)} total, {len(need)} need, {len(cache)} cached")
    
    # Normalize cache
    def norm(s): return re.sub(r'[^\w\s]', '', s.lower()).strip()
    cache_norm = {norm(k): v for k, v in cache.items()}
    
    ok = fail = nomatch = 0
    for idx, prod in need:
        name = prod['n']
        n = norm(name)
        url = cache_norm.get(n)
        
        # Try partial matching
        if not url:
            words = set(n.split()) - {'the', 'a', 'an', 'with', 'for', 'and', 'in', 'of', 'by', 'to'}
            if len(words) >= 2:
                best = 0
                for cn, cu in cache_norm.items():
                    cw = set(cn.split())
                    if words and cw:
                        score = len(words & cw) / max(len(words), 1)
                        if score > best:
                            best = score
                            url = cu
                if best < 0.55:
                    url = None
        
        if not url:
            nomatch += 1
            continue
        
        slug = slugify(name)
        filename = f"{idx+1}-{slug}.jpg"
        filepath = str(img_dir / filename)
        
        if download_image(url, filepath, 'https://www.ulta.com/'):
            products[idx]['i'] = f"/images/{brand_slug}/{filename}"
            ok += 1
        else:
            fail += 1
        
        if (ok + fail) % 100 == 0 and (ok + fail) > 0:
            with open(BRANDS_DIR / f'{brand_slug}.json', 'w') as f:
                json.dump(products, f)
            print(f"  Ulta: {ok} ok, {fail} fail, {nomatch} no match")
    
    with open(BRANDS_DIR / f'{brand_slug}.json', 'w') as f:
        json.dump(products, f)
    print(f"  Ulta DONE: {ok} ok, {fail} fail, {nomatch} no match")


def process_brand_with_scene7(brand_slug, scene7_base, cache_file, referer=''):
    """Process brands that use Scene7 CDN (Coach, Kate Spade)."""
    with open(BRANDS_DIR / f'{brand_slug}.json') as f:
        products = json.load(f)
    with open(cache_file) as f:
        cache = json.load(f)
    
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    need = [(i, p) for i, p in enumerate(products) if not p.get('i')]
    print(f"\n{brand_slug}: {len(products)} total, {len(need)} need, {len(cache)} cached")
    
    def norm(s): return re.sub(r'[^\w\s]', '', s.lower()).strip()
    cache_norm = {norm(k): v for k, v in cache.items()}
    
    ok = fail = nomatch = 0
    for idx, prod in need:
        name = prod['n']
        n = norm(name)
        url = cache_norm.get(n)
        
        if not url:
            words = set(n.split()) - {'the', 'a', 'an', 'with', 'for', 'and', 'in', 'of', 'by', 'to'}
            if len(words) >= 2:
                best = 0
                for cn, cu in cache_norm.items():
                    cw = set(cn.split())
                    score = len(words & cw) / max(len(words), 1)
                    if score > best:
                        best = score
                        url = cu
                if best < 0.55:
                    url = None
        
        if not url:
            nomatch += 1
            continue
        
        slug = slugify(name)
        filename = f"{idx+1}-{slug}.jpg"
        filepath = str(img_dir / filename)
        
        if download_image(url, filepath, referer):
            products[idx]['i'] = f"/images/{brand_slug}/{filename}"
            ok += 1
        else:
            fail += 1
        
        if (ok + fail) % 50 == 0 and (ok + fail) > 0:
            with open(BRANDS_DIR / f'{brand_slug}.json', 'w') as f:
                json.dump(products, f)
            print(f"  {brand_slug}: {ok} ok, {fail} fail, {nomatch} no match")
    
    with open(BRANDS_DIR / f'{brand_slug}.json', 'w') as f:
        json.dump(products, f)
    print(f"  {brand_slug} DONE: {ok} ok, {fail} fail, {nomatch} no match")


if __name__ == '__main__':
    brand = sys.argv[1] if len(sys.argv) > 1 else None
    cache_dir = BASE_DIR / 'scripts' / 'caches'
    
    if brand == 'ulta':
        process_ulta_from_cache(cache_dir / 'ulta.json')
    elif brand in ('coach', 'kate-spade'):
        scene7_bases = {
            'coach': 'https://coach.scene7.com/is/image/Coach/',
            'kate-spade': 'https://katespade.scene7.com/is/image/KateSpade/',
        }
        referers = {
            'coach': 'https://www.coachoutlet.com/',
            'kate-spade': 'https://www.katespade.com/',
        }
        process_brand_with_scene7(brand, scene7_bases[brand], cache_dir / f'{brand}.json', referers[brand])
    else:
        print("Usage: python3 auto_scrape.py <brand-slug>")
        print("Brands: ulta, coach, kate-spade")
