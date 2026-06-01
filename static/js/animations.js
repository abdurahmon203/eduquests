(function () {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function initParticles() {
    if (prefersReduced) return;
    const field = document.getElementById('particle-field');
    if (!field) return;
    const count = window.innerWidth < 768 ? 18 : 35;
    for (let i = 0; i < count; i++) {
      const p = document.createElement('span');
      p.className = 'particle';
      p.style.left = `${Math.random() * 100}%`;
      p.style.top = `${100 + Math.random() * 20}%`;
      p.style.animationDuration = `${12 + Math.random() * 18}s`;
      p.style.animationDelay = `${Math.random() * 10}s`;
      p.style.width = p.style.height = `${2 + Math.random() * 4}px`;
      field.appendChild(p);
    }
  }

  function initScrollReveal() {
    const selectors = '.reveal, .reveal-scale, .reveal-left, .reveal-right, .reveal-blur';
    const revealEls = document.querySelectorAll(selectors);
    if (!revealEls.length) return;

    if (prefersReduced) {
      revealEls.forEach((el) => el.classList.add('is-visible'));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      },
      { root: null, rootMargin: '0px 0px -60px 0px', threshold: 0.08 }
    );

    revealEls.forEach((el) => observer.observe(el));
  }

  function initStaggerGroups() {
    document.querySelectorAll('.stagger-group').forEach((group) => {
      const kids = group.querySelectorAll(
        ':scope > .reveal, :scope > .reveal-scale, :scope > .hover-lift, :scope > article, :scope > .feature-card, :scope > .step-card, :scope > .subject-card, :scope > .level-card'
      );
      kids.forEach((kid, i) => {
        kid.style.setProperty('--stagger-i', i);
        if (!kid.classList.contains('reveal') && !kid.classList.contains('reveal-scale')) {
          kid.classList.add('reveal');
        }
      });
    });
  }

  function initHeaderScroll() {
    const header = document.getElementById('site-header');
    if (!header) return;
    const onScroll = () => {
      header.classList.toggle('header-scrolled', window.scrollY > 24);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  function initParallax() {
    if (prefersReduced) return;
    const els = document.querySelectorAll('[data-parallax]');
    if (!els.length) return;

    let ticking = false;
    const update = () => {
      const y = window.scrollY;
      els.forEach((el) => {
        const speed = parseFloat(el.dataset.parallax) || 0.15;
        el.style.transform = `translateY(${y * speed}px)`;
      });
      ticking = false;
    };

    window.addEventListener(
      'scroll',
      () => {
        if (!ticking) {
          requestAnimationFrame(update);
          ticking = true;
        }
      },
      { passive: true }
    );
    update();
  }

  function initTiltCards() {
    if (prefersReduced || window.innerWidth < 900) return;
    document.querySelectorAll('.tilt-card').forEach((card) => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        card.style.transform = `perspective(800px) rotateY(${x * 10}deg) rotateX(${-y * 10}deg) translateY(-8px)`;
      });
      card.addEventListener('mouseleave', () => {
        card.style.transform = '';
      });
    });
  }

  function initRipples() {
    document.querySelectorAll('.btn-primary, .btn-secondary, .lang-btn').forEach((btn) => {
      if (!btn.classList.contains('ripple-host')) btn.classList.add('ripple-host');
      btn.addEventListener('click', function (e) {
        if (prefersReduced) return;
        const rect = this.getBoundingClientRect();
        const ripple = document.createElement('span');
        ripple.className = 'ripple';
        const size = Math.max(rect.width, rect.height);
        ripple.style.width = ripple.style.height = `${size}px`;
        ripple.style.left = `${e.clientX - rect.left - size / 2}px`;
        ripple.style.top = `${e.clientY - rect.top - size / 2}px`;
        this.appendChild(ripple);
        setTimeout(() => ripple.remove(), 700);
      });
    });
  }

  function initCountUp() {
    if (prefersReduced) return;
    const els = document.querySelectorAll('.count-up');
    if (!els.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting || entry.target.classList.contains('is-done')) return;
          const el = entry.target;
          const target = parseFloat(el.dataset.count || el.textContent) || 0;
          const suffix = el.dataset.suffix || '';
          const prefix = el.dataset.prefix || '';
          const duration = 1400;
          const start = performance.now();
          const isFloat = String(target).includes('.');

          const step = (now) => {
            const p = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            const val = target * eased;
            el.textContent = prefix + (isFloat ? val.toFixed(1) : Math.floor(val)) + suffix;
            if (p < 1) requestAnimationFrame(step);
            else {
              el.classList.add('is-done');
              el.textContent = prefix + target + suffix;
            }
          };
          requestAnimationFrame(step);
          observer.unobserve(el);
        });
      },
      { threshold: 0.5 }
    );
    els.forEach((el) => observer.observe(el));
  }

  function initProgressBars() {
    const bars = document.querySelectorAll('.animate-progress');
    if (!bars.length) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-animating');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.3 }
    );
    bars.forEach((b) => observer.observe(b));
  }

  function autoRevealGrids() {
    const grids = document.querySelectorAll(
      '.features-grid, .steps-container, .subject-grid, .level-grid, .friends-grid, .about-stats'
    );
    grids.forEach((grid) => {
      if (!grid.classList.contains('stagger-group')) grid.classList.add('stagger-group');
      grid.querySelectorAll(':scope > *').forEach((child, i) => {
        if (!child.classList.contains('reveal')) child.classList.add('reveal');
        child.style.setProperty('--stagger-i', i);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initStaggerGroups();
    autoRevealGrids();
    initScrollReveal();
    initHeaderScroll();
    initParallax();
    initTiltCards();
    initRipples();
    initCountUp();
    initProgressBars();
  });
})();
