    /* =============================================
       1. THEME — auto-detect system preference,
          respect manual toggle, persist to localStorage
    ============================================= */
    (function () {
      const html    = document.documentElement;
      const btn     = document.getElementById('themeBtn');
      const STORAGE = 'carelix-theme';

      function applyTheme(theme) {
        html.setAttribute('data-theme', theme);
        if (btn) {
          btn.innerHTML = theme === 'dark'
            ? "<i class='bx bx-sun'></i>"
            : "<i class='bx bx-moon'></i>";
        }
      }

      /* Determine initial theme:
         1. Honour saved preference first
         2. Fall back to OS/browser prefers-color-scheme */
      const saved  = localStorage.getItem(STORAGE);
      const prefers = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      const initial = saved || prefers;
      applyTheme(initial);

      /* Manual toggle */
      window.toggleTheme = function () {
        const current = html.getAttribute('data-theme');
        const next    = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        localStorage.setItem(STORAGE, next);
      };

      /* React to OS theme change (only if user hasn't overridden) */
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
        if (!localStorage.getItem(STORAGE)) {
          applyTheme(e.matches ? 'dark' : 'light');
        }
      });
    })();

    /* =============================================
       2. NAV — mobile menu
    ============================================= */
    function toggleMenu() {
      const burger = document.getElementById('burger');
      const menu   = document.getElementById('mobileMenu');
      const isOpen = menu.classList.contains('open');
      if (isOpen) { closeMenu(); return; }
      burger.classList.add('open');
      menu.classList.add('open');
      menu.querySelectorAll('.mobile-link').forEach(function (link) {
        link.style.animation = 'none';
        link.offsetHeight; // reflow
        link.style.animation = '';
      });
    }

    function closeMenu() {
      document.getElementById('burger').classList.remove('open');
      document.getElementById('mobileMenu').classList.remove('open');
    }

    /* =============================================
       3. CAROUSEL
    ============================================= */
    (function () {
      var CARD_W = 340 + 24; // card width + gap
      var idx    = 0;
      var track  = document.getElementById('carouselTrack');
      var cards  = track.querySelectorAll('.testi-card');
      var total  = cards.length;
      var dots   = document.getElementById('carouselDots');

      function visCount() {
        return Math.max(1, Math.floor(document.querySelector('.carousel-wrapper').offsetWidth / CARD_W));
      }

      var slides = Math.max(1, total - visCount() + 1);

      for (var i = 0; i < slides; i++) {
        (function (n) {
          var d = document.createElement('div');
          d.className = 'carousel-dot' + (n === 0 ? ' active' : '');
          d.onclick = function () { goTo(n); };
          dots.appendChild(d);
        })(i);
      }

      function updateDots() {
        document.querySelectorAll('.carousel-dot').forEach(function (d, i) {
          d.classList.toggle('active', i === idx);
        });
      }

      function goTo(n) {
        idx = Math.max(0, Math.min(n, slides - 1));
        /* On mobile, account for narrower card width */
        var effectiveW = window.innerWidth <= 640
          ? (document.querySelector('.carousel-wrapper').offsetWidth + 24)
          : CARD_W;
        track.style.transform = 'translateX(-' + (idx * effectiveW) + 'px)';
        updateDots();
      }

      window.moveCarousel = function (dir) { goTo(idx + dir); };

      var timer = setInterval(function () {
        idx = (idx + 1) % slides;
        goTo(idx);
      }, 5000);

      track.addEventListener('mouseenter', function () { clearInterval(timer); });
      track.addEventListener('mouseleave', function () {
        timer = setInterval(function () { idx = (idx + 1) % slides; goTo(idx); }, 5000);
      });

      /* Recalculate on resize */
      window.addEventListener('resize', function () {
        slides = Math.max(1, total - visCount() + 1);
        idx = Math.min(idx, slides - 1);
        goTo(idx);
      });
    })();

    /* =============================================
       4. SCROLL REVEAL
    ============================================= */
    (function () {
      var reveals  = document.querySelectorAll('[data-reveal]');
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12 });
      reveals.forEach(function (el) { observer.observe(el); });
    })();

    /* =============================================
       5. NAV ACTIVE LINK HIGHLIGHT
    ============================================= */
    (function () {
      var sections = document.querySelectorAll('section[id]');
      window.addEventListener('scroll', function () {
        var current = '';
        sections.forEach(function (s) {
          if (window.scrollY >= s.offsetTop - 90) current = s.id;
        });
        document.querySelectorAll('.nav-links a').forEach(function (a) {
          var active = a.getAttribute('href') === '#' + current;
          a.style.color      = active ? 'var(--accent-blue)' : '';
          a.style.background = active ? 'var(--accent-blue-light)' : '';
        });
      });
    })();

    /* =============================================
       6. CONTACT FORM — JS-only Formspree submit
          Replace YOUR_FORM_ID with your real ID
    ============================================= */
    (function () {
      var FORMSPREE_URL = 'https://formspree.io/f/YOUR_FORM_ID';

      var form      = document.getElementById('contactForm');
      var loader    = document.getElementById('formLoader');
      var submitBtn = document.getElementById('submitBtn');
      var msgEl     = document.getElementById('formMsg');

      function showMsg(type, text) {
        msgEl.className = 'form-msg ' + type;
        msgEl.textContent = text;
      }

      function clearMsg() {
        msgEl.className = 'form-msg';
        msgEl.textContent = '';
      }

      function setLoading(on) {
        loader.classList.toggle('active', on);
        submitBtn.disabled = on;
        submitBtn.style.opacity = on ? '0.6' : '1';
      }

      form.addEventListener('submit', function (e) {
        e.preventDefault();
        clearMsg();

        /* Basic client-side validation */
        var fname    = form.querySelector('#fname').value.trim();
        var email    = form.querySelector('#email').value.trim();
        var category = form.querySelector('#category').value;
        var message  = form.querySelector('#message').value.trim();

        if (!fname || !email || !category || !message) {
          showMsg('error', 'Please fill in all required fields before sending.');
          return;
        }

        var emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRe.test(email)) {
          showMsg('error', 'Please enter a valid email address.');
          return;
        }

        setLoading(true);

        var data = new FormData(form);

        fetch(FORMSPREE_URL, {
          method: 'POST',
          body: data,
          headers: { 'Accept': 'application/json' }
        })
        .then(function (res) {
          setLoading(false);
          if (res.ok) {
            form.reset();
            showPopup();
          } else {
            return res.json().then(function (body) {
              var errMsg = (body && body.errors && body.errors[0] && body.errors[0].message)
                ? body.errors[0].message
                : 'Something went wrong. Please try again.';
              showMsg('error', errMsg);
            });
          }
        })
        .catch(function () {
          setLoading(false);
          showMsg('error', 'Network error — please check your connection and try again.');
        });
      });

      /* Success popup */
      window.showPopup = function () {
        var overlay = document.getElementById('popupOverlay');
        var fill    = document.getElementById('popupBarFill');
        overlay.classList.add('show');
        fill.style.transition = 'none';
        fill.style.width = '100%';
        requestAnimationFrame(function () {
          fill.style.transition = 'width 3.5s linear';
          fill.style.width = '0%';
        });
        setTimeout(function () {
          overlay.classList.remove('show');
        }, 3600);
      };

      document.getElementById('popupOverlay').addEventListener('click', function (e) {
        if (e.target === this) this.classList.remove('show');
      });
    })();