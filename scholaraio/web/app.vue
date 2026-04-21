<template>
  <div class="aio-shell">
    <nav class="aio-nav">
      <div class="aio-nav-links">
        <NuxtLink to="/" :class="{ active: route.path === '/' }">Todo</NuxtLink>
        <NuxtLink to="/explore" :class="{ active: route.path.startsWith('/explore') }">趋势</NuxtLink>
      </div>
      <button
        class="aio-theme-toggle"
        type="button"
        :aria-label="themeToggleLabel"
        :title="themeToggleLabel"
        @click="toggleTheme"
      >
        {{ themeIcon }}
      </button>
    </nav>
    <main class="aio-page">
      <NuxtPage />
    </main>
  </div>
</template>

<script setup>
const route = useRoute()
const theme = ref('night')

const applyTheme = (value) => {
  if (!import.meta.client) return
  document.documentElement.dataset.theme = value
}

const themeIcon = computed(() => theme.value === 'day' ? '☾' : '☀')
const themeToggleLabel = computed(() => theme.value === 'day' ? '切换夜间模式' : '切换日间模式')

const toggleTheme = () => {
  theme.value = theme.value === 'day' ? 'night' : 'day'
  applyTheme(theme.value)
  if (import.meta.client) {
    window.localStorage.setItem('scholaraio.theme', theme.value)
  }
}

onMounted(() => {
  const saved = window.localStorage.getItem('scholaraio.theme')
  if (saved === 'day' || saved === 'night') {
    theme.value = saved
  }
  applyTheme(theme.value)
})
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
  --aio-page-bg:
    radial-gradient(circle at 18% -8%, rgba(74, 222, 154, 0.10), transparent 30rem),
    radial-gradient(circle at 92% 10%, rgba(96, 165, 250, 0.08), transparent 28rem),
    var(--aio-bg);
  --aio-shell-bg: linear-gradient(180deg, rgba(13, 15, 17, 0.98), rgba(13, 15, 17, 1));
  --aio-nav-bg: rgba(13, 15, 17, 0.82);
  --aio-soft-surface: rgba(255, 255, 255, 0.03);
  --aio-panel-bg: rgba(255, 255, 255, 0.025);
  --aio-control-bg: rgba(13, 15, 17, 0.84);
  --aio-control-focus-bg: rgba(17, 21, 25, 0.95);
  --aio-writeback-bg: rgba(13, 15, 17, 0.42);
  --aio-card-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.020));
  --aio-card-hover-bg: linear-gradient(180deg, rgba(255, 255, 255, 0.075), rgba(255, 255, 255, 0.030));
  --aio-card-border: rgba(255, 255, 255, 0.15);
  --aio-card-shadow: 0 18px 42px rgba(0, 0, 0, 0.30), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  --aio-card-hover-shadow: 0 22px 52px rgba(0, 0, 0, 0.34), inset 0 1px 0 rgba(255, 255, 255, 0.07);
  --aio-card-accent: linear-gradient(180deg, rgba(74, 222, 154, 0.86), rgba(96, 165, 250, 0.58));
  --aio-button-text: #07100b;
  --aio-button-hover-bg: #6ee7ad;
  --aio-font-serif: "Noto Serif SC", "Songti SC", Georgia, serif;
  --aio-font-sans: Inter, "Noto Sans SC", "Microsoft YaHei", Arial, sans-serif;
  --aio-font-mono: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
}

:root[data-theme="day"] {
  --aio-bg: #f4f1ea;
  --aio-bg-soft: #fffaf2;
  --aio-bg-mute: #ebe5d8;
  --aio-border: rgba(35, 31, 24, 0.12);
  --aio-border-strong: rgba(35, 31, 24, 0.20);
  --aio-text: #1f1c18;
  --aio-text-soft: #514a3f;
  --aio-text-muted: #7a7164;
  --aio-accent: #137a4f;
  --aio-blue: #2563eb;
  --aio-amber: #a95f00;
  --aio-purple: #7c3aed;
  --aio-red: #be123c;
  --aio-page-bg:
    radial-gradient(circle at 16% -8%, rgba(19, 122, 79, 0.12), transparent 30rem),
    radial-gradient(circle at 92% 10%, rgba(37, 99, 235, 0.10), transparent 28rem),
    var(--aio-bg);
  --aio-shell-bg: linear-gradient(180deg, rgba(244, 241, 234, 0.98), rgba(244, 241, 234, 1));
  --aio-nav-bg: rgba(244, 241, 234, 0.86);
  --aio-soft-surface: rgba(255, 255, 255, 0.52);
  --aio-panel-bg: rgba(255, 255, 255, 0.48);
  --aio-control-bg: rgba(255, 252, 246, 0.92);
  --aio-control-focus-bg: rgba(255, 255, 255, 0.98);
  --aio-writeback-bg: rgba(255, 252, 246, 0.58);
  --aio-card-bg: rgba(255, 255, 255, 0.58);
  --aio-card-hover-bg: rgba(255, 255, 255, 0.82);
  --aio-card-border: rgba(35, 31, 24, 0.14);
  --aio-card-shadow: 0 16px 34px rgba(44, 36, 24, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.72);
  --aio-card-hover-shadow: 0 18px 38px rgba(44, 36, 24, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.82);
  --aio-card-accent: linear-gradient(180deg, rgba(19, 122, 79, 0.70), rgba(37, 99, 235, 0.46));
  --aio-button-text: #f9fff9;
  --aio-button-hover-bg: #0f6e47;
}

