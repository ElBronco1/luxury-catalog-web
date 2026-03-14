# Pandora Image Scraping Instructions

## Task Summary
Scrape 2,075 Pandora product images from us.pandora.net and save them to `public/images/pandora/`

## Strategy

### 1. Extract Image URLs from Each Category

Visit these URLs in browser (with `sz=999` to load all products):

- https://us.pandora.net/en/jewelry/charms/?sz=999
- https://us.pandora.net/en/jewelry/bracelets/?sz=999  
- https://us.pandora.net/en/jewelry/rings/?sz=999
- https://us.pandora.net/en/jewelry/necklaces/?sz=999
- https://us.pandora.net/en/jewelry/earrings/?sz=999

### 2. Run This Script in Browser Console

```javascript
(async () => {
  const products = [];
  const images = Array.from(document.querySelectorAll('img')).filter(img => 
    img.src && img.src.includes('pandora.net') && img.src.includes('/dw/image/') && img.src.includes('_RGB')
  );
  
  images.forEach(img => {
    const container = img.closest('a');
    if (!container) return;
    
    let name = '';
    const paragraphs = Array.from(container.querySelectorAll('p'));
    
    for (const p of paragraphs) {
      const text = p.textContent.trim();
      if (text.includes('$') || text.includes('NEW') || text.includes('BEST SELLER') || text.length < 5) {
        continue;
      }
      if (text.length > 10) {
        name = text;
        break;
      }
    }
    
    if (!name) {
      const ariaLabel = container.getAttribute('aria-label');
      if (ariaLabel) name = ariaLabel.split('\n')[0].trim();
    }
    
    if (img.src && img.src.includes('_RGB')) {
      const highResUrl = img.src.replace(/\?.*$/, '').replace(/sw=\d+/, 'sw=600').replace(/sh=\d+/, 'sh=600') + '?sw=600&sh=600&sm=fit&sfrm=png';
      
      products.push({
        name: name || 'Unknown',
        url: highResUrl
      });
    }
  });
  
  const unique = Array.from(new Map(products.map(p => [p.url, p])).values());
  console.log(JSON.stringify(unique, null, 2));
  return unique;
})();
```

### 3. Save Output

Copy the JSON output from console and append to `pandora_scraped.json`

### 4. Download Images

```bash
chmod +x download_pandora.sh
./download_pandora.sh
```

## Current Progress

- **Scraped so far:** 73 URLs from charms page
- **Remaining:** ~2,002 products

## Notes

- Each category should be scraped separately to avoid browser slowdown
- Use `sz=999` parameter to load max products per page
- Filter for `_RGB` in URL to get product shots (not model shots)
- Pandora CDN URL pattern: `/dw/image/v2/AAVX_PRD/.../productimages/.../[SKU]_RGB.jpg`
