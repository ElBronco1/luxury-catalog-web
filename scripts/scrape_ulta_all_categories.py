#!/usr/bin/env python3
"""
Aggregate Ulta product cache from browser-extracted data.
Reads stdin for JSON data extracted from browser and appends to cache.
"""
import json
import sys
from pathlib import Path

CACHE_FILE = Path('/Users/maurocastellanos/clawd/projects/luxury-catalog-web/scripts/ulta_product_cache.json')

def add_to_cache(new_data):
    """Add new product mappings to the cache."""
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            cache = json.load(f)
    else:
        cache = {}
    
    before = len(cache)
    cache.update(new_data)
    after = len(cache)
    
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)
    
    print(f"Cache: {before} -> {after} products (+{after - before} new)")

if __name__ == '__main__':
    data = json.load(sys.stdin)
    if isinstance(data, dict) and 'data' in data:
        add_to_cache(data['data'])
    elif isinstance(data, dict):
        add_to_cache(data)
    else:
        print("Unknown format")
