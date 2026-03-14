/**
 * Extract Pandora product image URLs from loaded page
 * Run this in browser console on us.pandora.net category pages
 * Copy the output and save to pandora_scraped.json
 */

async function extractProducts() {
  const products = [];
  
  // Get all images
  const images = Array.from(document.querySelectorAll('img')).filter(img => 
    img.src && img.src.includes('pandora.net') && img.src.includes('/dw/image/')
  );
  
  console.log(`Found ${images.length} product images on page`);
  
  images.forEach(img => {
    const container = img.closest('a');
    if (!container) return;
    
    // Try to get product name
    let name = '';
    const paragraphs = Array.from(container.querySelectorAll('p'));
    
    for (const p of paragraphs) {
      const text = p.textContent.trim();
      // Skip prices and labels
      if (text.includes('$') || text.includes('NEW') || text.includes('BEST SELLER') || text.length < 5) {
        continue;
      }
      if (text.length > 10) {
        name = text;
        break;
      }
    }
    
    // Fallback to aria-label
    if (!name) {
      const ariaLabel = container.getAttribute('aria-label');
      if (ariaLabel) {
        name = ariaLabel.split('\n')[0].trim();
      }
    }
    
    if (img.src) {
      // Upgrade to 600x600
      const highResUrl = img.src
        .replace(/\?sw=\d+/, '?sw=600')
        .replace(/&sh=\d+/, '&sh=600');
      
      products.push({
        name: name || 'Unknown',
        url: highResUrl
      });
    }
  });
  
  return products;
}

// Main execution
(async () => {
  console.log('Extracting products...');
  const products = await extractProducts();
  
  // Deduplicate
  const unique = Array.from(new Map(products.map(p => [p.url, p])).values());
  
  console.log(`\nExtracted ${unique.length} unique products`);
  console.log('\n=== COPY EVERYTHING BELOW THIS LINE ===\n');
  console.log(JSON.stringify(unique, null, 2));
  console.log('\n=== END ===\n');
  
  return unique;
})();
