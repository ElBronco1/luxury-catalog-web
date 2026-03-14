const fs = require('fs');
const path = require('path');
const Anthropic = require('@anthropic-ai/sdk');

// Use the same API key OpenClaw is using (should be the $200/mo account)
const anthropic = new Anthropic();

const brandsDir = path.join(__dirname, '../public/brands');
const indexPath = path.join(brandsDir, 'index.json');
const brandIndex = JSON.parse(fs.readFileSync(indexPath, 'utf8'));

// Image path to base64
function imageToBase64(imagePath) {
  const fullPath = path.join(__dirname, '..', 'public', imagePath);
  const imageBuffer = fs.readFileSync(fullPath);
  return imageBuffer.toString('base64');
}

// Get media type from file extension
function getMediaType(imagePath) {
  const ext = path.extname(imagePath).toLowerCase();
  return ext === '.png' ? 'image/png' : 'image/jpeg';
}

async function classifyProduct(product, brandName) {
  try {
    const imageData = imageToBase64(product.i);
    const mediaType = getMediaType(product.i);
    
    const prompt = `You are a product classifier. Look at this image and classify it into ONE specific subcategory.

Product name: ${product.n}
Brand: ${brandName}
Category: ${product.c}

Return ONLY the subcategory name from this list (choose the MOST specific match):

For Women's Shoes: Ankle Boots, Knee Boots, Over-the-Knee Boots, Combat Boots, Chelsea Boots, Boots, Heels, Sandals, Sneakers, Flats, Wedges, Mules, Slippers
For Men's Shoes: Boots, Sneakers, Loafers, Sandals, Oxfords, Dress Shoes
For Kid's Shoes: Boots, Sneakers, Sandals, Flats
For Handbags: Totes, Crossbody, Shoulder Bags, Clutches, Backpacks, Satchels, Wallets
For Accessories: Sunglasses, Belts, Scarves, Hats, Socks, Jewelry, Watches
For Beauty: Moisturizers, Serums, Cleansers, Toners, Masks, Eye Cream, Sunscreen, Lip Care, Foundation, Concealer, Blush, Highlighter, Bronzer, Eyeshadow, Mascara, Eyeliner, Lipstick, Lip Gloss, Setting Spray, Primer, Shampoo, Conditioner, Hair Mask, Styling, Fragrance
For Charms: Dangle Charms, Clip Charms, Spacer Charms
For Jewelry: Rings, Necklaces, Bracelets, Earrings

If it doesn't fit any subcategory, return: ${product.c}

Return ONLY the subcategory name, nothing else.`;

    const message = await anthropic.messages.create({
      model: 'claude-3-haiku-20240307',
      max_tokens: 50,
      messages: [{
        role: 'user',
        content: [
          {
            type: 'image',
            source: {
              type: 'base64',
              media_type: mediaType,
              data: imageData
            }
          },
          {
            type: 'text',
            text: prompt
          }
        ]
      }]
    });

    const subcategory = message.content[0].text.trim();
    return subcategory;
    
  } catch (error) {
    console.error(`Error classifying ${product.n}:`, error.message);
    return product.c; // Fallback to category
  }
}

async function processProducts() {
  for (const brand of brandIndex) {
    const brandPath = path.join(brandsDir, `${brand.slug}.json`);
    if (!fs.existsSync(brandPath)) continue;
    
    const products = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
    console.log(`\nProcessing ${brand.name}: ${products.length} products...`);
    
    let updated = 0;
    for (let i = 0; i < products.length; i++) {
      const product = products[i];
      
      // Skip if no image
      if (!product.i) {
        product.s = product.c;
        continue;
      }
      
      console.log(`  [${i+1}/${products.length}] Classifying: ${product.n.substring(0, 50)}...`);
      
      const subcategory = await classifyProduct(product, brand.name);
      product.s = subcategory;
      updated++;
      
      // Save after every 10 products to avoid data loss
      if (updated % 10 === 0) {
        fs.writeFileSync(brandPath, JSON.stringify(products, null, 2));
        console.log(`    💾 Saved checkpoint (${updated} done)`);
      }
      
      // No delay - max speed
      // await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    // Final save
    fs.writeFileSync(brandPath, JSON.stringify(products, null, 2));
    console.log(`✓ ${brand.name}: ${updated} products classified\n`);
  }
}

processProducts().catch(console.error);
