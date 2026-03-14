// This script will be run externally with browser automation
// It extracts product name -> SKU mappings from Ulta category pages

const extractProducts = () => {
  const products = [];
  const productLinks = document.querySelectorAll('a[href*="/p/"]');
  
  productLinks.forEach(link => {
    const name = link.textContent?.trim();
    const href = link.href;
    const sku = href.match(/sku=(\d+)/)?.[1];
    
    if (name && sku && name.length > 5) {
      products.push({ name, sku, url: href });
    }
  });
  
  // Remove duplicates by SKU
  const unique = [...new Map(products.map(p => [p.sku, p])).values()];
  return unique;
};

// Return the function as string for eval
extractProducts.toString();
