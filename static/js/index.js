    function toggleTheme() {
      const html = document.documentElement;
      const isDark = html.getAttribute('data-theme') === 'dark';
      html.setAttribute('data-theme', isDark ? 'light' : 'dark');
      document.getElementById('themeBtn').innerHTML = isDark
        ? "<i class='bx bx-moon'></i>"
        : "<i class='bx bx-sun'></i>";
    }

    function toggleMenu() {
      const burger = document.getElementById('burger');
      const menu = document.getElementById('mobileMenu');
      const isOpen = menu.classList.contains('open');
      if (isOpen) { closeMenu(); return; }
      burger.classList.add('open');
      menu.classList.add('open');
      // re-trigger animations
      menu.querySelectorAll('.mobile-link').forEach(link => {
        link.style.animation = 'none';
        link.offsetHeight; // reflow
        link.style.animation = '';
      });
    }
    function closeMenu() {
      document.getElementById('burger').classList.remove('open');
      document.getElementById('mobileMenu').classList.remove('open');
    }

    const CARD_WIDTH = 340 + 24; // card + gap
    let currentIndex = 0;
    const track = document.getElementById('carouselTrack');
    const cards = track.querySelectorAll('.testi-card');
    const totalCards = cards.length;
    const dotsContainer = document.getElementById('carouselDots');
    let visibleCount = Math.floor(document.querySelector('.carousel-wrapper').offsetWidth / CARD_WIDTH) || 1;
    const totalSlides = Math.max(1, totalCards - visibleCount + 1);

    // build dots
    for (let i = 0; i < totalSlides; i++) {
      const dot = document.createElement('div');
      dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
      dot.onclick = () => goToSlide(i);
      dotsContainer.appendChild(dot);
    }

    function updateDots() {
      document.querySelectorAll('.carousel-dot').forEach((d, i) => {
        d.classList.toggle('active', i === currentIndex);
      });
    }
    function goToSlide(n) {
      currentIndex = Math.max(0, Math.min(n, totalSlides - 1));
      track.style.transform = `translateX(-${currentIndex * CARD_WIDTH}px)`;
      updateDots();
    }
    function moveCarousel(dir) { goToSlide(currentIndex + dir); }

    let autoPlay = setInterval(() => {
      currentIndex = (currentIndex + 1) % totalSlides;
      goToSlide(currentIndex);
    }, 5000);
    track.addEventListener('mouseenter', () => clearInterval(autoPlay));
    track.addEventListener('mouseleave', () => {
      autoPlay = setInterval(() => { currentIndex = (currentIndex + 1) % totalSlides; goToSlide(currentIndex); }, 5000);
    });

    const reveals = document.querySelectorAll('[data-reveal]');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting) {
          entry.target.style.transitionDelay = entry.target.style.transitionDelay || '0s';
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach(el => observer.observe(el));

    const form = document.getElementById('contactForm');
    const loader = document.getElementById('formLoader');
    const overlay = document.getElementById('popupOverlay');

    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      loader.style.display = 'flex';
      form.style.display = 'none';

      try {
        const data = new FormData(form);
        const response = await fetch(form.action, {
          method: 'POST',
          body: data,
          headers: { 'Accept': 'application/json' }
        });
        loader.style.display = 'none';
        if (response.ok) {
          showPopup();
          form.reset();
        } else {
          form.style.display = 'block';
          alert('Something went wrong. Please try again or email us directly.');
        }
      } catch (err) {
        loader.style.display = 'none';
        form.style.display = 'block';
        alert('Network error. Please check your connection and try again.');
      }
    });

    function showPopup() {
      overlay.classList.add('show');
      const fill = document.getElementById('popupBarFill');
      fill.style.transition = 'none';
      fill.style.width = '100%';
      requestAnimationFrame(() => {
        fill.style.transition = 'width 3.5s linear';
        fill.style.width = '0%';
      });
      setTimeout(() => {
        overlay.classList.remove('show');
        form.style.display = 'block';
      }, 3600);
    }
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) overlay.classList.remove('show');
    });

    const sections = document.querySelectorAll('section[id]');
    window.addEventListener('scroll', () => {
      let current = '';
      sections.forEach(s => {
        if (window.scrollY >= s.offsetTop - 90) current = s.id;
      });
      document.querySelectorAll('.nav-links a').forEach(a => {
        a.style.color = a.getAttribute('href') === '#' + current
          ? 'var(--accent-blue)' : '';
        a.style.background = a.getAttribute('href') === '#' + current
          ? 'var(--accent-blue-light)' : '';
      });
    });