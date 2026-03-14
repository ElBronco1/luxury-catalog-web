const fs = require('fs');
const path = require('path');

const brandsDir = path.join(__dirname, '../public/brands');
const indexPath = path.join(brandsDir, 'index.json');
const brandIndex = JSON.parse(fs.readFileSync(indexPath, 'utf8'));

// Subcategory patterns (order matters - check specific before general)
const patterns = {
  // Shoes
  'Ankle Boots': /ankle boot|bootie/i,
  'Knee Boots': /knee boot|tall boot/i,
  'Over-the-Knee Boots': /over[-\s]?the[-\s]?knee|otk boot/i,
  'Combat Boots': /combat boot|lug boot/i,
  'Chelsea Boots': /chelsea boot/i,
  'Boots': /boot/i,
  'Heels': /heel|pump|stiletto/i,
  'Sandals': /sandal|slide|flip.?flop/i,
  'Sneakers': /sneaker|trainer|tennis shoe|athletic/i,
  'Flats': /flat|ballet|loafer/i,
  'Wedges': /wedge/i,
  'Mules': /mule|clog/i,
  'Slippers': /slipper/i,
  
  // Handbags
  'Totes': /tote/i,
  'Crossbody': /crossbody|cross.?body/i,
  'Shoulder Bags': /shoulder bag/i,
  'Clutches': /clutch/i,
  'Backpacks': /backpack|rucksack/i,
  'Satchels': /satchel/i,
  'Wallets': /wallet|card.?holder|coin.?purse/i,
  
  // Accessories
  'Sunglasses': /sunglasses|sunnies/i,
  'Belts': /belt/i,
  'Scarves': /scarf|scarves/i,
  'Hats': /hat|beanie|cap/i,
  'Socks': /sock|tight|hosiery/i,
  'Jewelry - Earrings': /earring/i,
  'Jewelry - Necklaces': /necklace|pendant/i,
  'Jewelry - Bracelets': /bracelet|bangle/i,
  'Jewelry - Rings': /ring(?!let)/i,
  'Jewelry - Anklets': /anklet/i,
  'Watches': /watch(?! ring)/i,
  
  // Beauty - Skincare
  'Moisturizers': /moisturizer|cream(?! blush)|lotion/i,
  'Serums': /serum/i,
  'Cleansers': /cleanser|wash|micellar/i,
  'Toners': /toner|essence/i,
  'Masks': /mask/i,
  'Eye Cream': /eye cream|eye gel/i,
  'Sunscreen': /sunscreen|spf/i,
  'Lip Care': /lip balm|lip treatment|lip care/i,
  
  // Beauty - Makeup
  'Foundation': /foundation|bb cream|cc cream/i,
  'Concealer': /concealer/i,
  'Blush': /blush/i,
  'Highlighter': /highlighter|glow/i,
  'Bronzer': /bronzer|contour/i,
  'Eyeshadow': /eyeshadow|eye shadow|palette/i,
  'Mascara': /mascara/i,
  'Eyeliner': /eyeliner|eye liner/i,
  'Lipstick': /lipstick/i,
  'Lip Gloss': /lip gloss|lip shine/i,
  'Setting Spray': /setting spray|fixing spray/i,
  'Primer': /primer/i,
  
  // Clothing
  'Dresses': /dress(?!ing)/i,
  'Tops': /top|blouse|shirt|tee(?!th)/i,
  'Bottoms': /pant|jean|skirt|short/i,
  'Sweaters': /sweater|cardigan|knit/i,
  'Jackets': /jacket|coat|blazer/i,
  'Activewear': /athletic|yoga|sports.?bra|legging/i,
};

function extractSubcategory(productName, category) {
  // Check patterns in order
  for (const [subcategory, pattern] of Object.entries(patterns)) {
    if (pattern.test(productName)) {
      return subcategory;
    }
  }
  
  // Fallback to category if no pattern matches
  return category;
}

// Process all brands
let totalUpdated = 0;
let subcategoryStats = {};

brandIndex.forEach(brand => {
  const brandPath = path.join(brandsDir, `${brand.slug}.json`);
  if (!fs.existsSync(brandPath)) return;
  
  const products = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
  
  products.forEach(product => {
    const subcategory = extractSubcategory(product.n, product.c);
    product.s = subcategory; // Add subcategory field
    
    // Track stats
    const key = `${brand.name} > ${subcategory}`;
    subcategoryStats[key] = (subcategoryStats[key] || 0) + 1;
    totalUpdated++;
  });
  
  // Write updated file
  fs.writeFileSync(brandPath, JSON.stringify(products, null, 2));
  console.log(`✓ Updated ${brand.name}: ${products.length} products`);
});

// Print summary
console.log(`\n✅ Total products updated: ${totalUpdated.toLocaleString()}`);
console.log(`\nTop 30 subcategories:`);

Object.entries(subcategoryStats)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 30)
  .forEach(([key, count]) => {
    console.log(`  ${key}: ${count}`);
  });
