<template>
  <div class="aio-shell">
    <nav class="aio-nav">
      <NuxtLink to="/" class="aio-nav-logo">~/scholaraio</NuxtLink>
      <div class="aio-nav-links">
        <NuxtLink to="/" :class="{ active: route.path === '/' }">Library</NuxtLink>
        <NuxtLink to="/explore" :class="{ active: route.path.startsWith('/explore') }">Explore</NuxtLink>
      </div>
      <div class="aio-nav-meta">static snapshot · read status writeback</div>
    </nav>
    <main class="aio-page">
      <NuxtPage />
    </main>
  </div>
</template>

<script setup>
const route = useRoute()
</script>

<style>
:root {
  --aio-bg: #0d0f11;
  --aio-bg-soft: #13161a;
  --aio-bg-mute: #1a1e24;
  --aio-border: rgba(255, 255, 255, 0.08);
  --aio-border-strong: rgba(255, 255, 255, 0.14);
  --aio-text: #e8e6e0;
  --aio-text-soft: #b8b2aa;
  --aio-text-muted: #8c8780;
  --aio-accent: #4ade9a;
  --aio-blue: #60a5fa;
  --aio-amber: #f59e0b;
  --aio-purple: #a78bfa;
  --aio-red: #fb7185;
  --aio-font-serif: "Noto Serif SC", "Songti SC", Georgia, serif;
  --aio-font-sans: Inter, "Noto Sans SC", "Microsoft YaHei", Arial, sans-serif;
  --aio-font-mono: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
}

html {
  background: var(--aio-bg);
}

body {
  margin: 0;
  background:
    radial-gradient(circle at 18% -8%, rgba(74, 222, 154, 0.10), transparent 30rem),
    radial-gradient(circle at 92% 10%, rgba(96, 165, 250, 0.08), transparent 28rem),
    var(--aio-bg);
  color: var(--aio-text);
  font-family: var(--aio-font-sans);
}

a {
  color: inherit;
  text-decoration: none;
}

button,
input,
select,
textarea {
  font: inherit;
}

.aio-shell {
  min-height: 100vh;
  background: linear-gradient(180deg, rgba(13, 15, 17, 0.98), rgba(13, 15, 17, 1));
}

.aio-nav {
  position: fixed;
  inset: 0 0 auto;
  z-index: 50;
  display: grid;
  min-height: 64px;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: 18px;
  border-bottom: 1px solid var(--aio-border);
  background: rgba(13, 15, 17, 0.82);
  padding: 0 28px;
  backdrop-filter: blur(18px);
}

.aio-nav-logo {
  justify-self: start;
  color: var(--aio-text);
  font-family: var(--aio-font-mono);
  font-size: 13px;
  letter-spacing: 0;
}

.aio-nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--aio-border);
  background: rgba(255, 255, 255, 0.03);
  padding: 4px;
}

.aio-nav-links a {
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 12px;
  padding: 8px 12px;
  transition: color 160ms ease, background 160ms ease;
}

.aio-nav-links a:hover,
.aio-nav-links a.active {
  background: rgba(74, 222, 154, 0.10);
  color: var(--aio-accent);
}

.aio-nav-meta {
  justify-self: end;
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 11px;
}

.aio-page {
  min-height: 100vh;
  padding-top: 64px;
}

.aio-content {
  margin: 0 auto;
  max-width: 1180px;
  padding: 42px 22px 76px;
}

.aio-hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 30px;
  align-items: end;
  border-bottom: 1px solid var(--aio-border);
  padding: 46px 0 34px;
}

.aio-kicker {
  color: var(--aio-accent);
  font-family: var(--aio-font-mono);
  font-size: 12px;
  letter-spacing: 0;
}

.aio-title {
  margin: 14px 0 0;
  max-width: 820px;
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: clamp(42px, 7vw, 86px);
  font-weight: 500;
  line-height: 0.98;
  letter-spacing: 0;
}

.aio-subtitle {
  margin: 18px 0 0;
  max-width: 720px;
  color: var(--aio-text-soft);
  font-size: 15px;
  line-height: 1.9;
}

