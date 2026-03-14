#!/usr/bin/env python3
"""
Batch download images from a URL mapping file.
Usage: python3 batch_download.py <brand-slug> <mapping-file>

mapping-file is a JSON file: {"product_index": {"url": "...", "name": "..."}, ...}
"""
import json, os, re, sys, requests, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]

def download_one(args):
    idx, url, name, brand_slug, referer = args
    slug = slugify(name)
    filename = f"{idx}-{slug}.jpg"
    filepath = BASE / 'public' / 'images' / brand_slug / filename
    
    if filepath.exists() and filepath.stat().st_size > 3000:
        return idx, filename, True, 'cached'
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'image/*,*/*',
        }
        if referer:
            headers['Referer'] = referer
        
        resp = requests.get(url, headers=headers, timeout=15, verify=False)
        if resp.status_code == 200 and len(resp.content) > 2000:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(resp.content)
            return idx, filename, True, 'downloaded'
        return idx, filename, False, f'status={resp.status_code} size={len(resp.content)}'
    except Exception as e:
        return idx, filename, False, str(e)[:60]

def main():
    brand_slug = sys.argv[1]
    mapping_file = sys.argv[2]
    referer = sys.argv[3] if len(sys.argv) > 3 else ''
    
    with open(mapping_file) as f:
        mapping = json.load(f)
    
    products_file = BASE / 'public' / 'brands' / f'{brand_slug}.json'
    with open(products_file) as f:
        products = json.load(f)
    
    print(f"[{brand_slug}] {len(mapping)} images to download for {len(products)} products")
    
    tasks = []
    for idx_str, info in mapping.items():
        idx = int(idx_str)
        tasks.append((idx, info['url'], info['name'], brand_slug, referer))
    
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(download_one, t): t for t in tasks}
        for future in as_completed(futures):
            idx, filename, success, reason = future.result()
            if success:
                ok += 1
                products[idx]['i'] = f"/images/{brand_slug}/{filename}"
            else:
                fail += 1
            
            if (ok + fail) % 100 == 0:
                print(f"  [{brand_slug}] {ok} ok, {fail} fail / {len(tasks)} total")
                with open(products_file, 'w') as f:
                    json.dump(products, f)
    
    with open(products_file, 'w') as f:
        json.dump(products, f)
    
    print(f"[{brand_slug}] DONE: {ok} downloaded, {fail} failed / {len(tasks)} total")

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()
    main()
