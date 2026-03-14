#!/bin/bash
#
# Simple Pandora image scraper
# Uses curl to fetch HTML and grep to extract image URLs
#

set -e

PROJECT_DIR="/Users/maurocastellanos/clawd/projects/luxury-catalog-web"
JSON_FILE="$PROJECT_DIR/public/brands/pandora.json"
IMAGE_DIR="$PROJECT_DIR/public/images/pandora"
OUTPUT_FILE="$PROJECT_DIR/pandora_image_urls.txt"

echo "========================================================================"
echo "PANDORA IMAGE SCRAPER"
echo "========================================================================"

# Create image directory
mkdir -p "$IMAGE_DIR"

# Categories to scrape
CATEGORIES=(
  "https://us.pandora.net/en/jewelry/charms/"
  "https://us.pandora.net/en/jewelry/bracelets/"
  "https://us.pandora.net/en/jewelry/rings/"
  "https://us.pandora.net/en/jewelry/necklaces/"
  "https://us.pandora.net/en/jewelry/earrings/"
)

echo ""
echo "[1/3] Scraping category pages for image URLs..."
> "$OUTPUT_FILE"  # Clear output file

for URL in "${CATEGORIES[@]}"; do
  echo "  Fetching: $URL"
  
  # Fetch page and extract image URLs
  curl -s -A "Mozilla/5.0" "$URL" | \
    grep -oE 'https://[^"]+/dw/image/v2/AAVX_PRD/[^"]+\.(jpg|png)' | \
    sed 's/\\?sw=[0-9]\+/?sw=600/' | \
    sed 's/&sh=[0-9]\+/\&sh=600/' | \
    sort -u >> "$OUTPUT_FILE"
  
  sleep 1  # Rate limiting
done

# Deduplicate all URLs
sort -u "$OUTPUT_FILE" -o "$OUTPUT_FILE"

TOTAL_URLS=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')
echo "  Total unique image URLs found: $TOTAL_URLS"

# Get count of products in JSON
TOTAL_PRODUCTS=$(jq 'length' "$JSON_FILE")
echo "  Total products in JSON: $TOTAL_PRODUCTS"

echo ""
echo "[2/3] Downloading images..."

COUNTER=0
SUCCESS=0
FAILED=0

# Read image URLs and download them
while IFS= read -r IMAGE_URL; do
  COUNTER=$((COUNTER + 1))
  
  # Generate filename from counter (matching JSON order)
  FILENAME=$(jq -r ".[$((COUNTER - 1))].i" "$JSON_FILE")
  
  if [ "$FILENAME" = "null" ] || [ -z "$FILENAME" ]; then
    echo "  [$COUNTER/$TOTAL_URLS] No filename for index $((COUNTER - 1)), skipping..."
    FAILED=$((FAILED + 1))
    continue
  fi
  
  FULL_PATH="$PROJECT_DIR/public$FILENAME"
  PRODUCT_NAME=$(jq -r ".[$((COUNTER - 1))].n" "$JSON_FILE" | cut -c1-50)
  
  echo "  [$COUNTER/$TOTAL_URLS] $PRODUCT_NAME..."
  echo "      URL: $IMAGE_URL"
  
  # Download with curl
  if curl -s -A "Mozilla/5.0" -m 15 --referer "https://us.pandora.net/" \
          "$IMAGE_URL" -o "$FULL_PATH" 2>/dev/null; then
    
    # Check if downloaded file is valid (>1KB)
    FILE_SIZE=$(stat -f%z "$FULL_PATH" 2>/dev/null || echo 0)
    
    if [ "$FILE_SIZE" -gt 1000 ]; then
      SUCCESS=$((SUCCESS + 1))
      echo "      ✓ Downloaded ($FILE_SIZE bytes)"
    else
      FAILED=$((FAILED + 1))
      echo "      ✗ Failed (file too small: $FILE_SIZE bytes)"
      rm -f "$FULL_PATH"
    fi
  else
    FAILED=$((FAILED + 1))
    echo "      ✗ Failed to download"
  fi
  
  # Rate limiting
  sleep 0.3
  
  # Progress checkpoint
  if [ $((COUNTER % 50)) -eq 0 ]; then
    echo ""
    echo "  === Checkpoint: $COUNTER | Success: $SUCCESS | Failed: $FAILED ==="
    echo ""
  fi
  
  # Limit to available URLs
  if [ "$COUNTER" -ge "$TOTAL_URLS" ]; then
    break
  fi
done < "$OUTPUT_FILE"

echo ""
echo "========================================================================"
echo "SCRAPING COMPLETE"
echo "========================================================================"
echo "Total products in JSON:     $TOTAL_PRODUCTS"
echo "Image URLs scraped:         $TOTAL_URLS"
echo "Successfully downloaded:    $SUCCESS"
echo "Failed:                     $FAILED"
echo "========================================================================"
