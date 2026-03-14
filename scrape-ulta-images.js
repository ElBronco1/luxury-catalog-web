#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

const JSON_FILE = path.join(__dirname, 'public/brands/ulta.json');
const OUTPUT_DIR = path.join(__dirname, 'public/images/ulta');
const SAVE_INTERVAL = 100; // Save JSON every N images

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Read the JSON
const products = JSON.parse(fs.readFileSync(JSON_FILE, 'utf8'));
console.log(`Loaded ${products.length} products`);

// Filter products without images
const productsWithoutImages = products.map((p, index) => ({ ...p, originalIndex: index }))
  .filter(p => !p.i || p.i === '');

console.log(`Found ${productsWithoutImages.length} products without images`);

// Helper to slugify product name
function slugify(text) {
  return text.toLowerCase()
    .replace(/[^\w\s-]/g, '') // Remove non-word chars
    .replace(/[\s_-]+/g, '-') // Replace spaces/underscores with single dash
    .replace(/^-+|-+$/g, ''); // Trim dashes from edges
}

// Helper to search Ulta for a product and extract image URL
async function searchProductImage(productName) {
  try {
    const searchQuery = encodeURIComponent(productName);
    const searchUrl = `https://www.ulta.com/search?q=${searchQuery}`;
    
    // Use openclaw browser to navigate and extract
    // This is a simplified version - we'll need to implement browser automation
    console.log(`  Searching: ${searchUrl}`);
    
    // For now, return null - we'll implement browser automation separately
    return null;
  } catch (error) {
    console.error(`  Error searching for ${productName}:`, error.message);
    return null;
  }
}

// Helper to download image using curl
async function downloadImage(imageUrl, outputPath) {
  try {
    const command = `curl -s -o "${outputPath}" "${imageUrl}"`;
    await execAsync(command);
    
    // Verify file was created and has content
    const stats = fs.statSync(outputPath);
    if (stats.size < 1000) { // Images should be at least 1KB
      fs.unlinkSync(outputPath);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error(`  Failed to download ${imageUrl}:`, error.message);
    return false;
  }
}

// Main processing function
async function processProducts() {
  let processedCount = 0;
  let successCount = 0;
  
  for (const product of productsWithoutImages) {
    const index = product.originalIndex;
    console.log(`\n[${processedCount + 1}/${productsWithoutImages.length}] Processing: ${product.n}`);
    
    // Try to find image URL
    const imageUrl = await searchProductImage(product.n);
    
    if (imageUrl) {
      const slug = slugify(product.n);
      const filename = `${index}-${slug}.jpg`;
      const outputPath = path.join(OUTPUT_DIR, filename);
      
      console.log(`  Downloading to: ${filename}`);
      const success = await downloadImage(imageUrl, outputPath);
      
      if (success) {
        // Update JSON with image path
        products[index].i = `/images/ulta/${filename}`;
        successCount++;
        console.log(`  ✓ Success`);
      } else {
        console.log(`  ✗ Download failed`);
      }
    } else {
      console.log(`  ✗ No image found`);
    }
    
    processedCount++;
    
    // Save JSON periodically
    if (processedCount % SAVE_INTERVAL === 0) {
      console.log(`\n=== Saving progress (${successCount} images downloaded) ===`);
      fs.writeFileSync(JSON_FILE, JSON.stringify(products, null, 2));
    }
  }
  
  // Final save
  console.log(`\n=== Final save (${successCount} images downloaded) ===`);
  fs.writeFileSync(JSON_FILE, JSON.stringify(products, null, 2));
  
  console.log(`\nDone! Successfully downloaded ${successCount}/${processedCount} images`);
}

// Run if executed directly
if (require.main === module) {
  processProducts().catch(console.error);
}

module.exports = { processProducts, searchProductImage, downloadImage };
