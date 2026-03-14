const fs = require('fs');
const path = require('path');
const { GoogleGenerativeAI } = require('@google/generative-ai');

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || 'AIzaSyBYsAAYh2oP2vQbP2TYOiEBzbv8NusTUIA');

const brandsDir = path.join(__dirname, '../public/brands');
const indexPath = path.join(brandsDir, 'index.json');
const brandIndex = JSON.parse(fs.readFileSync(indexPath, 'utf8'));

// Subcategory reference for prompt
const SUBCATEGORY_MAP = {
  "Women's Shoes": "Ankle Boots | Knee Boots | Over-the-Knee Boots | Combat Boots | Chelsea Boots | Boots | Heels | Pumps | Sandals | Sneakers | Flats | Wedges | Mules | Slippers",
  "Men's Shoes": "Boots | Sneakers | Loafers | Sandals | Oxfords | Dress Shoes | Casual",
  "Kid's Shoes": "Boots | Sneakers | Sandals | Flats | Athletic",
  "Handbags": "Totes | Crossbody | Shoulder Bags | Clutches | Backpacks | Satchels | Wallets | Wristlets",
  "Women's Handbags": "Totes | Crossbody | Shoulder Bags | Clutches | Backpacks | Satchels | Wallets | Wristlets",
  "Women's Accessories": "Sunglasses | Belts | Scarves | Hats | Jewelry | Watches | Gloves",
  "Men's Accessories": "Sunglasses | Belts | Wallets | Watches | Ties | Cufflinks",
  "Women's Clothing": "Dresses | Tops | Bottoms | Sweaters | Jackets | Activewear | Jeans",
  "Men's Clothing": "Shirts | Pants | Jackets | Sweaters | Suits | Casual",
  "Clothing": "Dresses | Tops | Bottoms | Outerwear | Activewear",
};

async function classifyImage(imagePath, productName, category, brandName) {
  try {
    const fullPath = path.join(__dirname, '..', 'public', imagePath);
    const imageBuffer = fs.readFileSync(fullPath);
    const base64Image = imageBuffer.toString('base64');
    
    const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });
    
    const subcategories = SUBCATEGORY_MAP[category] || category;
    
    const prompt = `Look at this product image and classify it.

Product: ${productName}
Brand: ${brandName}
Category: ${category}

Choose ONE subcategory from: ${subcategories}

If none match, return: ${category}

Return ONLY the subcategory name, nothing else.`;

    const result = await model.generateContent([
      prompt,
      {
        inlineData: {
          data: base64Image,
          mimeType: imagePath.endsWith('.png') ? 'image/png' : 'image/jpeg'
        }
      }
    ]);
    
    const response = await result.response;
    const text = response.text().trim();
    
    return text;
    
  } catch (error) {
    console.error(`Error: ${error.message}`);
    return category; // Fallback
  }
}

async function processProducts() {
  const startTime = Date.now();
  let totalProcessed = 0;
  let totalVision = 0;
  
  for (const brand of brandIndex) {
    const brandPath = path.join(brandsDir, `${brand.slug}.json`);
    if (!fs.existsSync(brandPath)) continue;
    
    const products = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
    const needsVision = products.filter(p => p._needsVision).length;
    
    if (needsVision === 0) {
      console.log(`⏭️  ${brand.name}: Already classified (${products.length} products)`);
      continue;
    }
    
    console.log(`\n🔍 ${brand.name}: Processing ${needsVision}/${products.length} products...`);
    
    let processed = 0;
    for (let i = 0; i < products.length; i++) {
      const product = products[i];
      
      if (!product._needsVision) continue;
      
      if (!product.i) {
        product.s = product.c;
        delete product._needsVision;
        continue;
      }
      
      const subcategory = await classifyImage(product.i, product.n, product.c, brand.name);
      product.s = subcategory;
      delete product._needsVision;
      
      processed++;
      totalProcessed++;
      totalVision++;
      
      if (processed % 10 === 0) {
        process.stdout.write(`\r  Progress: ${processed}/${needsVision} (${Math.round(processed/needsVision*100)}%)`);
      }
      
      // Save checkpoint every 50
      if (processed % 50 === 0) {
        fs.writeFileSync(brandPath, JSON.stringify(products, null, 2));
        console.log(` 💾`);
      }
      
      // Small delay to avoid rate limits
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    
    fs.writeFileSync(brandPath, JSON.stringify(products, null, 2));
    console.log(`\r  ✓ ${brand.name}: ${processed} products classified          `);
  }
  
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`\n🎉 Done! ${totalVision} products classified in ${elapsed}s`);
  console.log(`   Average: ${(totalVision / parseFloat(elapsed)).toFixed(1)} products/sec`);
}

processProducts().catch(console.error);
