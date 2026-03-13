const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Brand configurations
const BRANDS = [
  { name: 'Steve Madden', slug: 'steve-madden' },
  { name: 'Sephora', slug: 'sephora' },
  { name: 'Michael Kors', slug: 'michael-kors' },
  { name: 'Coach', slug: 'coach' },
  { name: 'Kate Spade', slug: 'kate-spade' },
  { name: 'Tory Burch', slug: 'tory-burch' },
  { name: 'Calvin Klein', slug: 'calvin-klein' },
  { name: 'Tommy Hilfiger', slug: 'tommy-hilfiger' },
  { name: 'Lululemon', slug: 'lululemon' },
  { name: "Victoria's Secret", slug: 'victorias-secret' },
  { name: 'Ulta', slug: 'ulta' }
];

const BASE_DIR = path.join(__dirname, '..');
const BRANDS_DIR = path.join(BASE_DIR, 'public/brands');
const IMAGES_BASE = path.join(BASE_DIR, 'public/images');

// Download image from URL
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
      } else if (response.statusCode === 301 || response.statusCode === 302) {
        // Handle redirects
        const redirectUrl = response.headers.location;
        downloadImage(redirectUrl, filepath).then(resolve).catch(reject);
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
    .replace(/^-|-$/g, '')
    .substring(0, 100); // Limit length for filesystem
}

// Process a single brand
async function processBrand(brand) {
  console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`📦 Processing: ${brand.name}`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
  
  // Create image directory
  const imageDir = path.join(IMAGES_BASE, brand.slug);
  if (!fs.existsSync(imageDir)) {
    fs.mkdirSync(imageDir, { recursive: true });
  }
  
  // Load brand data
  const brandFile = path.join(BRANDS_DIR, `${brand.slug}.json`);
  if (!fs.existsSync(brandFile)) {
    console.log(`⊘ File not found: ${brandFile}`);
    return { brand: brand.name, success: 0, failed: 0, skipped: 0 };
  }
  
  const products = JSON.parse(fs.readFileSync(brandFile, 'utf8'));
  const updatedProducts = [];
  
  let successCount = 0;
  let failCount = 0;
  let skippedCount = 0;
  
  for (let i = 0; i < products.length; i++) {
    const product = products[i];
    const productSlug = slugify(product.n || product.name || 'product');
    const imageFilename = `${i + 1}-${productSlug}.jpg`;
    const imagePath = path.join(imageDir, imageFilename);
    
    // Progress indicator
    if ((i + 1) % 100 === 0 || i === 0) {
      console.log(`[${i + 1}/${products.length}] ${product.n || product.name}`);
    }
    
    const imageData = product.i || product.image;
    
    // Skip if no image data
    if (!imageData || imageData === '') {
      updatedProducts.push({
        ...product,
        i: ''
      });
      skippedCount++;
      continue;
    }
    
    try {
      // Case 1: Base64 data URI
      if (imageData.startsWith('data:image')) {
        const base64Data = imageData.split(',')[1];
        const buffer = Buffer.from(base64Data, 'base64');
        fs.writeFileSync(imagePath, buffer);
        
        updatedProducts.push({
          ...product,
          i: `/images/${brand.slug}/${imageFilename}`
        });
        successCount++;
      }
      // Case 2: HTTP/HTTPS URL
      else if (imageData.startsWith('http://') || imageData.startsWith('https://')) {
        await downloadImage(imageData, imagePath);
        
        updatedProducts.push({
          ...product,
          i: `/images/${brand.slug}/${imageFilename}`
        });
        successCount++;
      }
      // Case 3: Already a local path
      else if (imageData.startsWith('/images/')) {
        updatedProducts.push(product);
        skippedCount++;
      }
      // Case 4: Unknown format
      else {
        updatedProducts.push({
          ...product,
          i: ''
        });
        failCount++;
      }
    } catch (err) {
      console.log(`  ✗ Error on product ${i + 1}: ${err.message}`);
      updatedProducts.push({
        ...product,
        i: ''
      });
      failCount++;
    }
    
    // Rate limit: small delay every 50 images
    if ((i + 1) % 50 === 0) {
      await new Promise(resolve => setTimeout(resolve, 200));
    }
  }
  
  // Save updated JSON
  const outputFile = path.join(BRANDS_DIR, `${brand.slug}-new.json`);
  fs.writeFileSync(outputFile, JSON.stringify(updatedProducts, null, 2));
  
  console.log(`\n📊 ${brand.name} Summary:`);
  console.log(`   Total: ${products.length}`);
  console.log(`   Success: ${successCount}`);
  console.log(`   Failed: ${failCount}`);
  console.log(`   Skipped: ${skippedCount}`);
  console.log(`\n💾 Saved to: ${outputFile}`);
  console.log(`📁 Images in: ${imageDir}`);
  
  return {
    brand: brand.name,
    total: products.length,
    success: successCount,
    failed: failCount,
    skipped: skippedCount
  };
}

// Main execution
async function main() {
  console.log('🚀 Starting image extraction for all brands...\n');
  
  const results = [];
  
  for (const brand of BRANDS) {
    const result = await processBrand(brand);
    results.push(result);
  }
  
  // Summary report
  console.log('\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('📈 FINAL SUMMARY');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
  
  results.forEach(r => {
    console.log(`${r.brand}:`);
    console.log(`  Total: ${r.total} | Success: ${r.success} | Failed: ${r.failed} | Skipped: ${r.skipped}`);
  });
  
  const totalSuccess = results.reduce((sum, r) => sum + r.success, 0);
  const totalFailed = results.reduce((sum, r) => sum + r.failed, 0);
  const totalProducts = results.reduce((sum, r) => sum + r.total, 0);
  
  console.log(`\n✅ Total extracted: ${totalSuccess}/${totalProducts} images`);
  console.log(`❌ Total failed: ${totalFailed}`);
  
  console.log('\n🔄 Next steps:');
  console.log('   1. Review the *-new.json files');
  console.log('   2. Replace old JSON files: mv brand-new.json brand.json');
  console.log('   3. Rebuild and redeploy');
}

main().catch(console.error);
