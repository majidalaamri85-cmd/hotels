document.addEventListener('DOMContentLoaded', initializeOptimizations);

function initializeOptimizations() {
  lazyLoadImages();
  optimizeForms();
  enableSmoothScrolling();
  optimizeTableScrolling();
  setupDependentWilayatSelect();
  setupHotelLocationLink();
  setupVisitingTeamFields();
}

function lazyLoadImages() {
  if (!('IntersectionObserver' in window)) {
    return;
  }

  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) {
        return;
      }

      const img = entry.target;
      if (img.dataset.src) {
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
      }
      img.classList.add('loaded');
      observer.unobserve(img);
    });
  }, { rootMargin: '50px' });

  document.querySelectorAll('img[data-src]').forEach(img => {
    imageObserver.observe(img);
  });
}

function optimizeForms() {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function() {
      const submitBtn = this.querySelector('[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.dataset.originalText = submitBtn.textContent;
        submitBtn.textContent = 'جاري الحفظ...';
      }
    });

    form.querySelectorAll('input[type="file"]').forEach(input => {
      input.addEventListener('change', handleFileInput);
    });
  });
}

function handleFileInput(event) {
  const maxSize = 5 * 1024 * 1024;
  const files = Array.from(event.target.files || []);

  for (const file of files) {
    if (file.size > maxSize) {
      alert(`الملف ${file.name} أكبر من 5 MB`);
      event.target.value = '';
      return;
    }
  }
}

function enableSmoothScrolling() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (!href || href === '#') {
        return;
      }

      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

function optimizeTableScrolling() {
  document.querySelectorAll('.table-responsive').forEach(wrapper => {
    wrapper.setAttribute('tabindex', '0');
    wrapper.setAttribute('aria-label', 'جدول قابل للتمرير');
  });
}

function setupDependentWilayatSelect() {
  const dataNode = document.getElementById('governorate-wilayat-data');
  const governorateSelect = document.querySelector('select[name="governorate"]');
  const wilayatSelect = document.querySelector('select[name="wilayat"]');

  if (!dataNode || !governorateSelect || !wilayatSelect) {
    return;
  }

  let mapping = {};
  try {
    mapping = JSON.parse(dataNode.textContent || '{}');
  } catch (error) {
    mapping = {};
  }

  const defaultOptions = Array.from(wilayatSelect.options).map(option => ({
    value: option.value,
    text: option.textContent,
  }));

  function renderWilayatOptions(governorate) {
    const options = mapping[governorate] || [];
    const selectedValue = wilayatSelect.value;
    wilayatSelect.innerHTML = '';

    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'اختر الولاية';
    wilayatSelect.appendChild(placeholder);

    const source = options.length ? options : defaultOptions.filter(option => option.value);
    source.forEach(optionData => {
      const option = document.createElement('option');
      option.value = optionData[0] || optionData.value;
      option.textContent = optionData[1] || optionData.text;
      if (selectedValue && option.value === selectedValue) {
        option.selected = true;
      }
      wilayatSelect.appendChild(option);
    });

    if (!source.length) {
      wilayatSelect.value = '';
    }
  }

  governorateSelect.addEventListener('change', () => renderWilayatOptions(governorateSelect.value));
  renderWilayatOptions(governorateSelect.value);
}

