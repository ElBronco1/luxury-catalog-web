const fs = require('fs');
const path = require('path');

const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/ElBronco1/luxury-catalog-web/main';
const BRANDS_DIR = path.join(__dirname, '../public/brands');

// Get all brand JSON files
const brandFiles = fs.readdirSync(BRANDS_DIR).filter(f => f.endsWith('.json') && f !== 'index.json');

console.log(`Updating ${brandFiles.length} brand files to use GitHub CDN URLs...\n`);

brandFiles.forEach(file => {
  const filePath = path.join(BRANDS_DIR, file);
  const products = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  
  let updated = 0;
  products.forEach(product => {
    if (product.i && product.i.startsWith('/images/')) {
      product.i = `${GITHUB_RAW_BASE}${product.i}`;
      updated++;
    }
  });
  
  fs.writeFileSync(filePath, JSON.stringify(products, null, 2));
  console.log(`✓ ${file}: Updated ${updated} image URLs`);
});

console.log('\n✅ All brand files updated!');
