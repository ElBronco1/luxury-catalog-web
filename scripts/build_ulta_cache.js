// This JavaScript runs in the browser context to extract all products from a page
(function() {
  const cards = document.querySelectorAll('.ProductCard[data-item-id]');
  const results = [];
  for (const card of cards) {
    const itemId = card.getAttribute('data-item-id');
    const lines = card.innerText.split('\n').filter(l => l.trim());
    const fullName = lines[0] || '';
    if (itemId && fullName && fullName.length > 3) {
      results.push({
        id: itemId,
        name: fullName,
        url: `https://media.ultainc.com/i/ulta/${itemId}?w=600&h=600&fmt=auto`
      });
    }
  }
  return results;
})();
