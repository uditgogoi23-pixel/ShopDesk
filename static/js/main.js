/* ═══════════════════════════════════════════════════════════════════════════
   Harry Retail — Main JS
   Sidebar toggle + shared utilities
   ══════════════════════════════════════════════════════════════════════════ */

"use strict";

// ── SIDEBAR TOGGLE ─────────────────────────────────────────────────────────
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ── CURRENCY FORMAT ────────────────────────────────────────────────────────
const CURRENCY = '₹';

function formatCurrency(amount) {
  return CURRENCY + Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

// ── CONFIRM DELETE ─────────────────────────────────────────────────────────
function confirmDelete(formId, productName) {
  if (confirm(`Delete "${productName}"?\n\nThis cannot be undone.`)) {
    document.getElementById(formId).submit();
  }
}

// ── AUTO-DISMISS FLASH ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 5000);
  });
});
