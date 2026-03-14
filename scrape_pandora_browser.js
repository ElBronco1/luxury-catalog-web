/**
 * Scrape Pandora product images using browser automation
 * Run in browser console on us.pandora.net category pages
 */

async function scrapeProductsFromPage() {
    const products = [];
    
    // Find all product tiles on the page
    const productLinks = document.querySelectorAll('a[href*="/en/charms/"], a[href*="/en/bracelets/"], a[href*="/en/rings/"], a[href*="/en/necklaces/"], a[href*="/en/earrings/"]');
    
    productLinks.forEach(link => {
        // Get product image
        const img = link.querySelector('img[src*="/dw/image/"]');
        if (!img || !img.src) return;
        
        // Get product name - try multiple selectors
        let name = '';
        const nameElem = link.querySelector('p, [class*="product-name"], [class*="title"]');
        if (nameElem) {
            name = nameElem.textContent.trim();
        } else {
            // Try aria-label
            name = link.getAttribute('aria-label') || '';
        }
        
        // Clean name - remove extra labels
        name = name.split('\n')[0].trim();
        name = name.replace(/^(NEW|BEST SELLER|TOP GIFT|BACK IN STOCK|EXCLUSIVE TO MY PANDORA MEMBERS|LAST CHANCE)\s*\|\s*/gi, '');
        name = name.replace(/\s*\|\s*(NEW|BEST SELLER|TOP GIFT).*$/gi, '');
        
        if (name && img.src.includes('/dw/image/')) {
            // Upgrade to 600x600
            const highResUrl = img.src
                .replace(/\?sw=\d+/, '?sw=600')
                .replace(/&sh=\d+/, '&sh=600');
            
            products.push({
                name: name,
                url: highResUrl,
                productUrl: link.href
            });
        }
    });
    
    return products;
}

async function scrapeAllPages() {
    const allProducts = [];
    
    // Scrape current page
    console.log('Scraping current page...');
    const products = await scrapeProductsFromPage();
    allProducts.push(...products);
    console.log(`Found ${products.length} products on this page`);
    
    // Check if there's a "Load More" button
    const loadMoreBtn = document.querySelector('button:has-text("Load More"), button[aria-label*="Load"]');
    if (loadMoreBtn) {
        console.log('Clicking "Load More" button...');
        loadMoreBtn.click();
        
        // Wait for new products to load
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Recursive call
        const moreProducts = await scrapeAllPages();
        allProducts.push(...moreProducts);
    }
    
    return allProducts;
}

// Export results as JSON
async function exportResults() {
    console.log('Starting scrape...');
    const products = await scrapeAllPages();
    
    // Deduplicate by URL
    const unique = {};
    products.forEach(p => {
        unique[p.url] = p;
    });
    
    const uniqueProducts = Object.values(unique);
    console.log(`\nTotal unique products: ${uniqueProducts.length}`);
    
    // Copy to clipboard
    const json = JSON.stringify(uniqueProducts, null, 2);
    console.log('Results (copy this):');
    console.log(json);
    
    return uniqueProducts;
}

// Run it
exportResults().then(results => {
    console.log('\n=== SCRAPING COMPLETE ===');
    console.log(`Total products scraped: ${results.length}`);
    console.log('\nCopy the JSON above and save it to a file.');
});
