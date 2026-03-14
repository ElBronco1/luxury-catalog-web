#!/usr/bin/env python3
"""
Read Ulta product cache from browser-extracted JSON data.
This reads from ulta_product_cache.json and downloads images.
"""
import json
import os
import re
import sys
from pathlib import Path
from difflib import SequenceMatcher

BASE_DIR = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')
BRANDS_DIR = BASE_DIR / 'public' / 'brands'
IMAGES_DIR = BASE_DIR / 'public' / 'images'
CACHE_FILE = BASE_DIR / 'scripts' / 'ulta_product_cache.json'

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]

def normalize(s):
    return re.sub(r'[^\w\s]', '', s.lower()).strip()

def main():
    # Load cache
    if not CACHE_FILE.exists():
        print("No cache file. Build it first.")
        return
    
    with open(CACHE_FILE) as f:
        cache = json.load(f)
    
    print(f"Cache: {len(cache)} products")
    
    # Load ulta products  
    with open(BRANDS_DIR / 'ulta.json') as f:
        products = json.load(f)
    
    need = [(i, p) for i, p in enumerate(products) if not p.get('i')]
    print(f"Products: {len(products)} total, {len(need)} need images")
    
    # Build normalized cache
    cache_norm = {}
    for name, url in cache.items():
        n = normalize(name)
        cache_norm[n] = url
    
    # Match products
    matched = []
    unmatched = []
    
    for idx, prod in need:
        name = prod['n']
        norm = normalize(name)
        
        # Exact match
        if norm in cache_norm:
            matched.append((idx, cache_norm[norm], 'exact'))
            continue
        
        # Try with "brand product" format (Ulta products have names like "Product Name" 
        # but Ulta listings show "Brand Product Name")
        found = False
        for cn, url in cache_norm.items():
            # Check if our product name is a suffix of the cache name
            if cn.endswith(norm) or norm in cn:
                matched.append((idx, url, 'suffix'))
                found = True
                break
        
        if found:
            continue
        
        # Fuzzy match - check top candidates
        best = 0
        best_url = None
        for cn, url in cache_norm.items():
            # Quick filter: skip if too different in length
            if abs(len(cn) - len(norm)) > len(norm) * 0.5:
                continue
            r = SequenceMatcher(None, norm, cn).ratio()
            if r > best:
                best = r
                best_url = url
        
        if best > 0.60:
            matched.append((idx, best_url, f'fuzzy:{best:.2f}'))
        else:
            unmatched.append((idx, name))
    
    print(f"\nMatched: {len(matched)}")
    print(f"Unmatched: {len(unmatched)}")
    
    if matched:
        print(f"\nSample matches:")
        for idx, url, method in matched[:5]:
            print(f"  [{method}] {products[idx]['n'][:60]} -> {url[-30:]}")
    
    if unmatched:
        print(f"\nSample unmatched:")
        for idx, name in unmatched[:5]:
            print(f"  {name[:80]}")
    
    # Download matched images
    import urllib.request
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'image/*,*/*;q=0.8',
    }
    
    img_dir = IMAGES_DIR / 'ulta'
    os.makedirs(img_dir, exist_ok=True)
    
    ok = 0
    fail = 0
    
    for idx, url, method in matched:
        name = products[idx]['n']
        slug = slugify(name)
        filename = f"{idx+1}-{slug}.jpg"
        filepath = str(img_dir / filename)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 3000:
            products[idx]['i'] = f"/images/ulta/{filename}"
            ok += 1
            continue
        
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
                if len(data) > 1000:
                    with open(filepath, 'wb') as f:
                        f.write(data)
                    products[idx]['i'] = f"/images/ulta/{filename}"
                    ok += 1
                else:
                    fail += 1
        except Exception:
            fail += 1
        
        if (ok + fail) % 100 == 0:
            with open(BRANDS_DIR / 'ulta.json', 'w') as f:
                json.dump(products, f)
            print(f"  Progress: {ok} downloaded, {fail} failed")
    
    # Final save
    with open(BRANDS_DIR / 'ulta.json', 'w') as f:
        json.dump(products, f)
    
    print(f"\nFinal: {ok} downloaded, {fail} failed, {len(unmatched)} unmatched")


if __name__ == '__main__':
    main()
