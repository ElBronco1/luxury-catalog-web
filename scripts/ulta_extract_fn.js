// Extract function for browser evaluate - returns name->URL mapping
(() => {
  const cards = document.querySelectorAll('.ProductCard[data-item-id]');
  const r = {};
  for (const c of cards) {
    const id = c.getAttribute('data-item-id');
    const l = c.innerText.split('\n').filter(x => x.trim());
    const n = l[0] || '';
    if (id && n.length > 5) r[n] = `https://media.ultainc.com/i/ulta/${id}?w=600&h=600&fmt=auto`;
  }
  return r;
})()
