document.addEventListener('DOMContentLoaded', initializeOptimizations);

function initializeOptimizations() {
  lazyLoadImages();
  optimizeForms();
  enableSmoothScrolling();
  optimizeTableScrolling();
  setupDependentWilayatSelect();
  setupHotelLocationLink();
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
  const locationLink = document.getElementById('hotel-location-link');
  const latitudeField = document.getElementById('id_latitude');
  const longitudeField = document.getElementById('id_longitude');

  if (!locationLink || !latitudeField || !longitudeField) {
    return;
  }

  function syncLocationLink() {
    const latitude = latitudeField.value.trim();
    const longitude = longitudeField.value.trim();

    if (!latitude || !longitude) {
      locationLink.href = '#';
      locationLink.setAttribute('aria-disabled', 'true');
      locationLink.classList.add('disabled');
      return;
    }

    locationLink.href = `https://www.google.com/maps?q=${encodeURIComponent(latitude)},${encodeURIComponent(longitude)}`;
    locationLink.setAttribute('aria-disabled', 'false');
    locationLink.classList.remove('disabled');
  }

  latitudeField.addEventListener('input', syncLocationLink);
  longitudeField.addEventListener('input', syncLocationLink);
  syncLocationLink();
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    lazyLoadImages,
    optimizeForms,
    enableSmoothScrolling,
    setupDependentWilayatSelect,
    setupHotelLocationLink,
  };
}
