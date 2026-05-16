document.addEventListener('DOMContentLoaded', initializeOptimizations);

function initializeOptimizations() {
  lazyLoadImages();
  optimizeForms();
  enableSmoothScrolling();
  optimizeTableScrolling();
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

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    lazyLoadImages,
    optimizeForms,
    enableSmoothScrolling,
  };
}