html {
  background: var(--aio-bg);
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--aio-page-bg);
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
  background: var(--aio-shell-bg);
}

.aio-nav {
  position: fixed;
  inset: 0 0 auto;
  z-index: 50;
  display: flex;
  min-height: 64px;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--aio-border);
  background: var(--aio-nav-bg);
  padding: 0 28px;
  backdrop-filter: blur(18px);
}

.aio-nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
  border: 1px solid var(--aio-border);
  background: var(--aio-soft-surface);
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

.aio-theme-toggle {
  position: absolute;
  right: 28px;
  display: inline-flex;
  width: 38px;
  height: 38px;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--aio-border);
  background: var(--aio-soft-surface);
  cursor: pointer;
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 15px;
  line-height: 1;
  transition: border-color 160ms ease, color 160ms ease, background 160ms ease;
}

.aio-theme-toggle:hover {
  border-color: rgba(74, 222, 154, 0.45);
  color: var(--aio-accent);
}

.aio-page {
  min-height: 100vh;
  padding-top: 64px;
}

.aio-content {
  margin: 0 auto;
  max-width: 1180px;
  padding: 18px 22px 76px;
}

.aio-hero {
  display: flex;
  flex-direction: column;
  gap: 18px;
  align-items: stretch;
  border-bottom: 1px solid var(--aio-border);
  padding: 14px 0 22px;
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
  font-size: clamp(38px, 5.2vw, 68px);
  font-weight: 500;
  line-height: 1.02;
  letter-spacing: 0;
}

.aio-hero .aio-title:first-child {
  margin-top: 0;
}

.aio-hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border: 1px solid var(--aio-border);
}

.aio-stat {
  border-right: 1px solid var(--aio-border);
  padding: 12px 14px;
}

.aio-stat:last-child {
  border-right: 0;
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
  background: var(--aio-panel-bg);
}

.aio-filter-panel {
  margin-top: 18px;
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
  background: var(--aio-control-bg);
  color: var(--aio-text);
  font-size: 14px;
  outline: none;
  padding: 12px 13px;
  transition: border-color 160ms ease, background 160ms ease;
}

.aio-input:focus,
.aio-select:focus {
  border-color: rgba(74, 222, 154, 0.60);
  background: var(--aio-control-focus-bg);
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

.aio-writeback-panel {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 16px;
  border: 1px solid var(--aio-border);
  background: var(--aio-writeback-bg);
  padding: 14px;
}

.aio-writeback-panel .aio-kicker,
.aio-writeback-panel .aio-muted {
  margin: 0;
}

.aio-writeback-panel .aio-muted {
  margin-top: 7px;
  max-width: 680px;
  line-height: 1.55;
}

.aio-button,
.aio-button-secondary,
.aio-read-toggle,
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
  color: var(--aio-button-text);
}

.aio-button:hover {
  background: var(--aio-button-hover-bg);
}

.aio-button-secondary,
.aio-read-toggle,
.aio-text-link {
  background: var(--aio-soft-surface);
  color: var(--aio-text-soft);
}

.aio-button-secondary:hover,
.aio-read-toggle:hover,
.aio-text-link:hover {
  border-color: rgba(74, 222, 154, 0.45);
  color: var(--aio-accent);
}

.aio-button:disabled,
.aio-button-secondary:disabled,
.aio-read-toggle:disabled {
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
  gap: 16px;
  align-items: start;
  margin-top: 18px;
}

.aio-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--aio-card-border);
  background: var(--aio-card-bg);
  box-shadow: var(--aio-card-shadow);
  border-radius: 4px;
  overflow: hidden;
  padding: 22px;
  position: relative;
  transition: background 160ms ease, border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
}

.aio-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: var(--aio-card-accent);
  opacity: 0.72;
  transition: opacity 160ms ease;
}

