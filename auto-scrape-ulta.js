#!/usr/bin/env node

/**
 * Automated Ulta image scraper
 * Uses browser automation to search for each product and extract SKU + image
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

const JSON_FILE = path.join(__dirname, 'public/brands/ulta.json');
const OUTPUT_DIR = path.join(__dirname, 'public/images/ulta');
const PROGRESS_FILE = path.join(__dirname, 'ulta-progress.json');
const SAVE_INTERVAL = 50;

// Load products
const products = JSON.parse(fs.readFileSync(JSON_FILE, 'utf8'));
console.log(`Loaded ${products.length} products`);

// Load progress
let progress = { lastIndex: -1, successCount: 0, failedProducts: [] };
if (fs.existsSync(PROGRESS_FILE)) {
  progress = JSON.parse(fs.readFileSync(PROGRESS_FILE, 'utf8'));
  console.log(`Resuming from index ${progress.lastIndex + 1}`);
}

// Ensure output dir
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

function slugify(text) {
  return text.toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/[\s_-]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

async function downloadImage(sku, outputPath) {
  const urls = [
    `https://media.ulta.com/i/ulta/${sku}?w=600&h=600&fmt=auto`,
    `https://media.ulta.com/i/ulta/${sku}`,
  ];
  
  for (const url of urls) {
    try {
      await execAsync(`curl -s -f -o "${outputPath}" "${url}"`);
      const stats = fs.statSync(outputPath);
      if (stats.size > 1000) return true;
    } catch (e) {
      // Try next URL
    }
  }
  
  if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
  return false;
}

async function searchAndDownload(product, index) {
  const slug = slugify(product.n);
  const filename = `${index}-${slug}.jpg`;
  const outputPath = path.join(OUTPUT_DIR, filename);
  
  // Check if already exists
  if (fs.existsSync(outputPath)) {
    products[index].i = `/images/ulta/${filename}`;
    return { success: true, existing: true };
  }
  
  // This function would need browser automation to:
  // 1. Navigate to https://www.ulta.com/search?q={productName}
  // 2. Extract first result's SKU
  // 3. Download image using SKU
  
  // For now, return placeholder
  console.log(`  Would search for: ${product.n}`);
  return { success: false, reason: 'Browser automation not implemented in this script' };
}

async function processProducts() {
  const startIndex = progress.lastIndex + 1;
  const productsToProcess = products.slice(startIndex).filter(p => !p.i || p.i === '');
  
  console.log(`\nProcessing ${productsToProcess.length} products starting from index ${startIndex}...`);
  
  for (let i = 0; i < productsToProcess.length; i++) {
    const currentIndex = startIndex + i;
    const product = products[currentIndex];
    
    console.log(`\n[${i + 1}/${productsToProcess.length}] Index ${currentIndex}: ${product.n}`);
    
    const result = await searchAndDownload(product, currentIndex);
    
    if (result.success) {
      if (!result.existing) progress.successCount++;
      console.log(result.existing ? '  ⊙ Already exists' : '  ✓ Downloaded');
    } else {
      progress.failedProducts.push({ index: currentIndex, name: product.n, reason: result.reason });
      console.log(`  ✗ Failed: ${result.reason}`);
    }
    
    progress.lastIndex = currentIndex;
    
    // Save progress periodically
    if ((i + 1) % SAVE_INTERVAL === 0) {
      console.log(`\n=== Saving progress ===`);
      fs.writeFileSync(JSON_FILE, JSON.stringify(products, null, 2));
      fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
    }
    
    // Small delay
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  
  // Final save
  console.log(`\n=== Final save ===`);
  fs.writeFileSync(JSON_FILE, JSON.stringify(products, null, 2));
  fs.writeFileSync(PROGRESS_FILE, JSON.stringify(progress, null, 2));
  
  console.log(`\nDone!`);
  console.log(`  Success: ${progress.successCount}`);
  console.log(`  Failed: ${progress.failedProducts.length}`);
}

// Main
if (require.main === module) {
  console.log('\n⚠️  This script requires browser automation to be fully functional.');
  console.log('The actual scraping needs to be done via OpenClaw browser tool.\n');
  
  // processProducts().catch(console.error);
}

module.exports = { searchAndDownload, downloadImage, slugify };
