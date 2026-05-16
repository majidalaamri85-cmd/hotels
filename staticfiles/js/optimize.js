/**
 * Performance optimization script for mobile and desktop
 * Lazy loading, intersection observer, and DOM optimization
 */

// Initialize once DOM is ready
document.addEventListener('DOMContentLoaded', initializeOptimizations);

function initializeOptimizations() {
  // Lazy load images
  lazyLoadImages();
  
  // Optimize forms
  optimizeForms();
  
  // Smooth scrolling for anchor links
  enableSmoothScrolling();
  
  // Debounce resize events
  debounceResizeEvents();
}

/**
 * Lazy load images using Intersection Observer
 */
function lazyLoadImages() {
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          img.classList.add('loaded');
          observer.unobserve(img);
        }
      });
    }, {
      rootMargin: '50px'
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
      imageObserver.observe(img);
    });
  }
}

/**
 * Optimize form interactions
 */
function optimizeForms() {
  const forms = document.querySelectorAll('form');
  
  forms.forEach(form => {
    // Add loading state on submit
    form.addEventListener('submit', function() {
      const submitBtn = this.querySelector('[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'جاري المعالجة...';
      }
    });
    
    // Optimize file inputs
    const fileInputs = form.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
      input.addEventListener('change', handleFileInput);
    });
  });
}

/**
 * Handle file input with size validation
 */
function handleFileInput(event) {
  const MAX_SIZE = 5 * 1024 * 1024; // 5 MB
  const files = event.target.files;
  
  for (let file of files) {
    if (file.size > MAX_SIZE) {
      alert(`الملف ${file.name} أكبر من 5 MB`);
      event.target.value = '';
      return;
    }
  }
}

/**
 * Enable smooth scrolling for anchor links
 */
function enableSmoothScrolling() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href !== '#') {
        e.preventDefault();
        const target = document.querySelector(href);
        if (target) {
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });
}

/**
 * Debounce resize events to prevent excessive reflows
 */
function debounceResizeEvents() {
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
      // Handle resize logic here
    }, 250);
  });
}

/**
 * Optimize table scrolling on mobile
 */
function optimizeTableScrolling() {
  const tables = document.querySelectorAll('.table');
  tables.forEach(table => {
    // Tables are already in overflow containers
    table.setAttribute('role', 'region');
    table.setAttribute('aria-label', 'جدول البيانات');
  });
}

/**
 * Preload critical resources
 */
function preloadCriticalResources() {
  // Preload next page resources if predictable
  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.href = window.location.href;
  document.head.appendChild(link);
}

/**
 * Monitor Core Web Vitals (if available)
 */
function monitorWebVitals() {
  // Send performance data to analytics if needed
  if ('PerformanceObserver' in window) {
    try {
      // Monitor largest contentful paint
      const lcpObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          console.log('LCP:', entry.startTime);
        }
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      // LCP might not be available
    }
  }
}

// Initialize monitoring
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', monitorWebVitals);
} else {
  monitorWebVitals();
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    lazyLoadImages,
    optimizeForms,
    enableSmoothScrolling
  };
}
