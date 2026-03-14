#!/usr/bin/env node
// Helper script to extract SKU mappings from currently open browser pages

const extractSKUs = `
(() => {
  const products = [];
  const productLinks = document.querySelectorAll('a[href*="/p/"]');
  
  productLinks.forEach(link => {
    const name = link.textContent?.trim();
    const href = link.href;
    const sku = href.match(/sku=(\\d+)/)?.[1];
    
    if (name && sku && name.length > 5 && !name.includes('\\n')) {
      products.push({ name, sku });
    }
  });
  
  return [...new Map(products.map(p => [p.sku, p])).values()];
})()
`;

console.log(extractSKUs);
