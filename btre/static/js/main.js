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

// Ask before destructive actions (e.g. deleting a listing)
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', e => { if (!confirm(form.dataset.confirm)) e.preventDefault(); });
});

// Listing form: click the map to set latitude/longitude
const picker = document.querySelector('[data-map-picker]');
if (picker && window.L) {
  L.Icon.Default.imagePath = '';
  L.Icon.Default.mergeOptions({
    iconUrl: picker.dataset.icon, iconRetinaUrl: picker.dataset.icon2x, shadowUrl: picker.dataset.shadow,
  });
  const latInput = document.getElementById('id_latitude');
  const lngInput = document.getElementById('id_longitude');
  const start = latInput.value && lngInput.value ? [+latInput.value, +lngInput.value] : null;
  const map = L.map(picker).setView(start || [39.5, -98.35], start ? 15 : 4);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    referrerPolicy: 'strict-origin-when-cross-origin',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);
  let marker = start ? L.marker(start).addTo(map) : null;
  const place = latlng => {
    marker = marker ? marker.setLatLng(latlng) : L.marker(latlng).addTo(map);
    latInput.value = latlng.lat.toFixed(6);
    lngInput.value = latlng.lng.toFixed(6);
  };
  map.on('click', e => place(e.latlng));
  [latInput, lngInput].forEach(input => input.addEventListener('change', () => {
    if (latInput.value && lngInput.value) {
      const ll = L.latLng(+latInput.value, +lngInput.value);
      place(ll);
      map.setView(ll, Math.max(map.getZoom(), 13));
    }
  }));
}

// Listing form: preview a photo as soon as it's chosen
document.querySelectorAll('.photo-slot input[type=file]').forEach(input => {
  input.addEventListener('change', () => {
    const file = input.files[0];
    if (!file || !file.type.startsWith('image/')) return;
    const slot = input.closest('.photo-slot');
    let img = slot.querySelector('img');
    if (!img) {
      img = document.createElement('img');
      img.alt = 'Selected photo';
      slot.querySelector('.placeholder-img').replaceWith(img);
    }
    img.src = URL.createObjectURL(file);
  });
});
