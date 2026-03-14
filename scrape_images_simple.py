#!/usr/bin/env python3
"""
Simple image scraper - downloads placeholder images for catalog
"""

import json
import os
import subprocess
from pathlib import Path
import re

def slugify(text):
    """Convert text to slug format"""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def download_placeholder_images():
    """Download placeholder product images"""
    
    base_dir = Path("/Users/maurocastellanos/clawd/projects/luxury-catalog-web")
    brands = {
        'victorias-secret': [
            'https://i.pinimg.com/736x/89/b5/8f/89b58f96bc8bcecc0fbbc64a4cda87bb.jpg',  # VS bra placeholder
            'https://i.pinimg.com/736x/d9/e4/d1/d9e4d1c4a0d0c7e0f9f7a8b2c3d4e5f6.jpg',  # Generic lingerie
        ],
        'tommy-hilfiger': [
            'https://via.placeholder.com/400x500/003da5/ffffff?text=Tommy+Hilfiger+Product',
        ],
        'calvin-klein': [
            'https://via.placeholder.com/400x500/000000/ffffff?text=Calvin+Klein+Product',
        ]
    }
    
    for brand_slug, urls in brands.items():
        print(f"\n===== {brand_slug} =====")
        
        # Read JSON
        json_path = base_dir / 'public' / 'brands' / f'{brand_slug}.json'
        with open(json_path) as f:
            products = json.load(f)
        
        # Limit to first 10 products
        products = products[:10]
        
        img_dir = base_dir / 'public' / 'images' / brand_slug
        img_dir.mkdir(parents=True, exist_ok=True)
        
        updated_count = 0
        for idx, product in enumerate(products):
            if product['i']:  # Skip if already has image
                continue
            
            # Use a single placeholder URL (cycle through if we had more)
            url_idx = idx % len(urls)
            img_url = urls[url_idx]
            
            product_slug = slugify(product['n'])
            output_file = img_dir / f"{idx}-{product_slug}.jpg"
            
            print(f"  [{idx}] {product['n'][:40]}")
            
            # Download with curl
            try:
                result = subprocess.run(
                    ['curl', '-L', '-o', str(output_file), img_url],
                    capture_output=True,
                    timeout=10
                )
                
                if result.returncode == 0 and output_file.exists():
                    # Update JSON with relative path
                    product['i'] = f"/images/{brand_slug}/{output_file.name}"
                    updated_count += 1
                    print(f"      ✓ Downloaded")
                else:
                    print(f"      ✗ Download failed")
            except Exception as e:
                print(f"      ✗ Error: {e}")
        
        # Save updated JSON
        if updated_count > 0:
            with open(json_path, 'w') as f:
                json.dump(products, f, indent=2)
            print(f"\n  Updated {updated_count} products in {brand_slug}.json")

if __name__ == '__main__':
    download_placeholder_images()
    print("\n✅ Done!")
