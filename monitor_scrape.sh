#!/bin/bash
cd /Users/maurocastellanos/clawd/projects/luxury-catalog-web

echo "=== Michael Kors Scraper Monitor ==="
echo "Started: $(date)"
echo ""

while true; do
    count=$(ls public/images/michael-kors/ 2>/dev/null | wc -l | xargs)
    size=$(du -sh public/images/michael-kors/ 2>/dev/null | awk '{print $1}')
    percent=$((count * 100 / 1061))
    
    echo "[$(date '+%H:%M:%S')] Downloaded: $count/1061 ($percent%) | Size: $size"
    
    # Check if process is still running
    if ! ps -p 18462 > /dev/null 2>&1; then
        echo ""
        echo "Process finished!"
        echo "Final count: $count images"
        break
    fi
    
    sleep 30
done
