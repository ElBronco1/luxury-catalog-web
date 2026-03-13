const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Create directories
const IMAGES_DIR = path.join(__dirname, '../public/images/pandora');
const OUTPUT_FILE = path.join(__dirname, '../public/brands/pandora-new.json');

if (!fs.existsSync(IMAGES_DIR)) {
  fs.mkdirSync(IMAGES_DIR, { recursive: true });
}

// Download image helper
function downloadImage(url, filepath) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    
    protocol.get(url, (response) => {
      if (response.statusCode === 200) {
        const writeStream = fs.createWriteStream(filepath);
        response.pipe(writeStream);
        
        writeStream.on('finish', () => {
          writeStream.close();
          resolve(filepath);
        });
        
        writeStream.on('error', reject);
      } else {
        reject(new Error(`Failed to download: ${response.statusCode}`));
      }
    }).on('error', reject);
  });
}

// Slugify helper
function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

async function scrapePandora() {
  console.log('🔍 Scraping Pandora products...\n');
  
  // Load the old pandora.json to get image URLs
  const oldData = JSON.parse(
    fs.readFileSync(path.join(__dirname, '../public/brands/pandora.json'), 'utf8')
  );
  
  const products = [];
  let successCount = 0;
  let failCount = 0;
  
  for (let i = 0; i < oldData.length; i++) {
    const product = oldData[i];
    const productSlug = slugify(product.n);
    const imageFilename = `${i + 1}-${productSlug}.jpg`;
    const imagePath = path.join(IMAGES_DIR, imageFilename);
    
    console.log(`[${i + 1}/${oldData.length}] ${product.n}`);
    
    // Check if base64 image exists
    if (product.i && product.i.startsWith('data:image')) {
      try {
        // Extract base64 data
        const base64Data = product.i.split(',')[1];
        const buffer = Buffer.from(base64Data, 'base64');
        
        // Save to file
        fs.writeFileSync(imagePath, buffer);
        
        // Update product with file path
        products.push({
          b: product.b,
          n: product.n,
          c: product.c,
          f: product.f,
          i: `/images/pandora/${imageFilename}`
        });
        
        successCount++;
        console.log(`  ✓ Saved image: ${imageFilename}`);
      } catch (err) {
        console.log(`  ✗ Error: ${err.message}`);
        failCount++;
        
        // Keep product but with placeholder
        products.push({
          b: product.b,
          n: product.n,
          c: product.c,
          f: product.f,
          i: ''
        });
      }
    } else {
      console.log(`  ⊘ No image data`);
      products.push({
        b: product.b,
        n: product.n,
        c: product.c,
        f: product.f,
        i: ''
      });
      failCount++;
    }
    
    // Rate limit: small delay every 10 products
    if ((i + 1) % 10 === 0) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  
  // Save new JSON
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(products, null, 2));
  
  console.log('\n📊 Summary:');
  console.log(`   Total: ${products.length}`);
  console.log(`   Success: ${successCount}`);
  console.log(`   Failed: ${failCount}`);
  console.log(`\n💾 Saved to: ${OUTPUT_FILE}`);
  console.log(`📁 Images in: ${IMAGES_DIR}`);
}

scrapePandora().catch(console.error);
