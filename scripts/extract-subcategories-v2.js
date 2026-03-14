const fs = require('fs');
const path = require('path');

const brandsDir = path.join(__dirname, '../public/brands');
const indexPath = path.join(brandsDir, 'index.json');
const brandIndex = JSON.parse(fs.readFileSync(indexPath, 'utf8'));

// Category-specific subcategory patterns
// Only match within the correct parent category
const categoryPatterns = {
  "Women's Shoes": {
    'Ankle Boots': /\bankle boot|bootie\b/i,
    'Knee Boots': /\bknee boot|tall boot\b/i,
    'Over-the-Knee Boots': /over[-\s]?the[-\s]?knee|otk boot/i,
    'Combat Boots': /combat boot|lug boot/i,
    'Chelsea Boots': /chelsea boot/i,
    'Boots': /\bboot\b/i,
    'Heels': /\bheel|pump|stiletto\b/i,
    'Sandals': /\bsandal\b(?!wood)/i, // exclude sandalwood
    'Sneakers': /\bsneaker|trainer|tennis shoe|athletic\b/i,
    'Flats': /\bflat|ballet|loafer\b/i,
    'Wedges': /\bwedge\b/i,
    'Mules': /\bmule|clog\b/i,
    'Slippers': /\bslipper\b/i,
  },
  
  "Men's Shoes": {
    'Boots': /\bboot\b/i,
    'Sneakers': /\bsneaker|trainer|athletic\b/i,
    'Loafers': /\bloafer\b/i,
    'Sandals': /\bsandal\b(?!wood)/i,
    'Oxfords': /\boxford|derby\b/i,
  },
  
  "Kid's Shoes": {
    'Boots': /\bboot\b/i,
    'Sneakers': /\bsneaker|trainer\b/i,
    'Sandals': /\bsandal\b(?!wood)/i,
    'Flats': /\bflat|ballet\b/i,
  },
  
  "Handbags": {
    'Totes': /\btote\b/i,
    'Crossbody': /crossbody|cross.?body/i,
    'Shoulder Bags': /shoulder bag/i,
    'Clutches': /\bclutch\b/i,
    'Backpacks': /\bbackpack|rucksack\b/i,
    'Satchels': /\bsatchel\b/i,
    'Wallets': /\bwallet|card.?holder|coin.?purse\b/i,
  },
  
  "Accessories": {
    'Sunglasses': /\bsunglasses|sunnies\b/i,
    'Belts': /\bbelt\b/i,
    'Scarves': /\bscarf|scarves\b/i,
    'Hats': /\bhat|beanie|cap\b/i,
    'Socks': /\bsock|tight|hosiery\b/i,
    'Jewelry - Earrings': /\bearring\b/i,
    'Jewelry - Necklaces': /\bnecklace|pendant\b/i,
    'Jewelry - Bracelets': /\bbracelet|bangle\b/i,
    'Jewelry - Rings': /\bring(?!let)\b/i,
    'Jewelry - Anklets': /\banklet\b/i,
    'Watches': /\bwatch\b(?! ring)/i,
  },
  
  "Beauty": {
    'Moisturizers': /moisturizer|cream(?! blush)|lotion/i,
    'Serums': /\bserum\b/i,
    'Cleansers': /cleanser|\bwash\b|micellar/i,
    'Toners': /\btoner|essence\b/i,
    'Masks': /\bmask\b/i,
    'Eye Cream': /eye cream|eye gel/i,
    'Sunscreen': /sunscreen|spf/i,
    'Lip Care': /lip balm|lip treatment|lip care/i,
    'Foundation': /foundation|bb cream|cc cream/i,
    'Concealer': /concealer/i,
    'Blush': /\bblush\b/i,
    'Highlighter': /highlighter|\bglow\b/i,
    'Bronzer': /bronzer|contour/i,
    'Eyeshadow': /eyeshadow|eye shadow|palette/i,
    'Mascara': /mascara/i,
    'Eyeliner': /eyeliner|eye liner/i,
    'Lipstick': /lipstick/i,
    'Lip Gloss': /lip gloss|lip shine/i,
    'Setting Spray': /setting spray|fixing spray/i,
    'Primer': /\bprimer\b/i,
    'Shampoo': /shampoo/i,
    'Conditioner': /conditioner/i,
    'Hair Mask': /hair mask|hair treatment/i,
    'Styling': /styling|hairspray|gel|mousse/i,
    'Fragrance': /perfume|cologne|eau de|fragrance/i,
  },
  
  "Women's Clothing": {
    'Dresses': /\bdress\b(?!ing)/i,
    'Tops': /\btop|blouse|shirt|tee\b(?!th)/i,
    'Bottoms': /\bpant|jean|skirt|short\b/i,
    'Sweaters': /sweater|cardigan|knit/i,
    'Jackets': /jacket|coat|blazer/i,
    'Activewear': /athletic|yoga|sports.?bra|legging/i,
  },
  
  "Charms": {
    'Dangle Charms': /dangle charm/i,
    'Clip Charms': /clip charm/i,
    'Spacer Charms': /spacer/i,
  },
  
  "Jewelry": {
    'Rings': /\bring\b/i,
    'Necklaces': /necklace|pendant/i,
    'Bracelets': /bracelet|bangle/i,
    'Earrings': /earring/i,
  },
  
  "Sale": {
    // Keep as "Sale" - no subcategories
  },
  
  "Gift Cards": {
    // Keep as "Gift Cards"
  },
  
  "Bundle": {
    // Keep as "Bundle"
  },
  
  "Unknown": {
    // Keep as "Unknown"
  },
};

function extractSubcategory(productName, category) {
  // Get patterns for this category
  const patterns = categoryPatterns[category];
  
  // If no patterns defined, return category as subcategory
  if (!patterns) {
    return category;
  }
  
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
let errorLog = [];

brandIndex.forEach(brand => {
  const brandPath = path.join(brandsDir, `${brand.slug}.json`);
  if (!fs.existsSync(brandPath)) return;
  
  const products = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
  
  products.forEach((product, idx) => {
    const subcategory = extractSubcategory(product.n, product.c);
    product.s = subcategory; // Add subcategory field
    
    // Track stats
    const key = `${brand.name} > ${product.c} > ${subcategory}`;
    subcategoryStats[key] = (subcategoryStats[key] || 0) + 1;
    
    // Log suspicious matches (sandalwood → sandals, etc.)
    if (subcategory === 'Sandals' && /sandalwood/i.test(product.n)) {
      errorLog.push(`SANDALWOOD BUG: ${brand.name} | ${product.n} → ${subcategory}`);
    }
    
    totalUpdated++;
  });
  
  // Write updated file
  fs.writeFileSync(brandPath, JSON.stringify(products, null, 2));
  console.log(`✓ Updated ${brand.name}: ${products.length} products`);
});

// Print summary
console.log(`\n✅ Total products updated: ${totalUpdated.toLocaleString()}`);

if (errorLog.length > 0) {
  console.log(`\n❌ Errors found: ${errorLog.length}`);
  errorLog.slice(0, 10).forEach(err => console.log(`  ${err}`));
}

console.log(`\nTop 50 subcategories:`);
Object.entries(subcategoryStats)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 50)
  .forEach(([key, count]) => {
    console.log(`  ${key}: ${count}`);
  });
