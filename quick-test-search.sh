#!/bin/bash

# Test searching Ulta for a product and extracting SKU

PRODUCT_NAME="Do It All Sheer Tint Face Balm"
SEARCH_URL="https://www.ulta.com/search?q=$(echo "$PRODUCT_NAME" | sed 's/ /%20/g')"

echo "Searching for: $PRODUCT_NAME"
echo "URL: $SEARCH_URL"

# Fetch and look for SKU pattern
curl -s "$SEARCH_URL" | grep -oP 'sku=\d+' | head -1

