#!/bin/bash
#
# Download Pandora images from scraped URLs
# Reads from scraped JSON and downloads to match product filenames
#

set -e

PROJECT_DIR="/Users/maurocastellanos/clawd/projects/luxury-catalog-web"
JSON_FILE="$PROJECT_DIR/public/brands/pandora.json"
SCRAPED_FILE="$PROJECT_DIR/pandora_scraped.json"
IMAGE_DIR="$PROJECT_DIR/public/images/pandora"

echo "========================================================================"
echo "PANDORA IMAGE DOWNLOADER"
echo "========================================================================"

mkdir -p "$IMAGE_DIR"

# Count products
TOTAL_PRODUCTS=$(jq 'length' "$JSON_FILE")
TOTAL_SCRAPED=$(jq 'length' "$SCRAPED_FILE")

echo "Products in JSON:     $TOTAL_PRODUCTS"
echo "Scraped image URLs:   $TOTAL_SCRAPED"
echo ""

SUCCESS=0
FAILED=0

# Iterate through products and download
for i in $(seq 0 $((TOTAL_SCRAPED - 1))); do
  # Get image URL from scraped data
  IMAGE_URL=$(jq -r ".[$i].url" "$SCRAPED_FILE")
  
  # Get corresponding product filename from JSON
  if [ "$i" -lt "$TOTAL_PRODUCTS" ]; then
    FILENAME=$(jq -r ".[$i].i" "$JSON_FILE")
    PRODUCT_NAME=$(jq -r ".[$i].n" "$JSON_FILE" | cut -c1-50)
  else
    echo "[$((i+1))/$TOTAL_SCRAPED] Ran out of products in JSON, stopping..."
    break
  fi
  
  if [ "$FILENAME" = "null" ] || [ -z "$FILENAME" ]; then
    echo "[$((i+1))/$TOTAL_SCRAPED] No filename for product, skipping..."
    FAILED=$((FAILED + 1))
    continue
  fi
  
  FULL_PATH="$PROJECT_DIR/public$FILENAME"
  
  echo "[$((i+1))/$TOTAL_SCRAPED] $PRODUCT_NAME..."
  
  # Download
  if curl -s -A "Mozilla/5.0" -m 15 --referer "https://us.pandora.net/" \
          "$IMAGE_URL" -o "$FULL_PATH" 2>/dev/null; then
    
    FILE_SIZE=$(stat -f%z "$FULL_PATH" 2>/dev/null || echo 0)
    
    if [ "$FILE_SIZE" -gt 1000 ]; then
      SUCCESS=$((SUCCESS + 1))
      echo "  ✓ Downloaded ($FILE_SIZE bytes)"
    else
      FAILED=$((FAILED + 1))
      echo "  ✗ File too small ($FILE_SIZE bytes)"
      rm -f "$FULL_PATH"
    fi
  else
    FAILED=$((FAILED + 1))
    echo "  ✗ Download failed"
  fi
  
  sleep 0.2
  
  if [ $((i % 50)) -eq 0 ] && [ "$i" -ne 0 ]; then
    echo ""
    echo "=== Checkpoint: $((i+1)) | Success: $SUCCESS | Failed: $FAILED ==="
    echo ""
  fi
done

echo ""
echo "========================================================================"
echo "DOWNLOAD COMPLETE"
echo "========================================================================"
echo "Successfully downloaded:    $SUCCESS"
echo "Failed:                     $FAILED"
echo "========================================================================"
