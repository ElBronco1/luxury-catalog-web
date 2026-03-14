#!/usr/bin/env python3
"""
Build brand cache files from browser-extracted data and download images.
This script contains all the data we've scraped and handles the download pipeline.
"""
import json
import os
import re
import time
import urllib.request
import urllib.error
import ssl
from pathlib import Path

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_DIR = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')
BRANDS_DIR = BASE_DIR / 'public' / 'brands'
IMAGES_DIR = BASE_DIR / 'public' / 'images'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
}


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]


def download_image(url, filepath, referer=None):
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


def normalize(s):
    return re.sub(r'[^\w\s]', '', s.lower()).strip()


def match_and_download(brand_slug, cache, referer=None):
    """Match cache entries to product JSON and download images."""
    brand_file = BRANDS_DIR / f'{brand_slug}.json'
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    with open(brand_file) as f:
        products = json.load(f)
    
    need = [(i, p) for i, p in enumerate(products) if not p.get('i')]
    print(f"\n{'='*60}")
    print(f"{brand_slug}: {len(products)} total, {len(need)} need, {len(cache)} cached")
    print(f"{'='*60}")
    
    if not need:
        print("  All images present!")
        return 0
    
    cache_norm = {normalize(k): v for k, v in cache.items()}
    
    ok = fail = nomatch = 0
    
    for idx, prod in need:
        name = prod['n']
        n = normalize(name)
        
        # Exact match
        url = cache_norm.get(n)
        
        # Partial word overlap match
        if not url:
            words = set(n.split()) - {'the', 'a', 'an', 'with', 'for', 'and', 'in', 'of', 'by', 'to', 'on'}
            if len(words) >= 2:
                best = 0
                best_url = None
                for cn, cu in cache_norm.items():
                    cw = set(cn.split())
                    if cw:
                        score = len(words & cw) / max(len(words), 1)
                        if score > best:
                            best = score
                            best_url = cu
                if best >= 0.55:
                    url = best_url
        
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
            with open(brand_file, 'w') as f:
                json.dump(products, f)
            print(f"  {ok} ok, {fail} fail, {nomatch} no match / {len(need)}")
        
        if (ok + fail) % 20 == 0:
            time.sleep(0.05)
    
    with open(brand_file, 'w') as f:
        json.dump(products, f)
    
    print(f"  DONE: {ok} ok, {fail} fail, {nomatch} no match")
    return ok


if __name__ == '__main__':
    import sys
    brand = sys.argv[1] if len(sys.argv) > 1 else 'all'
    cache_dir = BASE_DIR / 'scripts' / 'caches'
    os.makedirs(cache_dir, exist_ok=True)
    
    brands_to_process = []
    
    if brand in ('kate-spade', 'all'):
        cache_file = cache_dir / 'kate-spade.json'
        if cache_file.exists():
            with open(cache_file) as f:
                cache = json.load(f)
            match_and_download('kate-spade', cache, 'https://www.katespade.com/')
    
    if brand in ('coach', 'all'):
        cache_file = cache_dir / 'coach.json'
        if cache_file.exists():
            with open(cache_file) as f:
                cache = json.load(f)
            match_and_download('coach', cache, 'https://www.coachoutlet.com/')
    
    if brand in ('ulta', 'all'):
        cache_file = cache_dir / 'ulta.json'
        if cache_file.exists():
            with open(cache_file) as f:
                cache = json.load(f)
            match_and_download('ulta', cache, 'https://www.ulta.com/')
    
    if brand in ('tory-burch', 'all'):
        cache_file = cache_dir / 'tory-burch.json'
        if cache_file.exists():
            with open(cache_file) as f:
                cache = json.load(f)
            match_and_download('tory-burch', cache, 'https://www.toryburch.com/')