.aio-hero-stats {
  display: grid;
  min-width: 260px;
  border: 1px solid var(--aio-border);
}

.aio-stat {
  border-bottom: 1px solid var(--aio-border);
  padding: 16px 18px;
}

.aio-stat:last-child {
  border-bottom: 0;
}

.aio-stat-value {
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: 30px;
  line-height: 1;
}

.aio-stat-label {
  margin-top: 8px;
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 11px;
}

.aio-panel {
  border: 1px solid var(--aio-border);
  background: rgba(255, 255, 255, 0.025);
}

.aio-filter-panel {
  margin-top: 28px;
  padding: 18px;
}

.aio-field-grid {
  display: grid;
  gap: 14px;
}

.aio-field-grid.primary {
  grid-template-columns: minmax(0, 1fr) 190px;
}

.aio-field-grid.secondary {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 14px;
}

.aio-field span {
  display: block;
  margin-bottom: 8px;
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 11px;
}

.aio-input,
.aio-select {
  width: 100%;
  border: 1px solid var(--aio-border);
  border-radius: 0;
  background: rgba(13, 15, 17, 0.84);
  color: var(--aio-text);
  font-size: 14px;
  outline: none;
  padding: 12px 13px;
  transition: border-color 160ms ease, background 160ms ease;
}

.aio-input:focus,
.aio-select:focus {
  border-color: rgba(74, 222, 154, 0.60);
  background: rgba(17, 21, 25, 0.95);
}

.aio-input::placeholder {
  color: rgba(184, 178, 170, 0.48);
}

.aio-filter-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.aio-button,
.aio-button-secondary,
.aio-text-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  border: 1px solid var(--aio-border-strong);
  border-radius: 0;
  cursor: pointer;
  font-family: var(--aio-font-mono);
  font-size: 12px;
  line-height: 1;
  padding: 0 14px;
  transition: border-color 160ms ease, color 160ms ease, background 160ms ease, transform 160ms ease;
}

.aio-button {
  background: var(--aio-accent);
  border-color: rgba(74, 222, 154, 0.75);
  color: #07100b;
}

.aio-button:hover {
  background: #6ee7ad;
}

.aio-button-secondary,
.aio-text-link {
  background: rgba(255, 255, 255, 0.025);
  color: var(--aio-text-soft);
}

.aio-button-secondary:hover,
.aio-text-link:hover {
  border-color: rgba(74, 222, 154, 0.45);
  color: var(--aio-accent);
}

.aio-button:disabled,
.aio-button-secondary:disabled {
  cursor: not-allowed;
  opacity: 0.48;
}

.aio-muted {
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 12px;
}

.aio-section-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 42px;
  border-top: 1px solid var(--aio-border);
  padding-top: 18px;
}

.aio-section-header h2 {
  margin: 0;
  color: var(--aio-text);
  font-family: var(--aio-font-mono);
  font-size: 12px;
  font-weight: 500;
}

.aio-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 18px;
  border-top: 1px solid var(--aio-border);
  border-left: 1px solid var(--aio-border);
}

.aio-card {
  display: flex;
  min-height: 310px;
  flex-direction: column;
  border-right: 1px solid var(--aio-border);
  border-bottom: 1px solid var(--aio-border);
  background: rgba(255, 255, 255, 0.018);
  padding: 22px;
  position: relative;
  transition: background 160ms ease, transform 160ms ease;
}

.aio-card::before {
  content: "";
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 2px;
  background: transparent;
  transition: background 160ms ease;
}

.aio-card:hover {
  background: rgba(255, 255, 255, 0.045);
}

.aio-card:hover::before {
  background: var(--aio-accent);
}

.aio-card-top,
.aio-detail-topbar,
.aio-split-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.aio-pill-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.aio-pill {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--aio-border);
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 11px;
  line-height: 1;
  padding: 7px 9px;
}

.aio-pill.is-read {
  border-color: rgba(74, 222, 154, 0.35);
  color: var(--aio-accent);
}

.aio-pill.is-unread {
  border-color: rgba(245, 158, 11, 0.35);
  color: var(--aio-amber);
}

