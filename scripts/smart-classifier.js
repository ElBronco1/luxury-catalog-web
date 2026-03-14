const fs = require('fs');
const path = require('path');

const brandsDir = path.join(__dirname, '../public/brands');
const indexPath = path.join(brandsDir, 'index.json');
const brandIndex = JSON.parse(fs.readFileSync(indexPath, 'utf8'));

// Brands that need vision (style codes, no descriptive names)
const VISION_BRANDS = ['steve-madden', 'michael-kors', 'coach-outlet', 'kate-spade', 'tory-burch'];

// Pattern-based classification for descriptive brands
const categoryPatterns = {
  "Beauty": {
    'Fragrance': /\b(perfume|cologne|eau de parfum|eau de toilette|fragrance mist)\b/i,
    'Moisturizers': /\b(moisturizer|(?<!fragrance.{0,20})(cream|lotion))\b(?!.*\b(eye|hand|body)\b)/i,
    'Eye Cream': /\b(eye cream|eye gel|eye treatment)\b/i,
    'Hand Cream': /\b(hand cream|hand lotion)\b/i,
    'Serums': /\bserum\b/i,
    'Cleansers': /\b(cleanser|face wash|micellar|cleansing)\b/i,
    'Toners': /\b(toner|essence)\b/i,
    'Masks': /\b(mask|masque)\b/i,
    'Sunscreen': /\b(sunscreen|spf)\b/i,
    'Lip Care': /\b(lip balm|lip treatment|lip care|lip butter)\b/i,
    'Foundation': /\b(foundation|bb cream|cc cream|tinted moisturizer)\b/i,
    'Concealer': /\bconcealer\b/i,
    'Blush': /\bblush\b/i,
    'Highlighter': /\b(highlighter|glow|luminizer)\b/i,
    'Bronzer': /\b(bronzer|contour)\b/i,
    'Eyeshadow': /\b(eyeshadow|eye shadow|palette)\b/i,
    'Mascara': /\bmascara\b/i,
    'Eyeliner': /\b(eyeliner|eye liner|kajal)\b/i,
    'Lipstick': /\blipstick\b/i,
    'Lip Gloss': /\b(lip gloss|lip shine|lip lacquer)\b/i,
    'Lip Liner': /\b(lip liner|lip pencil)\b/i,
    'Setting Spray': /\b(setting spray|fixing spray|mist)\b/i,
    'Primer': /\bprimer\b/i,
    'Powder': /\b(powder|setting powder)\b/i,
    'Shampoo': /\bshampoo\b/i,
    'Conditioner': /\bconditioner\b/i,
    'Hair Mask': /\b(hair mask|hair treatment|deep conditioner)\b/i,
    'Dry Shampoo': /\bdry shampoo\b/i,
    'Styling': /\b(hairspray|mousse|gel|styling|texturizing|volumizing)\b/i,
    'Hair Oil': /\bhair oil\b/i,
  },
  
  "Charms": {
    'Dangle Charms': /\bdangle charm\b/i,
    'Clip Charms': /\bclip charm\b/i,
    'Spacer Charms': /\bspacer\b/i,
  },
  
  "Rings": {
    'Rings': /./i, // All rings are rings
  },
  
  "Necklaces": {
    'Necklaces': /./i,
  },
  
  "Bracelets": {
    'Bracelets': /./i,
  },
  
  "Earrings": {
    'Earrings': /./i,
  },
  
  "Jewelry": {
    'Rings': /\bring\b/i,
    'Necklaces': /\b(necklace|pendant|choker|collier)\b/i,
    'Bracelets': /\b(bracelet|bangle)\b/i,
    'Earrings': /\bearring\b/i,
  },
};

function patternClassify(productName, category) {
  const patterns = categoryPatterns[category];
  if (!patterns) return category;
  
  for (const [subcategory, pattern] of Object.entries(patterns)) {
    if (pattern.test(productName)) {
      return subcategory;
    }
  }
  
  return category;
}

// Process all brands
let stats = {
  pattern: 0,
  vision: 0,
  fallback: 0,
};

brandIndex.forEach(brand => {
  const brandPath = path.join(brandsDir, `${brand.slug}.json`);
  if (!fs.existsSync(brandPath)) return;
  
  const products = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
  const needsVision = VISION_BRANDS.includes(brand.slug);
  
  products.forEach(product => {
    if (needsVision) {
      // Mark for vision processing
      product.s = product.c; // Temporary fallback
      product._needsVision = true;
      stats.vision++;
    } else {
      // Pattern-based
      product.s = patternClassify(product.n, product.c);
      delete product._needsVision;
      stats.pattern++;
    }
  });
  
  fs.writeFileSync(brandPath, JSON.stringify(products, null, 2));
  console.log(`✓ ${brand.name}: ${products.length} products (${needsVision ? 'vision queued' : 'pattern classified'})`);
});

console.log(`\n📊 Summary:`);
console.log(`  Pattern classified: ${stats.pattern.toLocaleString()}`);
console.log(`  Needs vision: ${stats.vision.toLocaleString()}`);
console.log(`\nRun vision classifier next for ${stats.vision} products.`);
