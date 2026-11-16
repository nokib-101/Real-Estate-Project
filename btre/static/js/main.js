// Footer year
document.querySelectorAll('.year').forEach(el => { el.textContent = new Date().getFullYear(); });

// Toast messages close themselves after a few seconds
document.querySelectorAll('.toast-msg').forEach(toast => {
  const close = () => { toast.classList.add('hide'); setTimeout(() => toast.remove(), 300); };
  toast.querySelector('.btn-close')?.addEventListener('click', close);
  setTimeout(close, 6000);
});

// Swipeable photo strips on listing cards: arrows + dots
document.querySelectorAll('[data-media]').forEach(media => {
  const track = media.querySelector('.media-track');
  const dots = [...media.querySelectorAll('.media-dots span')];
  const go = dir => track.scrollBy({ left: dir * track.clientWidth });
  media.querySelector('.media-nav.prev')?.addEventListener('click', e => { e.preventDefault(); go(-1); });
  media.querySelector('.media-nav.next')?.addEventListener('click', e => { e.preventDefault(); go(1); });
  track.addEventListener('scroll', () => {
    const i = Math.round(track.scrollLeft / track.clientWidth);
    dots.forEach((d, j) => d.classList.toggle('on', i === j));
  }, { passive: true });
});

// Search filters: apply as soon as a select or the price slider changes
document.querySelectorAll('[data-autosubmit]').forEach(form => {
  form.querySelectorAll('select, input[type=range]').forEach(input => {
    input.addEventListener('change', () => form.requestSubmit());
  });
  // A price slider at its maximum means "any price": don't send it
  form.addEventListener('submit', () => {
    form.querySelectorAll('input[type=range]').forEach(r => { r.disabled = +r.value >= +r.max; });
  });
});
const usd = n => '$' + Math.round(n).toLocaleString('en-US');
document.querySelectorAll('[data-range-output]').forEach(range => {
  const out = document.getElementById(range.dataset.rangeOutput);
  const show = () => { out.textContent = +range.value >= +range.max ? 'Any' : usd(range.value); };
  range.addEventListener('input', show);
  show();
});

// Gallery: open the modal carousel at the photo that was clicked
document.querySelectorAll('[data-gallery-index]').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const modal = document.getElementById('galleryModal');
    bootstrap.Carousel.getOrCreateInstance(modal.querySelector('.carousel')).to(+link.dataset.galleryIndex);
    bootstrap.Modal.getOrCreateInstance(modal).show();
  });
});

// Mortgage calculator (monthly principal + interest)
const calc = document.getElementById('mortgage-calc');
if (calc) {
  const $ = id => document.getElementById(id);
  const update = () => {
    const price = +$('calc-price').value || 0;
    const downPct = +$('calc-down').value;
    const rate = +$('calc-rate').value / 100 / 12;
    const months = +$('calc-term').value * 12;
    const loan = price * (1 - downPct / 100);
    const monthly = rate ? loan * rate / (1 - Math.pow(1 + rate, -months)) : loan / months;
    const totalInterest = monthly * months - loan;
    $('calc-down-out').textContent = `${downPct}% (${usd(price * downPct / 100)})`;
    $('calc-monthly').textContent = usd(monthly);
    $('calc-loan').textContent = usd(loan);
    $('calc-interest').textContent = usd(Math.max(totalInterest, 0));
    const principalShare = loan / (loan + Math.max(totalInterest, 0) || 1) * 100;
    $('calc-bar-principal').style.width = principalShare + '%';
  };
  calc.querySelectorAll('input, select').forEach(el => el.addEventListener('input', update));
  update();
}

// Listing map (Leaflet + OpenStreetMap tiles)
const mapEl = document.getElementById('map');
if (mapEl && window.L) {
  // Leaflet guesses its icon folder from its CSS, which fails with hashed
  // static file names, so the icon URLs come from the template instead
  L.Icon.Default.imagePath = '';
  L.Icon.Default.mergeOptions({
    iconUrl: mapEl.dataset.icon, iconRetinaUrl: mapEl.dataset.icon2x, shadowUrl: mapEl.dataset.shadow,
  });
  const pos = [+mapEl.dataset.lat, +mapEl.dataset.lng];
  const map = L.map(mapEl, { scrollWheelZoom: false }).setView(pos, 14);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    // OpenStreetMap's tile policy blocks requests without a Referer, and
    // Django's default Referrer-Policy (same-origin) strips it. Send just
    // the site's origin with tile requests.
    referrerPolicy: 'strict-origin-when-cross-origin',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  L.marker(pos).addTo(map).bindPopup(mapEl.dataset.label);
}
