#!/usr/bin/env python3
"""
Brand image scraper. Each brand has its own strategy.
Usage: python3 scrape_brand.py <brand-slug>
"""
import json, os, re, sys, subprocess, time, urllib.request, urllib.parse, ssl
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web')
BRANDS = BASE / 'public' / 'brands'
IMAGES = BASE / 'public' / 'images'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
}

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:80]

def download(url, filepath, referer=None, min_size=2000):
    """Download image. Returns True on success."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > min_size:
        return True
    hdrs = dict(HEADERS)
    if referer:
        hdrs['Referer'] = referer
    try:
        req = urllib.request.Request(url, headers=hdrs)
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            data = resp.read()
            if len(data) < min_size:
                return False
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(data)
            return True
    except Exception as e:
        return False

def download_curl(url, filepath, referer=None, min_size=2000):
    """Download using curl (better for some CDNs)."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > min_size:
        return True
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    cmd = ['curl', '-sL', '-o', filepath, '-m', '15',
           '-H', f'User-Agent: {HEADERS["User-Agent"]}']
    if referer:
        cmd += ['-H', f'Referer: {referer}']
    cmd.append(url)
    try:
        subprocess.run(cmd, timeout=20, capture_output=True)
        if os.path.exists(filepath) and os.path.getsize(filepath) > min_size:
            return True
        if os.path.exists(filepath):
            os.remove(filepath)
        return False
    except:
        return False

def load_products(slug):
    with open(BRANDS / f'{slug}.json') as f:
        return json.load(f)

def save_products(slug, products):
    with open(BRANDS / f'{slug}.json', 'w') as f:
        json.dump(products, f)

def report(slug, ok, fail, skip, total):
    print(f'  [{slug}] {ok} downloaded, {fail} failed, {skip} skipped / {total} total')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scrape_brand.py <brand-slug>")
        sys.exit(1)
    brand = sys.argv[1]
    print(f"Scraper loaded for: {brand}")
    print(f"Working dir: {BASE}")
    print(f"Brand JSON: {BRANDS / f'{brand}.json'}")
    print(f"Image dir: {IMAGES / brand}")
