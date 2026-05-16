document.addEventListener('DOMContentLoaded', initializeOptimizations);

function initializeOptimizations() {
  lazyLoadImages();
  optimizeForms();
  enableSmoothScrolling();
  optimizeTableScrolling();
  setupDependentWilayatSelect();
  setupHotelLocationLink();
  setupVisitingTeamFields();
  setupCriterionFailureFields();
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
  const locationStatus = document.getElementById('hotel-location-status');
  const latitudeField = document.getElementById('id_latitude');
  const longitudeField = document.getElementById('id_longitude');

  if (!triggerButton || !locationStatus || !latitudeField || !longitudeField) {
    return;
  }

  function applyCoords(lat, lng) {
    latitudeField.value = lat.toFixed(7);
    longitudeField.value = lng.toFixed(7);
    locationStatus.textContent = `\u2705 تم تسجيل الموقع: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
    locationStatus.style.color = 'var(--brand)';
  }

  triggerButton.addEventListener('click', () => {
    if (!('geolocation' in navigator)) {
      locationStatus.textContent = 'المتصفح لا يدعم تحديد الموقع تلقائيًا.';
      locationStatus.style.color = 'var(--danger)';
      return;
    }

    triggerButton.disabled = true;
    triggerButton.textContent = 'جاري التحديد...';
    locationStatus.style.color = 'var(--muted)';
    locationStatus.textContent = 'جاري تحديد الموقع...';

    navigator.geolocation.getCurrentPosition(
      position => {
        triggerButton.disabled = false;
        triggerButton.textContent = 'تحديد الموقع المباشر الآن';
        applyCoords(position.coords.latitude, position.coords.longitude);
      },
      error => {
        triggerButton.disabled = false;
        triggerButton.textContent = 'تحديد الموقع المباشر الآن';
        if (error.code === 1) {
          locationStatus.textContent = 'تم رفض إذن الموقع. فعّل الإذن ثم أعد المحاولة.';
        } else {
          locationStatus.textContent = 'تعذر تحديد الموقع. أعد المحاولة مرة أخرى.';
        }
        locationStatus.style.color = 'var(--danger)';
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
    );
  });

  if (latitudeField.value && longitudeField.value) {
    const lat = parseFloat(latitudeField.value);
    const lng = parseFloat(longitudeField.value);
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

function setupCriterionFailureFields() {
  document.querySelectorAll('.criterion-preview-row').forEach(row => {
    const fields = row.querySelector('[data-failure-fields]');
    if (!fields) {
      return;
    }

    const inputs = Array.from(fields.querySelectorAll('input, textarea, select'));
    const radios = Array.from(row.querySelectorAll('input[type="radio"][name^="criterion_result_"]'));

    function syncFields() {
      const selected = radios.find(radio => radio.checked);
      const showFields = selected?.value === 'NO';
      fields.hidden = !showFields;
      inputs.forEach(input => {
        input.disabled = !showFields;
      });
    }

    radios.forEach(radio => {
      radio.addEventListener('change', syncFields);
    });
    syncFields();
  });

  document.querySelectorAll('[data-evaluation-criterion-row]').forEach(row => {
    const fields = row.querySelector('[data-failure-fields]');
    const select = row.querySelector('[data-result-select]');
    if (!fields || !select) {
      return;
    }

    const inputs = Array.from(fields.querySelectorAll('input, textarea, select'));

    function syncFields() {
      const showFields = select.value === 'NO';
      fields.hidden = !showFields;
      row.classList.toggle('is-failed', showFields);
      select.classList.toggle('border-danger', showFields);
      select.classList.toggle('text-danger', showFields);
      inputs.forEach(input => {
        input.disabled = !showFields;
      });

      if (showFields) {
        const actionField = fields.querySelector('textarea[name^="action_"]');
        if (actionField && !actionField.value.trim()) {
          actionField.value = actionField.dataset.defaultAction || '';
        }
      }
    }

    select.addEventListener('change', syncFields);
    syncFields();
  });
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    lazyLoadImages,
    optimizeForms,
    enableSmoothScrolling,
    setupDependentWilayatSelect,
    setupHotelLocationLink,
    setupVisitingTeamFields,
    setupCriterionFailureFields,
  };
}