.aio-pill.is-ready {
  border-color: rgba(96, 165, 250, 0.35);
  color: var(--aio-blue);
}

.aio-pill.is-muted {
  color: var(--aio-text-muted);
}

.aio-card-title {
  margin: 18px 0 0;
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: 25px;
  font-weight: 500;
  line-height: 1.24;
  letter-spacing: 0;
}

.aio-card-authors,
.aio-card-meta {
  margin: 11px 0 0;
  color: var(--aio-text-muted);
  font-size: 13px;
  line-height: 1.6;
}

.aio-card-summary {
  margin-top: 18px;
  border-top: 1px solid var(--aio-border);
  padding-top: 16px;
}

.aio-card-summary p {
  margin: 0;
  color: var(--aio-text-soft);
  font-size: 14px;
  line-height: 1.85;
}

.aio-card-preview {
  margin-top: 10px;
  color: var(--aio-text-muted);
  font-size: 13px;
  line-height: 1.8;
}

.aio-card-action {
  margin-top: auto;
  padding-top: 22px;
  color: var(--aio-accent);
  font-family: var(--aio-font-mono);
  font-size: 12px;
}

.aio-mark {
  background: rgba(74, 222, 154, 0.22);
  color: var(--aio-text);
  padding: 0 2px;
}

.aio-state {
  margin-top: 28px;
  border: 1px solid var(--aio-border);
  color: var(--aio-text-soft);
  padding: 34px;
  text-align: center;
}

.aio-state.error {
  border-color: rgba(251, 113, 133, 0.35);
  color: #fda4af;
  text-align: left;
}

.aio-spinner {
  width: 42px;
  height: 42px;
  margin: 0 auto 14px;
  border: 2px solid rgba(255, 255, 255, 0.08);
  border-top-color: var(--aio-accent);
  border-radius: 999px;
  animation: aio-spin 900ms linear infinite;
}

.aio-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 18px;
  border: 1px solid var(--aio-border);
  padding: 13px 14px;
}

.aio-pagination-controls {
  display: flex;
  gap: 8px;
}

.aio-detail-page {
  margin: 0 auto;
  max-width: 1060px;
  padding: 34px 22px 76px;
}

.aio-paper-header {
  border-bottom: 1px solid var(--aio-border);
  padding: 28px 0 32px;
}

.aio-paper-title {
  margin: 18px 0 0;
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: clamp(34px, 5.8vw, 66px);
  font-weight: 500;
  line-height: 1.08;
  letter-spacing: 0;
}

.aio-paper-meta {
  margin-top: 16px;
  color: var(--aio-text-soft);
  font-size: 14px;
  line-height: 1.8;
}

.aio-model-box {
  border: 1px solid var(--aio-border);
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 11px;
  padding: 12px 14px;
}

.aio-message {
  margin-top: 14px;
  border: 1px solid var(--aio-border);
  color: var(--aio-text-soft);
  font-size: 13px;
  line-height: 1.6;
  padding: 11px 13px;
}

.aio-message.error {
  border-color: rgba(251, 113, 133, 0.40);
  color: #fda4af;
}

.aio-message.success {
  border-color: rgba(74, 222, 154, 0.38);
  color: var(--aio-accent);
}

.aio-token-box {
  margin-top: 14px;
  border: 1px solid var(--aio-border);
  background: rgba(255, 255, 255, 0.02);
  padding: 14px;
}

.aio-token-actions {
  display: flex;
  gap: 8px;
  margin-top: 9px;
}

.aio-callout {
  margin-top: 26px;
  border: 1px solid var(--aio-border);
  background: rgba(255, 255, 255, 0.025);
  padding: 24px;
}

.aio-callout-accent {
  border-color: rgba(74, 222, 154, 0.18);
  background: linear-gradient(135deg, rgba(74, 222, 154, 0.09), rgba(255, 255, 255, 0.02));
}

.aio-callout p:not(.aio-kicker) {
  margin: 10px 0 0;
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: 24px;
  line-height: 1.55;
}

.aio-token-note {
  margin-top: 10px;
}

