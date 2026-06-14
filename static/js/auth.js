
function applySystemTheme() {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const html = document.documentElement;

  html.setAttribute('data-theme', prefersDark ? 'dark' : 'light');

  const themeBtn = document.getElementById('themeBtn');
  if (themeBtn) {
    themeBtn.innerHTML = prefersDark
      ? "<i class='bx bx-sun'></i>"
      : "<i class='bx bx-moon'></i>";
  }
}

// Run immediately
applySystemTheme();

// Listen for system theme changes while the page is open
window.matchMedia('(prefers-color-scheme: dark)')
  .addEventListener('change', (e) => {
    const html = document.documentElement;
    const isDark = e.matches;

    html.setAttribute('data-theme', isDark ? 'dark' : 'light');

    const themeBtn = document.getElementById('themeBtn');
    if (themeBtn) {
      themeBtn.innerHTML = isDark
        ? "<i class='bx bx-sun'></i>"
        : "<i class='bx bx-moon'></i>";
    }
  });

// ── Theme toggle ──
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';

  html.setAttribute('data-theme', isDark ? 'light' : 'dark');

  const themeBtn = document.getElementById('themeBtn');
  if (themeBtn) {
    themeBtn.innerHTML = isDark
      ? "<i class='bx bx-moon'></i>"
      : "<i class='bx bx-sun'></i>";
  }
}

// ── Password show/hide ──
function togglePw(id, btn) {
  const input = document.getElementById(id);
  const isText = input.type === 'text';

  input.type = isText ? 'password' : 'text';
  btn.innerHTML = isText
    ? "<i class='bx bx-show'></i>"
    : "<i class='bx bx-hide'></i>";
}

// ── Scroll reveal ──
const reveals = document.querySelectorAll('[data-reveal]');

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

reveals.forEach(el => observer.observe(el));

// Trigger immediately for above-fold elements
window.addEventListener('load', () => {
  reveals.forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight) {
      el.classList.add('visible');
    }
  });
});