.aio-card:hover {
  border-color: var(--aio-border-strong);
  background: var(--aio-card-hover-bg);
  box-shadow: var(--aio-card-hover-shadow);
}

.aio-card:hover::before {
  opacity: 1;
}

.aio-card-main {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
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

.aio-card-top > *,
.aio-detail-topbar > *,
.aio-split-top > * {
  min-width: 0;
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

.aio-pill.is-syncing {
  border-color: rgba(167, 139, 250, 0.38);
  color: var(--aio-purple);
}

.aio-pill.is-muted {
  color: var(--aio-text-muted);
}

.aio-card-title {
  margin: 14px 0 0;
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: 23px;
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
  margin-top: 15px;
  border-top: 1px solid var(--aio-border);
  padding-top: 14px;
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

.aio-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 18px;
  padding-top: 0;
}

.aio-card-open {
  color: var(--aio-accent);
  font-family: var(--aio-font-mono);
  font-size: 12px;
}

.aio-card-open:hover {
  color: #6ee7ad;
}

.aio-read-toggle {
  min-width: 96px;
  min-height: 36px;
  padding: 0 12px;
}

.aio-read-toggle.is-read {
  border-color: rgba(74, 222, 154, 0.35);
  color: var(--aio-accent);
}

.aio-read-toggle.is-unread {
  border-color: rgba(245, 158, 11, 0.38);
  color: var(--aio-amber);
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

.aio-paper-header .aio-split-top > :first-child {
  flex: 1 1 520px;
  min-width: 0;
  max-width: 100%;
}

.aio-detail-writeback {
  margin-top: 14px;
}

.aio-paper-title {
  margin: 18px 0 0;
  max-width: 100%;
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: clamp(34px, 5.8vw, 66px);
  font-weight: 500;
  line-height: 1.08;
  letter-spacing: 0;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.aio-paper-meta {
  margin-top: 16px;
  max-width: 100%;
  color: var(--aio-text-soft);
  font-size: 14px;
  line-height: 1.8;
  overflow-wrap: anywhere;
  word-break: break-word;
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
  overflow-wrap: anywhere;
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
  font-family: var(--aio-font-sans);
  font-size: 15px;
  font-weight: 650;
  line-height: 1.45;
}

.aio-cell p {
  margin: 10px 0 0;
  color: var(--aio-text-soft);
  font-size: 14px;
  line-height: 1.9;
  overflow-wrap: anywhere;
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
  overflow-wrap: anywhere;
}

.aio-compass-card {
  margin-top: 18px;
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(260px, 0.82fr);
  gap: 1px;
  border: 1px solid var(--aio-border);
  background: var(--aio-border);
}

.aio-compass-card.is-single {
  grid-template-columns: 1fr;
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

.aio-metric-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-content: flex-start;
  background: var(--aio-bg-soft);
  padding: 20px;
}

.aio-metric {
  min-width: 128px;
  flex: 1 1 140px;
  border-left: 1px solid var(--aio-border);
  padding-left: 12px;
}

.aio-metric span {
  color: var(--aio-text-muted);
  font-family: var(--aio-font-mono);
  font-size: 11px;
}

.aio-metric strong {
  display: block;
  margin-top: 7px;
  color: var(--aio-text);
  font-family: var(--aio-font-sans);
  font-size: 16px;
  font-weight: 650;
  line-height: 1.4;
}

.aio-metric.primary {
  min-width: 160px;
  flex-basis: 100%;
  border-left-color: rgba(74, 222, 154, 0.38);
}

.aio-metric.primary strong {
  color: var(--aio-accent);
  font-family: var(--aio-font-serif);
  font-size: 34px;
  font-weight: 500;
  line-height: 1.05;
}

.aio-compass-summary {
  margin-top: 14px;
  line-height: 1.8;
}

.aio-section-stack {
  display: grid;
  gap: 16px;
  margin-top: 22px;
}

.aio-section-stack > div:first-child > h3 {
  margin: 0;
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-size: 23px;
  font-weight: 500;
}

.aio-cell-accent {
  background:
    radial-gradient(circle at top left, rgba(74, 222, 154, 0.10), transparent 18rem),
    var(--aio-bg-soft);
}

.aio-meter {
  height: 7px;
  margin-top: 14px;
  overflow: hidden;
  border: 1px solid var(--aio-border);
  background: var(--aio-bg-mute);
}

.aio-meter-fill {
  height: 100%;
  background: var(--aio-card-accent);
}

.aio-empty-note {
  margin: 18px 0 0;
  border: 1px dashed var(--aio-border-strong);
  color: var(--aio-text-muted);
  font-size: 14px;
  line-height: 1.7;
  padding: 16px;
}

.aio-source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.aio-source-link {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  border: 1px solid rgba(96, 165, 250, 0.35);
  color: var(--aio-blue);
  font-family: var(--aio-font-mono);
  font-size: 12px;
  padding: 0 11px;
}

.aio-source-link:hover {
  border-color: rgba(74, 222, 154, 0.45);
  color: var(--aio-accent);
}

.aio-inline-list {
  display: grid;
  gap: 10px;
}

.aio-learning-step {
  display: flex;
  gap: 12px;
  border: 1px solid var(--aio-border);
  background: var(--aio-bg-soft);
  padding: 14px;
}

.aio-learning-step p {
  margin: 0;
  color: var(--aio-text-soft);
  font-size: 14px;
  line-height: 1.8;
}

.aio-step-index {
  display: inline-flex;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--aio-border-strong);
  color: var(--aio-accent);
  font-family: var(--aio-font-mono);
  font-size: 12px;
}

.aio-raw-report {
  margin-top: 18px;
  overflow: hidden;
  border: 1px solid var(--aio-border);
  background: var(--aio-bg-soft);
}

.aio-raw-summary {
  cursor: pointer;
  color: var(--aio-text);
  font-family: var(--aio-font-mono);
  font-size: 12px;
  padding: 14px 16px;
}

.aio-markdown {
  border-top: 1px solid var(--aio-border);
  color: var(--aio-text-soft);
  font-size: 14px;
  line-height: 1.9;
  overflow: auto;
  padding: 16px;
}

.aio-markdown.compact {
  margin-top: 12px;
  border-top: 0;
  padding: 0;
}

.aio-markdown :where(h1, h2, h3, h4) {
  color: var(--aio-text);
  font-family: var(--aio-font-serif);
  font-weight: 500;
  line-height: 1.35;
}

.aio-markdown :where(p, ul, ol, table) {
  margin: 12px 0 0;
}

.aio-markdown a {
  color: var(--aio-blue);
}

.aio-markdown table {
  width: 100%;
  border-collapse: collapse;
}

.aio-markdown th,
.aio-markdown td {
  border: 1px solid var(--aio-border);
  padding: 8px;
  text-align: left;
  vertical-align: top;
}

@keyframes aio-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .aio-nav {
    padding: 0 18px;
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

  .aio-metric.primary {
    flex-basis: auto;
  }

  .aio-field-grid.primary,
  .aio-field-grid.secondary {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .aio-nav {
    min-height: 64px;
    padding: 0 12px;
  }

  .aio-theme-toggle {
    right: 12px;
    width: 34px;
    height: 34px;
  }

  .aio-nav-links a {
    font-size: 11px;
    padding: 8px 9px;
  }

  .aio-page {
    padding-top: 64px;
  }

  .aio-content,
  .aio-detail-page {
    padding-left: 16px;
    padding-right: 16px;
  }

  .aio-detail-page {
    padding-right: 28px;
  }

  .aio-title {
    font-size: 40px;
  }

  .aio-hero-stats {
    grid-template-columns: 1fr;
  }

  .aio-stat {
    border-right: 0;
    border-bottom: 1px solid var(--aio-border);
  }

  .aio-stat:last-child {
    border-bottom: 0;
  }

  .aio-card {
    padding: 18px;
  }

  .aio-paper-title {
    font-size: 30px;
    line-height: 1.14;
  }

  .aio-paper-header .aio-split-top {
    align-items: stretch;
    flex-direction: column;
  }

  .aio-paper-header .aio-split-top > * {
    flex: 0 1 auto;
    width: 100%;
  }

  .aio-paper-header .aio-split-top > :first-child {
    flex: 0 1 auto;
    max-width: calc(100vw - 44px);
    min-width: 0;
    width: 100%;
  }

  .aio-paper-meta {
    font-size: 13px;
    word-break: break-all;
  }

  .aio-detail-page,
  .aio-paper-header,
  .aio-note-section,
  .aio-callout,
  .aio-two-col,
  .aio-three-col,
  .aio-compass-card {
    max-width: 100%;
    overflow-x: hidden;
  }

  .aio-paper-title,
  .aio-paper-meta,
  .aio-note-body,
  .aio-callout p:not(.aio-kicker),
  .aio-cell p,
  .aio-key-row span {
    max-width: calc(100vw - 72px);
    overflow-wrap: anywhere;
    word-break: break-all;
  }

  .aio-callout p:not(.aio-kicker) {
    font-size: 20px;
  }

  .aio-key-row {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .aio-token-actions,
  .aio-writeback-panel,
  .aio-detail-topbar,
  .aio-pagination {
    align-items: stretch;
    flex-direction: column;
  }

  .aio-detail-topbar > * {
    width: 100%;
  }

  .aio-card-footer {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
