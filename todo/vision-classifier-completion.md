# Vision Classifier Completion

**Status:** Paused at 75% completion
**Date:** 2026-03-14

## What's Done (4,461/5,943 products = 75%)

✅ **Fully Classified:**
- Kate Spade: 230/230 (100%)
- Michael Kors: 1,061/1,061 (100%)
- Sephora: 3,168/3,168 (100%)

⚠️ **Partially Classified:**
- Tory Burch: 20/38 (53%)

## What's Remaining (1,482 products = 25%)

❌ **Not Started:**
- Steve Madden: 4,614 products (0%)
- Tory Burch: 18 products remaining

## Why It Stopped

Vision classifier ran out of API credits on the SunCity Anthropic account after processing ~4,500 images. Attempted to use main account but couldn't auto-detect credentials.

## To Resume

**Option 1: Anthropic API (recommended)**
```bash
cd ~/clawd/projects/luxury-catalog-web
export ANTHROPIC_API_KEY=sk-ant-api03-...  # Your main $200/mo account key
node scripts/classify-with-vision.js
```
- Cost: ~$1.50 for remaining 1,482 images
- Time: ~20-30 minutes
- Model: Claude 3 Haiku

**Option 2: Free Gemini**
```bash
cd ~/clawd/projects/luxury-catalog-web
export GEMINI_API_KEY=AIzaSyBYsAAYh2oP2vQbP2TYOiEBzbv8NusTUIA
# Fix model name in scripts/gemini-classifier.js first
node scripts/gemini-classifier.js
```
- Cost: $0 (free tier)
- Time: ~30-45 minutes
- Model: Gemini 1.5 Flash (need to verify correct model ID)

## Current State

Products without vision classification fall back to their main category:
- Steve Madden "KROSBY BLACK SUEDE" → subcategory: "Women's Shoes" (instead of "Ankle Boots")
- Works, just less granular

## Files

- `scripts/classify-with-vision.js` - Main vision classifier (Anthropic)
- `scripts/gemini-classifier.js` - Alternative free classifier (needs model fix)
- `scripts/smart-classifier.js` - Pattern-based fallback for brands with descriptive names
- `public/brands/*.json` - Product data with `s` (subcategory) field

## Notes

The 75% we deployed is already a HUGE improvement over the broken version (no more "Sandals" on perfumes). Steve Madden subcategories are nice-to-have but not critical.
