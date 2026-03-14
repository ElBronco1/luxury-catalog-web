#!/usr/bin/env python3
"""
Download images from cached name->URL mappings.
Usage: python3 download_from_cache.py <brand-slug>
Cache files should be at: scripts/caches/{brand-slug}.json
"""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')
BRANDS_DIR = BASE_DIR / 'public' / 'brands'
IMAGES_DIR = BASE_DIR / 'public' / 'images'
CACHE_DIR = BASE_DIR / 'scripts' / 'caches'

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

def normalize(s):
    return re.sub(r'[^\w\s]', '', s.lower()).strip()

def download(url, filepath, referer=None):
    if os.path.exists(filepath) and os.path.getsize(filepath) > 3000:
        return True
    hdrs = dict(HEADERS)
    if referer:
        hdrs['Referer'] = referer
    try:
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            if len(data) < 2000:
                return False
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except Exception:
        return False

def main(brand_slug):
    cache_file = CACHE_DIR / f'{brand_slug}.json'
    brand_file = BRANDS_DIR / f'{brand_slug}.json'
    
    if not cache_file.exists():
        print(f"ERROR: No cache file at {cache_file}")
        return
    
    with open(cache_file) as f:
        cache = json.load(f)
    with open(brand_file) as f:
        products = json.load(f)
    
    img_dir = IMAGES_DIR / brand_slug
    os.makedirs(img_dir, exist_ok=True)
    
    need = [(i, p) for i, p in enumerate(products) if not p.get('i')]
    print(f"{brand_slug}: {len(products)} total, {len(need)} need, {len(cache)} cached")
    
    # Normalize cache
    cache_norm = {}
    for k, v in cache.items():
        n = normalize(k)
        if n not in cache_norm:
            cache_norm[n] = v
    
    ok = fail = nomatch = 0
    
    for idx, prod in need:
        name = prod['n']
        norm = normalize(name)
        
        # Exact
        url = cache_norm.get(norm)
        
        # Word overlap
        if not url:
            words = set(norm.split()) - {'the', 'a', 'an', 'with', 'for', 'and', 'in', 'of', 'by', 'to'}
            if len(words) >= 2:
                best_score = 0
                for cn, cu in cache_norm.items():
                    cw = set(cn.split())
                    if words and cw:
                        score = len(words & cw) / max(len(words), 1)
                        if score > best_score:
                            best_score = score
                            url = cu
                if best_score < 0.55:
                    url = None
        
        if not url:
            nomatch += 1
            continue
        
        slug = slugify(name)
        filename = f"{idx+1}-{slug}.jpg"
        filepath = str(img_dir / filename)
        
        if download(url, filepath):
            products[idx]['i'] = f"/images/{brand_slug}/{filename}"
            ok += 1
        else:
            fail += 1
        
        if (ok + fail) % 100 == 0 and (ok + fail) > 0:
            with open(brand_file, 'w') as f:
                json.dump(products, f)
            print(f"  {ok} ok, {fail} fail, {nomatch} no match / {len(need)}")
        
        if (ok + fail) % 20 == 0:
            time.sleep(0.1)
    
    with open(brand_file, 'w') as f:
        json.dump(products, f)
    
    print(f"DONE: {ok} ok, {fail} fail, {nomatch} no match / {len(need)}")

if __name__ == '__main__':
    main(sys.argv[1])
