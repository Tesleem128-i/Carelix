/* =========================================================
   CARELIX — DASHBOARD JS
   ========================================================= */

/* ── Sidebar ── */
function toggleSidebar() {
  var sb      = document.getElementById('dashSidebar');
  var overlay = document.getElementById('sidebarOverlay');
  if (!sb) return;
  var opening = !sb.classList.contains('open');
  sb.classList.toggle('open', opening);
  if (overlay) overlay.classList.toggle('active', opening);
}

function closeSidebarMobile() {
  var sb      = document.getElementById('dashSidebar');
  var overlay = document.getElementById('sidebarOverlay');
  if (sb)      sb.classList.remove('open');
  if (overlay) overlay.classList.remove('active');
}

/* ── Tab switching ── */
function switchTab(tabName, groupName) {
  /* panels */
  var panels = document.querySelectorAll('[data-panel-group="' + groupName + '"] .dash-tab-panel');
  panels.forEach(function(p) {
    p.classList.toggle('active', p.getAttribute('data-panel') === tabName);
  });

  /* nav links — match by data-tab attribute */
  var links = document.querySelectorAll('.dash-nav-link[data-tab]');
  links.forEach(function(l) {
    l.classList.toggle('active', l.getAttribute('data-tab') === tabName);
  });

  /* scroll to top */
  window.scrollTo(0, 0);
}

/* ── Copy to clipboard ── */
function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(function() {
    if (!btn) return;
    var orig = btn.innerHTML;
    btn.innerHTML = "<i class='bx bx-check'></i> Copied!";
    btn.classList.add('copied');
    setTimeout(function() { btn.innerHTML = orig; btn.classList.remove('copied'); }, 1800);
  });
}

/* ── Modals ── */
function openModal(id)  { var m = document.getElementById(id); if (m) m.classList.add('open'); }
function closeModal(id) { var m = document.getElementById(id); if (m) m.classList.remove('open'); }

document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) e.target.classList.remove('open');
});

function confirmSubmit(msg) { return window.confirm(msg); }

/* ── Flash auto-dismiss ── */
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.flash').forEach(function(f) {
    setTimeout(function() {
      f.style.transition = 'opacity 0.4s';
      f.style.opacity = '0';
      setTimeout(function() { f.remove(); }, 400);
    }, 4500);
  });
});