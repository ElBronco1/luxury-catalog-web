/**
 * Scrape Pandora product images using Playwright
 * Systematically goes through category pages and downloads high-res images
 */

const { chromium } = require('playwright');
const fs = require('fs').promises;
const path = require('path');
const https = require('https');

const JSON_FILE = './public/brands/pandora.json';
const IMAGE_DIR = './public/images/pandora';
const BASE_URL = 'https://us.pandora.net';

// Category URLs to scrape
const CATEGORIES = [
  '/en/jewelry/charms/',
  '/en/jewelry/bracelets/',
  '/en/jewelry/rings/',
  '/en/jewelry/necklaces/',
  '/en/jewelry/earrings/',
];

/**
 * Download image from URL to file
 */
async function downloadImage(url, filepath) {
  return new Promise((resolve, reject) => {
    const file = require('fs').createWriteStream(filepath);
    
    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`HTTP ${response.statusCode}`));
        return;
      }
      
      response.pipe(file);
      
      file.on('finish', () => {
        file.close();
        resolve(true);
      });
    }).on('error', (err) => {
      require('fs').unlink(filepath, () => {});
      reject(err);
    });
  });
}

/**
 * Scrape products from a single category page
 */
async function scrapeCategoryPage(page, categoryUrl) {
  console.log(`\n📍 Navigating to: ${categoryUrl}`);
  await page.goto(BASE_URL + categoryUrl, { waitUntil: 'networkidle' });
  
  // Wait for products to load
  await page.waitForSelector('img[src*="/dw/image/"]', { timeout: 10000 });
  
  const products = [];
  let loadMoreClicks = 0;
  const maxLoadMore = 50; // Load up to 50 pages of products
  
  while (loadMoreClicks < maxLoadMore) {
    // Extract products currently visible
    const currentProducts = await page.evaluate(() => {
      const items = [];
      
      // Find all product images
      const images = document.querySelectorAll('img[src*="/dw/image/"]');
      
      images.forEach(img => {
        if (!img.src.includes('pandora.net')) return;
        
        // Get product container
        const container = img.closest('a');
        if (!container) return;
        
        // Extract name from paragraphs
        let name = '';
        const paragraphs = Array.from(container.querySelectorAll('p'));
        
        for (const p of paragraphs) {
          const text = p.textContent.trim();
          // Skip labels, prices, and badges
          if (text.includes('$') || text.includes('NEW') || text.includes('BEST SELLER') || text.length < 5) {
            continue;
          }
          if (text.length > 10 && !name) {
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
        
        if (name && img.src) {
          // Upgrade to 600x600
          const highResUrl = img.src
            .replace(/\?sw=\d+/, '?sw=600')
            .replace(/&sh=\d+/, '&sh=600');
          
          items.push({
            name: name.trim(),
            url: highResUrl
          });
        }
      });
      
      return items;
    });
    
    console.log(`   Found ${currentProducts.length} products on current page`);
    products.push(...currentProducts);
    
    // Try to click "Load More"
    const loadMoreButton = await page.$('button:has-text("Load More")');
    if (loadMoreButton) {
      console.log(`   Clicking "Load More" (${loadMoreClicks + 1})...`);
      await loadMoreButton.click();
      await page.waitForTimeout(2000); // Wait for new products to load
      loadMoreClicks++;
    } else {
      console.log(`   No more "Load More" button found`);
      break;
    }
  }
  
  // Deduplicate by URL
  const uniqueProducts = Array.from(
    new Map(products.map(p => [p.url, p])).values()
  );
  
  console.log(`   ✓ Total unique products: ${uniqueProducts.length}`);
  return uniqueProducts;
}

/**
 * Main scraping function
 */
async function main() {
  console.log('='.repeat(70));
  console.log('PANDORA IMAGE SCRAPER (Playwright)');
  console.log('='.repeat(70));
  
  // Load products from JSON
  console.log('\n[1/4] Loading products from JSON...');
  const jsonData = await fs.readFile(JSON_FILE, 'utf-8');
  const products = JSON.parse(jsonData);
  console.log(`      Loaded ${products.length} products`);
  
  // Launch browser
  console.log('\n[2/4] Launching browser...');
  const browser = await chromium.launch({ headless: false }); // Use headless: true for production
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
  });
  const page = await context.newPage();
  
  // Scrape all categories
  console.log('\n[3/4] Scraping category pages...');
  const allScrapedProducts = [];
  
  for (const categoryUrl of CATEGORIES) {
    try {
      const categoryProducts = await scrapeCategoryPage(page, categoryUrl);
      allScrapedProducts.push(...categoryProducts);
      await page.waitForTimeout(1000); // Rate limiting
    } catch (error) {
      console.error(`   ✗ Error scraping ${categoryUrl}: ${error.message}`);
    }
  }
  
  await browser.close();
  
  // Deduplicate all products
  const uniqueScraped = Array.from(
    new Map(allScrapedProducts.map(p => [p.url, p])).values()
  );
  
  console.log(`\n   Total unique products scraped: ${uniqueScraped.length}`);
  
  // Download images
  console.log('\n[4/4] Downloading images...');
  
  let successful = 0;
  let failed = 0;
  
  // Match scraped products to JSON products and download
  for (let i = 0; i < Math.min(products.length, uniqueScraped.length); i++) {
    const product = products[i];
    const scraped = uniqueScraped[i];
    
    const imagePath = product.i;
    const fullPath = path.join(__dirname, 'public', imagePath);
    
    console.log(`\n      [${i + 1}/${Math.min(products.length, uniqueScraped.length)}] ${product.n.substring(0, 50)}...`);
    console.log(`      URL: ${scraped.url}`);
    
    try {
      await downloadImage(scraped.url, fullPath);
      successful++;
      console.log(`      ✓ Downloaded`);
    } catch (error) {
      failed++;
      console.log(`      ✗ Failed: ${error.message}`);
    }
    
    // Rate limiting
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // Progress checkpoint
    if ((i + 1) % 50 === 0) {
      console.log(`\n      === Checkpoint: ${i + 1} | Success: ${successful} | Failed: ${failed} ===\n`);
    }
  }
  
  console.log('\n' + '='.repeat(70));
  console.log('SCRAPING COMPLETE');
  console.log('='.repeat(70));
  console.log(`Total products in JSON:       ${products.length}`);
  console.log(`Total scraped image URLs:     ${uniqueScraped.length}`);
  console.log(`Successfully downloaded:      ${successful}`);
  console.log(`Failed:                       ${failed}`);
  console.log('='.repeat(70));
}

main().catch(console.error);