function setupHotelLocationLink() {
  const triggerButton = document.getElementById('hotel-location-trigger');
  const locationLink = document.getElementById('hotel-location-link');
  const locationStatus = document.getElementById('hotel-location-status');
  const pasteInput = document.getElementById('hotel-location-paste');
  const parseButton = document.getElementById('hotel-location-parse');
  const latitudeField = document.getElementById('id_latitude');
  const longitudeField = document.getElementById('id_longitude');

  if (!triggerButton || !locationLink || !locationStatus || !pasteInput || !parseButton || !latitudeField || !longitudeField) {
    return;
  }

  // Parse lat/lng from a Google Maps URL or plain "lat, lng" text
  function parseCoordsFromText(text) {
    text = text.trim();

    // Format: /@lat,lng,  or  ?q=lat,lng  or  ll=lat,lng  or  center=lat,lng
    const urlPattern = /[/@?&](?:q=|ll=|center=)?(-?\d{1,3}\.\d+)[,+](-?\d{1,3}\.\d+)/i;
    const urlMatch = text.match(urlPattern);
    if (urlMatch) {
      return { lat: parseFloat(urlMatch[1]), lng: parseFloat(urlMatch[2]) };
    }

    // Format: plain "23.5880, 58.3829" or "23.5880 58.3829"
    const plainPattern = /^(-?\d{1,3}\.\d+)[,\s]+(-?\d{1,3}\.\d+)$/;
    const plainMatch = text.match(plainPattern);
    if (plainMatch) {
      return { lat: parseFloat(plainMatch[1]), lng: parseFloat(plainMatch[2]) };
    }

    return null;
  }

  function applyCoords(lat, lng) {
    latitudeField.value = lat.toFixed(7);
    longitudeField.value = lng.toFixed(7);
    locationLink.href = `https://www.google.com/maps?q=${encodeURIComponent(lat)},${encodeURIComponent(lng)}`;
    locationStatus.textContent = `\u2705 تم تسجيل الموقع: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    locationStatus.style.color = 'var(--brand)';
  }

  // GPS button
  triggerButton.addEventListener('click', () => {
    if (!('geolocation' in navigator)) {
      locationStatus.textContent = 'المتصفح لا يدعم تحديد الموقع تلقائيًا. استخدم خيار اللصق أدناه.';
      return;
    }

    triggerButton.disabled = true;
    triggerButton.textContent = 'جاري التحديد...';
    locationStatus.style.color = 'var(--muted)';
    locationStatus.textContent = 'جاري تحديد الموقع...';

    navigator.geolocation.getCurrentPosition(
      position => {
        triggerButton.disabled = false;
        triggerButton.textContent = 'تحديد موقعي تلقائيًا (GPS)';
        applyCoords(position.coords.latitude, position.coords.longitude);
      },
      error => {
        triggerButton.disabled = false;
        triggerButton.textContent = 'تحديد موقعي تلقائيًا (GPS)';
        if (error.code === 1) {
          locationStatus.innerHTML = 'رُفض الإذن. يتم فتح خرائط Google تلقائيًا &mdash; انتقل للفندق، انسخ الرابط، ثم الصقه في الحقل أدناه.';
          window.open('https://maps.google.com', '_blank', 'noopener');
        } else {
          locationStatus.textContent = 'تعذر تحديد الموقع. الصق رابط Google Maps في الحقل أدناه.';
        }
        locationStatus.style.color = 'var(--danger)';
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
    );
  });

  // Parse-from-link button
  parseButton.addEventListener('click', () => {
    const coords = parseCoordsFromText(pasteInput.value);
    if (!coords) {
      locationStatus.textContent = 'تعذر قراءة الإحداثيات. تأكد من صحة الرابط أو الصيغة مثال: 23.5880, 58.3829';
      locationStatus.style.color = 'var(--danger)';
      return;
    }
    applyCoords(coords.lat, coords.lng);
    pasteInput.value = '';
  });

  // Also parse on Enter key inside paste input
  pasteInput.addEventListener('keydown', event => {
    if (event.key === 'Enter') {
      event.preventDefault();
      parseButton.click();
    }
  });

  // If coordinates already saved (edit mode), show status
  if (latitudeField.value && longitudeField.value) {
    const lat = parseFloat(latitudeField.value);
    const lng = parseFloat(longitudeField.value);
    locationLink.href = `https://www.google.com/maps?q=${encodeURIComponent(lat)},${encodeURIComponent(lng)}`;
    locationStatus.textContent = `\u2705 الموقع محفوظ: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    locationStatus.style.color = 'var(--brand)';
  }
}

function setupVisitingTeamFields() {
  const list = document.getElementById('visitor-team-list');
  const addButton = document.getElementById('visitor-add-person');

  if (!list || !addButton) {
    return;
  }

  function createRow(value = '') {
    const row = document.createElement('div');
    row.className = 'visitor-person-row';

    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'visiting_team_members[]';
    input.className = 'form-control';
    input.placeholder = 'اسم الشخص';
    input.value = value;

    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'btn btn-ghost visitor-remove-btn';
    removeButton.setAttribute('aria-label', 'حذف الشخص');
    removeButton.textContent = 'حذف';

    row.appendChild(input);
    row.appendChild(removeButton);
    return row;
  }

  function ensureAtLeastOneRow() {
    if (!list.querySelector('.visitor-person-row')) {
      list.appendChild(createRow(''));
    }
  }

  addButton.addEventListener('click', () => {
    const row = createRow('');
    list.appendChild(row);
    row.querySelector('input').focus();
  });

  list.addEventListener('click', event => {
    const removeButton = event.target.closest('.visitor-remove-btn');
    if (!removeButton) {
      return;
    }
    removeButton.closest('.visitor-person-row')?.remove();
    ensureAtLeastOneRow();
  });

  ensureAtLeastOneRow();
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    lazyLoadImages,
    optimizeForms,
    enableSmoothScrolling,
    setupDependentWilayatSelect,
    setupHotelLocationLink,
    setupVisitingTeamFields,
  };
}
