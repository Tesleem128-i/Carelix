/* =========================================================
   CARELIX — DASHBOARD JS (shared by patient & hospital)
   ========================================================= */

/* ---------- Mobile sidebar toggle ---------- */
function toggleSidebar() {
  const sb = document.getElementById('dashSidebar');
  if (sb) sb.classList.toggle('open');
}

/* close sidebar when clicking outside on mobile */
document.addEventListener('click', function (e) {
  const sb = document.getElementById('dashSidebar');
  const toggleBtn = document.getElementById('sidebarToggleBtn');
  if (!sb || !sb.classList.contains('open')) return;
  if (sb.contains(e.target) || (toggleBtn && toggleBtn.contains(e.target))) return;
  sb.classList.remove('open');
});

/* ---------- Copy to clipboard ---------- */
function copyText(text, btnEl) {
  navigator.clipboard.writeText(text).then(function () {
    if (!btnEl) return;
    const original = btnEl.innerHTML;
    btnEl.innerHTML = "<i class='bx bx-check'></i> Copied!";
    btnEl.classList.add('copied');
    setTimeout(function () {
      btnEl.innerHTML = original;
      btnEl.classList.remove('copied');
    }, 1800);
  });
}

/* ---------- Tabs ---------- */
function switchTab(tabName, groupName) {
  const tabs = document.querySelectorAll('[data-tab-group="' + groupName + '"] .dash-tab');
  const panels = document.querySelectorAll('[data-panel-group="' + groupName + '"] .dash-tab-panel');
  tabs.forEach(function (t) {
    t.classList.toggle('active', t.dataset.tab === tabName);
  });
  panels.forEach(function (p) {
    p.classList.toggle('active', p.dataset.panel === tabName);
  });
}

/* ---------- Modal helpers ---------- */
function openModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.add('open');
}
function closeModal(id) {
  const m = document.getElementById(id);
  if (m) m.classList.remove('open');
}
/* close modal on overlay click */
document.addEventListener('click', function (e) {
  if (e.target.classList && e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

/* ---------- Confirm before destructive form submit ---------- */
function confirmSubmit(message) {
  return window.confirm(message);
}

/* ---------- Auto-dismiss flash messages ---------- */
document.addEventListener('DOMContentLoaded', function () {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(function (f) {
    setTimeout(function () {
      f.style.transition = 'opacity 0.4s, transform 0.4s';
      f.style.opacity = '0';
      f.style.transform = 'translateY(-10px)';
      setTimeout(function () { f.remove(); }, 400);
    }, 4500);
  });
});