.aio-note-section {
  margin-top: 28px;
  border-top: 1px solid var(--aio-border);
  padding-top: 22px;
}

.aio-note-section h2 {
  margin: 0;
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: 28px;
  font-weight: 500;
}

.aio-note-body {
  margin-top: 14px;
  color: var(--aio-text-soft);
  font-size: 15px;
  line-height: 2;
}

.aio-two-col,
.aio-three-col {
  display: grid;
  gap: 1px;
  margin-top: 16px;
  border: 1px solid var(--aio-border);
  background: var(--aio-border);
}

.aio-two-col {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.aio-three-col {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.aio-cell {
  background: var(--aio-bg-soft);
  padding: 18px;
}

.aio-cell h3 {
  margin: 0;
  color: var(--aio-text);
  font-family: var(--aio-font-mono);
  font-size: 12px;
  font-weight: 500;
}

.aio-cell p {
  margin: 10px 0 0;
  color: var(--aio-text-soft);
  font-size: 14px;
  line-height: 1.9;
}

.aio-key-row {
  display: grid;
  grid-template-columns: 124px minmax(0, 1fr);
  gap: 18px;
  border-top: 1px solid var(--aio-border);
  padding: 15px 0;
}

.aio-key-row:first-child {
  border-top: 0;
}

.aio-key-row strong {
  color: var(--aio-text);
  font-family: var(--aio-font-mono);
  font-size: 12px;
  font-weight: 500;
}

.aio-key-row span {
  color: var(--aio-text-soft);
  font-size: 14px;
  line-height: 1.85;
}

.aio-compass-card {
  margin-top: 18px;
  display: grid;
  grid-template-columns: minmax(0, 1.12fr) minmax(0, 0.88fr);
  gap: 1px;
  border: 1px solid var(--aio-border);
  background: var(--aio-border);
}

.aio-verdict {
  background:
    radial-gradient(circle at top left, rgba(96, 165, 250, 0.16), transparent 22rem),
    var(--aio-bg-soft);
  padding: 22px;
}

.aio-score {
  margin: 16px 0 0;
  font-family: var(--aio-font-serif);
  font-size: 48px;
  line-height: 1;
}

.score-high {
  color: var(--aio-accent);
}

.score-mid {
  color: var(--aio-amber);
}

.score-low {
  color: var(--aio-red);
}

.score-empty {
  color: var(--aio-text-muted);
}

.aio-rating-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1px;
  background: var(--aio-border);
}

.aio-rating-cell {
  background: var(--aio-bg-soft);
  padding: 15px;
}

.aio-rating-cell span {
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 11px;
}

.aio-rating-cell strong {
  display: block;
  margin-top: 8px;
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: 23px;
  font-weight: 500;
}

@keyframes aio-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .aio-nav {
    grid-template-columns: minmax(0, 1fr) auto;
    padding: 0 18px;
  }

  .aio-nav-meta {
    display: none;
  }

  .aio-hero,
  .aio-card-grid,
  .aio-two-col,
  .aio-three-col,
  .aio-compass-card {
    grid-template-columns: 1fr;
  }

  .aio-hero-stats {
    min-width: 0;
  }

  .aio-field-grid.primary,
  .aio-field-grid.secondary {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .aio-nav {
    display: grid;
    grid-template-columns: 1fr;
    justify-items: start;
    min-height: 94px;
    align-content: center;
    gap: 8px;
    padding: 0 12px;
  }

  .aio-nav-links {
    justify-self: start;
  }

  .aio-nav-logo {
    font-size: 12px;
  }

  .aio-nav-links a {
    font-size: 11px;
    padding: 8px 9px;
  }

  .aio-page {
    padding-top: 94px;
  }

  .aio-content,
  .aio-detail-page {
    padding-left: 16px;
    padding-right: 16px;
  }

  .aio-title {
    font-size: 40px;
  }

  .aio-card {
    padding: 18px;
  }

  .aio-paper-title {
    font-size: 34px;
  }

  .aio-callout p:not(.aio-kicker) {
    font-size: 20px;
  }

  .aio-key-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .aio-token-actions,
  .aio-pagination {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
