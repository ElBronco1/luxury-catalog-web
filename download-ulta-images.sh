#!/bin/bash

# Batch download Ulta images using direct SKU URLs
# Usage: ./download-ulta-images.sh

JSON_FILE="public/brands/ulta.json"
OUTPUT_DIR="public/images/ulta"
TEMP_JSON="ulta-temp.json"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

echo "Starting Ulta image download..."
echo "Total products: $(jq 'length' $JSON_FILE)"

# Process each product
jq -c '.[] | select(.i == "") | {idx: (input_line_number - 1), n: .n}' $JSON_FILE | while IFS= read -r product; do
  IDX=$(echo "$product" | jq -r '.idx')
  NAME=$(echo "$product" | jq -r '.n')
  
  # Slugify name for filename
  SLUG=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-\|&$//')
  FILENAME="${IDX}-${SLUG}.jpg"
  OUTPUT_PATH="$OUTPUT_DIR/$FILENAME"
  
  # Skip if already exists
  if [ -f "$OUTPUT_PATH" ]; then
    echo "[$IDX] Already exists: $FILENAME"
    continue
  fi
  
  echo "[$IDX] Processing: $NAME"
  
  # We would need SKU here - this is a template
  # For now, skip products without SKU mapping
  echo "  [SKIP] No SKU mapping available"
done

echo "Done!"
