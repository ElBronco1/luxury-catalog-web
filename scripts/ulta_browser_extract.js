// Extract all products from current Ulta page
(() => {
  const cards = document.querySelectorAll('.ProductCard[data-item-id]');
  const results = {};
  for (const card of cards) {
    const itemId = card.getAttribute('data-item-id');
    const lines = card.innerText.split('\n').filter(l => l.trim());
    // First line is usually the full product name (Brand + Product)
    const fullName = lines[0] || '';
    if (itemId && fullName && fullName.length > 5) {
      results[fullName] = `https://media.ultainc.com/i/ulta/${itemId}?w=600&h=600&fmt=auto`;
    }
  }
  return results;
})()
