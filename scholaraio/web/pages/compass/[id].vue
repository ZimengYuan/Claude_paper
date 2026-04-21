<template>
  <div class="aio-detail-page aio-compass-detail-page">
    <div class="aio-detail-topbar">
      <button class="aio-text-link" @click="goBackToTodo">
        ← 返回 Todo 详情
      </button>

      <a
        v-if="sourceLink"
        class="aio-button-secondary"
        :href="sourceLink"
        :target="sourceLink.startsWith('http') ? '_blank' : null"
        :rel="sourceLink.startsWith('http') ? 'noopener noreferrer' : null"
      >
        查看原论文
      </a>
    </div>

    <div v-if="loading" class="aio-state">
      <div class="aio-spinner"></div>
      <p>Loading Paper Compass...</p>
    </div>

    <div v-else-if="errorMessage" class="aio-state error">
      {{ errorMessage }}
    </div>

    <article v-else-if="card">
      <header class="aio-paper-header">
        <div class="aio-split-top">
          <div>
            <div class="aio-pill-row">
              <span class="aio-pill is-ready">Paper Compass</span>
              <span class="aio-pill" :class="heroStatusClass">
                {{ heroStatusText }}
              </span>
              <span class="aio-pill">{{ card.year || 'n.d.' }}</span>
            </div>
            <h1 class="aio-paper-title">{{ card.title }}</h1>
            <p class="aio-paper-meta">
              {{ card.authors?.join(', ') || '作者信息缺失' }}
              <span v-if="card.journal"> · {{ card.journal }}</span>
              <span v-if="card.doi"> · DOI: {{ card.doi }}</span>
            </p>
          </div>
          <div class="aio-model-box">
            阅读优先级：{{ readingPriorityText || '待判断' }}
          </div>
        </div>
      </header>

      <section class="aio-compass-card">
        <div class="aio-verdict">
          <div class="aio-split-top">
            <p class="aio-kicker">核心判断</p>
            <span class="aio-pill" :class="materialClass(Boolean(scoreReport || readableReport))">
              {{ scoreReport || readableReport ? '材料已就绪' : '材料缺失' }}
            </span>
          </div>
          <p class="aio-note-body">{{ heroSummaryText }}</p>
          <p v-if="showTodoSummarySnippet" class="aio-muted aio-compass-summary">
            {{ card.one_line_summary }}
          </p>
          <div class="aio-pill-row">
            <span
              v-for="entry in heroMaterialEntries"
              :key="entry.label"
              class="aio-pill"
              :class="materialClass(entry.ready)"
            >
              {{ entry.label }}
            </span>
          </div>
        </div>

        <div class="aio-metric-panel">
          <div
            v-for="entry in heroMetricEntries"
            :key="entry.label"
            class="aio-metric"
            :class="{ primary: entry.primary }"
          >
            <span>{{ entry.label }}</span>
            <strong>{{ entry.value }}</strong>
          </div>
        </div>
      </section>

      <section id="score" class="aio-note-section">
        <div class="aio-split-top">
          <div>
            <p class="aio-kicker">Score Layer</p>
            <h2>Score Report</h2>
            <p class="aio-muted">先看结构化结论和分项评分，再按需展开原始报告。</p>
          </div>
          <span class="aio-pill" :class="materialClass(Boolean(scoreReport))">
            {{ scoreReport ? '已就绪' : '缺失' }}
          </span>
        </div>

        <div
          v-if="structuredScore.snapshot.length || structuredScore.conclusion.length || structuredScore.oneLine"
          class="aio-two-col"
        >
          <div v-if="structuredScore.snapshot.length" class="aio-cell">
            <h3>论文快照</h3>
            <div class="aio-note-body">
              <div
                v-for="entry in structuredScore.snapshot"
                :key="entry.label"
                class="aio-key-row"
              >
                <strong>{{ entry.label }}</strong>
                <span>{{ entry.value }}</span>
              </div>
            </div>
          </div>

          <div class="aio-cell">
            <h3>最终结论</h3>
            <p v-if="structuredScore.oneLine" class="aio-note-body">
              {{ structuredScore.oneLine }}
            </p>
            <div v-if="structuredScore.conclusion.length" class="aio-note-body">
              <div
                v-for="entry in structuredScore.conclusion"
                :key="entry.label"
                class="aio-key-row"
              >
                <strong>{{ entry.label }}</strong>
                <span>{{ entry.value }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="structuredScore.scoringRows.length" class="aio-section-stack">
          <div>
            <p class="aio-kicker">Scoring Breakdown</p>
            <h3>分项评分</h3>
          </div>
          <div class="aio-two-col">
            <article
              v-for="row in structuredScore.scoringRows"
              :key="row.dimension"
              class="aio-cell"
            >
              <div class="aio-split-top">
                <h3>{{ row.dimension }}</h3>
                <span class="aio-pill is-ready">{{ row.score }}/{{ row.fullMark }}</span>
              </div>
              <div class="aio-meter">
                <div
                  class="aio-meter-fill"
                  :style="{ width: scoreRatioWidth(row.score, row.fullMark) }"
                ></div>
              </div>
              <div class="aio-note-body">
                <div class="aio-key-row">
                  <strong>评分依据</strong>
                  <span>{{ row.rationale }}</span>
                </div>
                <div class="aio-key-row">
                  <strong>关键证据</strong>
                  <span>{{ row.evidence }}</span>
                </div>
              </div>
            </article>
          </div>
        </div>

        <div v-if="structuredScore.peers.length" class="aio-section-stack">
          <div>
            <p class="aio-kicker">Peer Set</p>
            <h3>相似论文对比集合</h3>
          </div>
          <div class="aio-three-col">
            <article
              v-for="peer in structuredScore.peers"
              :key="peer.peer + '-' + peer.title"
              class="aio-cell"
            >
              <div class="aio-pill-row">
                <span class="aio-pill">{{ peer.peer }}</span>
                <span v-if="peer.category" class="aio-pill is-ready">{{ peer.category }}</span>
                <span v-if="peer.year" class="aio-pill">{{ peer.year }}</span>
              </div>
              <h3>{{ peer.title }}</h3>
              <p v-if="peer.venue" class="aio-muted">{{ peer.venue }}</p>
              <p v-if="peer.citations" class="aio-muted">引用量 {{ peer.citations }}</p>
              <p>{{ peer.reason }}</p>
              <a
                v-if="peer.arxiv"
                class="aio-source-link"
                :href="peer.arxiv"
                target="_blank"
                rel="noopener noreferrer"
              >
                查看来源
              </a>
            </article>
          </div>
        </div>

        <div v-if="structuredScore.observations.length" class="aio-section-stack">
          <div>
            <p class="aio-kicker">Comparison Notes</p>
            <h3>横向对比观察</h3>
          </div>
          <div class="aio-three-col">
            <div
              v-for="entry in structuredScore.observations"
              :key="entry.label"
              class="aio-cell"
            >
              <h3>{{ entry.label }}</h3>
              <p>{{ entry.value }}</p>
            </div>
          </div>
        </div>

        <div v-if="structuredScore.reasons.length" class="aio-section-stack">
          <div>
            <p class="aio-kicker">Score Rationale</p>
            <h3>分数形成原因</h3>
          </div>
          <div class="aio-three-col">
            <div
              v-for="entry in structuredScore.reasons"
              :key="entry.label"
              class="aio-cell"
            >
              <h3>{{ entry.label }}</h3>
              <p>{{ entry.value }}</p>
            </div>
          </div>
        </div>

        <div v-if="structuredScore.priority.length || structuredScore.sources.length" class="aio-two-col">
          <div v-if="structuredScore.priority.length" class="aio-cell">
            <h3>是否值得优先读</h3>
            <div class="aio-note-body">
              <div
                v-for="entry in structuredScore.priority"
                :key="entry.label"
                class="aio-key-row"
              >
                <strong>{{ entry.label }}</strong>
                <span>{{ entry.value }}</span>
              </div>
            </div>
          </div>

          <div v-if="structuredScore.sources.length" class="aio-cell">
            <h3>Sources</h3>
            <div class="aio-source-list">
              <a
                v-for="source in structuredScore.sources"
                :key="source.url"
                class="aio-source-link"
                :href="source.url"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ source.label || source.url }}
              </a>
            </div>
          </div>
        </div>

        <details v-if="scoreReport" class="aio-raw-report">
          <summary class="aio-raw-summary">查看原始 Score Report 文本</summary>
          <div
            class="aio-markdown"
            v-html="renderMarkdown(scoreReport)"
          ></div>
        </details>
        <p v-else class="aio-empty-note">
          当前静态快照里还没有这篇论文的评分报告。
        </p>
      </section>

      <section id="report" class="aio-note-section">
        <div class="aio-split-top">
          <div>
            <p class="aio-kicker">Readable Layer</p>
            <h2>Report / Learnpath</h2>
            <p class="aio-muted">把学习路径拆成可扫读的信息块，优先看先修、顺序和快速起步。</p>
          </div>
          <span class="aio-pill" :class="materialClass(Boolean(readableReport))">
            {{ readableReport ? '已就绪' : '缺失' }}
          </span>
        </div>

        <div v-if="readableReport && structuredReport.hasStructuredContent" class="aio-section-stack">
          <div class="aio-two-col">
            <div class="aio-cell">
              <h3>论文快照</h3>
              <div class="aio-note-body">
                <div
                  v-for="entry in structuredReport.snapshot"
                  :key="entry.label"
                  class="aio-key-row"
                >
                  <strong>{{ entry.label }}</strong>
                  <span>{{ entry.value }}</span>
                </div>
              </div>
            </div>

            <div class="aio-cell aio-cell-accent">
              <h3>30 分钟快速起步</h3>
              <div
                class="aio-markdown compact"
                v-html="renderMarkdown(structuredReport.quickStartMarkdown || '当前报告里还没有快速起步块。')"
              ></div>
            </div>
          </div>

          <div v-if="structuredReport.prerequisites.length" class="aio-section-stack">
            <div>
              <p class="aio-kicker">Prerequisites</p>
              <h3>必学先修知识</h3>
            </div>
            <div class="aio-two-col">
              <article
                v-for="item in structuredReport.prerequisites"
                :key="item.order + '-' + item.title"
                class="aio-cell"
              >
                <div class="aio-split-top">
                  <span class="aio-pill">Step {{ item.order || '-' }}</span>
                  <span v-if="item.time" class="aio-muted">{{ item.time }}</span>
                </div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.reason }}</p>
                <div class="aio-note-body">
                  <div v-if="item.goal" class="aio-key-row">
                    <strong>最小目标</strong>
                    <span>{{ item.goal }}</span>
                  </div>
                  <div v-if="item.location" class="aio-key-row">
                    <strong>论文位置</strong>
                    <span>{{ item.location }}</span>
                  </div>
                  <div v-if="item.evidence" class="aio-key-row">
                    <strong>证据锚点</strong>
                    <span>{{ item.evidence }}</span>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <div v-if="structuredReport.bridges.length" class="aio-section-stack">
            <div>
              <p class="aio-kicker">Bridge Topics</p>
              <h3>桥接知识</h3>
            </div>
            <div class="aio-three-col">
              <article
                v-for="item in structuredReport.bridges"
                :key="item.title"
                class="aio-cell"
              >
                <h3>{{ item.title }}</h3>
                <div class="aio-note-body">
                  <div v-if="item.role" class="aio-key-row">
                    <strong>角色</strong>
                    <span>{{ item.role }}</span>
                  </div>
                  <div v-if="item.location" class="aio-key-row">
                    <strong>论文位置</strong>
                    <span>{{ item.location }}</span>
                  </div>
                  <div v-if="item.evidence" class="aio-key-row">
                    <strong>证据</strong>
                    <span>{{ item.evidence }}</span>
                  </div>
                  <div v-if="item.action" class="aio-key-row">
                    <strong>建议动作</strong>
                    <span>{{ item.action }}</span>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <div v-if="structuredReport.personalizedMarkdown" class="aio-cell">
            <h3>个性化增量</h3>
            <div
              class="aio-markdown compact"
              v-html="renderMarkdown(structuredReport.personalizedMarkdown)"
            ></div>
          </div>

          <div v-if="structuredReport.learningOrder.length" class="aio-section-stack">
            <div>
              <p class="aio-kicker">Learning Order</p>
              <h3>建议学习顺序</h3>
            </div>
            <div class="aio-inline-list">
              <div
                v-for="(item, index) in structuredReport.learningOrder"
                :key="index"
                class="aio-learning-step"
              >
                <span class="aio-step-index">{{ index + 1 }}</span>
                <p>{{ item }}</p>
              </div>
            </div>
          </div>

          <div v-if="structuredReport.resources.length" class="aio-section-stack">
            <div>
              <p class="aio-kicker">Resources</p>
              <h3>推荐学习资源</h3>
            </div>
            <div class="aio-two-col">
              <article
                v-for="resource in structuredReport.resources"
                :key="resource.title"
                class="aio-cell"
              >
                <h3>{{ resource.title }}</h3>
                <div
                  class="aio-markdown compact"
                  v-html="renderMarkdown(resource.body)"
                ></div>
              </article>
            </div>
          </div>

          <div v-if="structuredReport.sources.length" class="aio-cell">
            <h3>Sources</h3>
            <div class="aio-source-list">
              <a
                v-for="entry in structuredReport.sources"
                :key="entry.url"
                class="aio-source-link"
                :href="entry.url"
                target="_blank"
                rel="noopener noreferrer"
              >
                {{ entry.label || entry.url }}
              </a>
            </div>
          </div>
        </div>

        <div
          v-else-if="readableReport"
          class="aio-markdown aio-raw-report"
          v-html="renderMarkdown(readableReport)"
        ></div>
        <p v-else class="aio-empty-note">
          当前静态快照里还没有这篇论文的可读报告。
        </p>
      </section>
    </article>
  </div>
</template>

<script setup>
import { marked } from 'marked'

const { fetchJson } = useStaticSiteData()
const route = useRoute()
const routeId = computed(() => String(route.params.id || '').trim())

const loading = ref(true)
const errorMessage = ref('')
const card = ref(null)
const paper = ref(null)
const scoreReport = ref('')
const readableReport = ref('')

const todoDetailPath = computed(() => '/todo/' + routeId.value)

useHead(() => ({
  title: card.value ? card.value.title + ' | Paper Compass' : 'Paper Compass',
}))

const cleanInlineMarkdown = (value) => String(value || '')
  .replace(/\*\*/g, '')
  .replace(/`/g, '')
  .replace(/\[(.*?)\]\((.*?)\)/g, '$1')
  .replace(/^#+\s*/gm, '')
  .trim()

const materialClass = (enabled) => {
  return enabled
    ? 'is-ready'
    : 'is-muted'
}

const sourceLink = computed(() => {
  const doi = String(card.value?.doi || '').trim()
  return doi ? 'https://doi.org/' + doi : ''
})

const splitMarkdownSections = (markdown) => {
  const normalized = String(markdown || '').replace(/\r/g, '')
  const sections = []
  let currentTitle = ''
  let currentLines = []

  for (const line of normalized.split('\n')) {
    const match = line.match(/^##\s+(.+)$/)
    if (match) {
      if (currentTitle) {
        sections.push({ title: currentTitle, body: currentLines.join('\n').trim() })
      }
      currentTitle = cleanInlineMarkdown(match[1])
      currentLines = []
      continue
    }
    if (currentTitle) currentLines.push(line)
  }

  if (currentTitle) {
    sections.push({ title: currentTitle, body: currentLines.join('\n').trim() })
  }

  return sections
}

const findSectionBody = (sections, keyword) => {
  const section = sections.find((entry) => entry.title.includes(keyword))
  return section ? section.body : ''
}

const parseBulletEntries = (body) => {
  return String(body || '')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('- '))
    .map((line) => line.slice(2).trim())
    .map((line) => {
      const index = line.indexOf(':')
      if (index === -1) return { label: '', value: cleanInlineMarkdown(line) }
      return {
        label: cleanInlineMarkdown(line.slice(0, index)),
        value: cleanInlineMarkdown(line.slice(index + 1)),
      }
    })
    .filter((entry) => entry.label || entry.value)
}

const parseMarkdownTable = (body) => {
  const lines = String(body || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  const tableLines = []
  let collecting = false
  for (const line of lines) {
    if (line.startsWith('|')) {
      tableLines.push(line)
      collecting = true
      continue
    }
    if (collecting) break
  }

  if (tableLines.length < 3) return []

  const parseRow = (line) => line.split('|').slice(1, -1).map((cell) => cleanInlineMarkdown(cell))
  const headers = parseRow(tableLines[0])
  return tableLines.slice(2).map((line) => {
    const cells = parseRow(line)
    if (cells.length !== headers.length) return null
    const row = {}
    headers.forEach((header, index) => {
      row[header] = cells[index]
    })
    return row
  }).filter(Boolean)
}

const parseOrderedItems = (body) => {
  return String(body || '')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => /^\d+\.\s+/.test(line))
    .map((line) => cleanInlineMarkdown(line.replace(/^\d+\.\s+/, '')))
}

const parseSubsections = (body) => {
  const normalized = String(body || '').replace(/\r/g, '')
  const sections = []
  let currentTitle = ''
  let currentLines = []

  for (const line of normalized.split('\n')) {
    const match = line.match(/^###\s+(.+)$/)
    if (match) {
      if (currentTitle) {
        sections.push({ title: cleanInlineMarkdown(currentTitle), body: currentLines.join('\n').trim() })
      }
      currentTitle = match[1]
      currentLines = []
      continue
    }
    if (currentTitle) currentLines.push(line)
  }

  if (currentTitle) {
    sections.push({ title: cleanInlineMarkdown(currentTitle), body: currentLines.join('\n').trim() })
  }

  return sections.filter((entry) => entry.body)
}

const parseSourceLinks = (body) => {
  return String(body || '')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('- '))
    .map((line) => line.slice(2).trim())
    .map((line) => {
      const match = line.match(/https?:\/\/\S+/)
      const url = match ? match[0] : ''
      const label = cleanInlineMarkdown(url ? line.replace(url, '').replace(/[\s:-]+$/, '') : line)
      return { label: label || url, url }
    })
    .filter((entry) => entry.url)
}

const parseReadableReport = (markdown) => {
  const sections = splitMarkdownSections(markdown)
  const prerequisites = parseMarkdownTable(findSectionBody(sections, '必学先修知识')).map((row) => ({
    order: row['顺序'] || '',
    title: row['知识点'] || '',
    reason: row['为什么必学'] || '',
    location: row['论文使用位置'] || '',
    evidence: row['证据锚点'] || '',
    goal: row['最小学习目标'] || '',
    time: row['预计时间'] || '',
  })).filter((entry) => entry.title)

  const bridges = parseMarkdownTable(findSectionBody(sections, '桥接知识')).map((row) => ({
    title: row['知识点'] || '',
    role: row['角色'] || '',
    location: row['论文使用位置'] || '',
    evidence: row['证据'] || '',
    action: row['建议动作'] || '',
  })).filter((entry) => entry.title)

  return {
    snapshot: parseBulletEntries(findSectionBody(sections, '论文快照')),
    prerequisites,
    bridges,
    personalizedMarkdown: findSectionBody(sections, '个性化增量'),
    resources: parseSubsections(findSectionBody(sections, '推荐学习资源')),
    learningOrder: parseOrderedItems(findSectionBody(sections, '建议学习顺序')),
    quickStartMarkdown: findSectionBody(sections, '30 分钟快速起步'),
    sources: parseSourceLinks(findSectionBody(sections, 'Sources')),
    hasStructuredContent: Boolean(markdown) && (
      prerequisites.length > 0 ||
      bridges.length > 0 ||
      parseBulletEntries(findSectionBody(sections, '论文快照')).length > 0 ||
      parseSubsections(findSectionBody(sections, '推荐学习资源')).length > 0 ||
      parseOrderedItems(findSectionBody(sections, '建议学习顺序')).length > 0 ||
      Boolean(findSectionBody(sections, '30 分钟快速起步'))
    ),
  }
}

const parseScoreReport = (markdown) => {
  const sections = splitMarkdownSections(markdown)
  const conclusionEntries = parseBulletEntries(findSectionBody(sections, '最终结论'))

  return {
    snapshot: parseBulletEntries(findSectionBody(sections, '论文快照')),
    conclusion: conclusionEntries.filter((entry) => entry.label && entry.label !== '一句话判断'),
    oneLine: conclusionEntries.find((entry) => entry.label === '一句话判断')?.value || '',
    scoringRows: parseMarkdownTable(findSectionBody(sections, '分项评分')).map((row) => ({
      dimension: row['维度'] || '',
      fullMark: row['满分'] || '',
      score: row['得分'] || '',
      rationale: row['评分依据'] || '',
      evidence: row['关键证据'] || '',
    })).filter((row) => row.dimension),
    peers: parseMarkdownTable(findSectionBody(sections, '相似论文对比集合')).map((row) => ({
      peer: row['Peer'] || '',
      category: row['类别'] || '',
      title: row['论文'] || '',
      arxiv: row['arXiv'] || '',
      year: row['年份'] || '',
      venue: row['Venue'] || '',
      citations: row['引用量'] || '',
      reason: row['选入理由'] || '',
    })).filter((row) => row.title),
    observations: parseBulletEntries(findSectionBody(sections, '横向对比观察')),
    reasons: parseBulletEntries(findSectionBody(sections, '分数形成原因')),
    priority: parseBulletEntries(findSectionBody(sections, '是否值得优先读')),
    sources: parseSourceLinks(findSectionBody(sections, 'Sources')),
  }
}

const structuredReport = computed(() => parseReadableReport(readableReport.value))
const structuredScore = computed(() => parseScoreReport(scoreReport.value))

const conclusionValue = (label) => {
  return structuredScore.value.conclusion.find((entry) => entry.label === label)?.value || ''
}

const ratingNote = computed(() => paper.value?.rating?.one_line_verdict || paper.value?.rating?.notes || '')
const overallScore = computed(() => paper.value?.rating?.overall_score)
const overallRatingText = computed(() => {
  if (overallScore.value == null) return 'n/a'
  return Number(overallScore.value).toFixed(1)
})
const overallGradeText = computed(() => conclusionValue('等级'))
const readingPriorityText = computed(() => conclusionValue('阅读优先级'))
const heroSummaryText = computed(() => {
  if (structuredScore.value.oneLine) return structuredScore.value.oneLine
  if (ratingNote.value) return ratingNote.value
  if (card.value?.one_line_summary) return card.value.one_line_summary
  return '当前静态快照里还没有更细的 verdict，完整内容会随着评分报告一并更新。'
})
const showTodoSummarySnippet = computed(() => {
  const summary = String(card.value?.one_line_summary || '').trim()
  return Boolean(summary) && summary !== heroSummaryText.value
})
const heroMaterialEntries = computed(() => [
  { label: 'Score Report', ready: Boolean(scoreReport.value) },
  { label: 'Learnpath Report', ready: Boolean(readableReport.value) },
  { label: '结构化 Rating', ready: Boolean(paper.value?.rating) },
])
const heroMetricEntries = computed(() => {
  const entries = []
  if (overallScore.value != null) {
    entries.push({ label: 'Overall Score', value: overallRatingText.value + '/10', primary: true })
  }
  if (overallGradeText.value) entries.push({ label: '等级', value: overallGradeText.value })
  if (readingPriorityText.value) entries.push({ label: '阅读优先级', value: readingPriorityText.value })
  entries.push({ label: '材料状态', value: heroStatusText.value })
  return entries
})
const heroStatusText = computed(() => {
  const readyCount = heroMaterialEntries.value.filter((entry) => entry.ready).length
  if (readyCount === heroMaterialEntries.value.length) return '评分与报告已就绪'
  if (readyCount > 0) return '部分材料已就绪'
  return '材料待补全'
})
const heroStatusClass = computed(() => {
  const readyCount = heroMaterialEntries.value.filter((entry) => entry.ready).length
  if (readyCount === heroMaterialEntries.value.length) return 'is-ready'
  if (readyCount > 0) return 'is-syncing'
  return 'is-muted'
})
const scoreRatioWidth = (score, fullMark) => {
  const earned = Number(score)
  const total = Number(fullMark)
  if (!Number.isFinite(earned) || !Number.isFinite(total) || total <= 0) return '0%'
  return String(Math.min(Math.max(earned / total, 0), 1) * 100) + '%'
}

const goBackToTodo = () => navigateTo(todoDetailPath.value)

const renderMarkdown = (text) => {
  if (!text) return ''
  try {
    return marked.parse(String(text))
  } catch (error) {
    console.error('Markdown rendering error:', error)
    return ''
  }
}

const applyPaperPayload = (payload) => {
  paper.value = payload
  scoreReport.value = payload?.score_report || ''
  readableReport.value = payload?.readable_report || ''
}

const loadLinkedPaper = async (matchedCard) => {
  paper.value = null
  scoreReport.value = ''
  readableReport.value = ''

  const linkedRouteId = String(matchedCard?.paper_route_id || '').trim()
  if (!linkedRouteId) return

  try {
    const payload = await fetchJson('papers/' + linkedRouteId + '.json')
    applyPaperPayload(payload)
  } catch (error) {
    console.error('Failed to load linked paper snapshot:', error)
  }
}

const loadCard = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const todoData = await fetchJson('todo-cards.json')
    const cards = Array.isArray(todoData?.cards) ? todoData.cards : []
    const matched = cards.find((item) => item.route_id === routeId.value)
    if (!matched) {
      throw new Error('Paper Compass item not found in snapshot.')
    }
    card.value = {
      ...matched,
      read_status: 'unread',
    }
    await loadLinkedPaper(matched)
  } catch (error) {
    console.error('Failed to load compass detail:', error)
    errorMessage.value = 'Failed to load Paper Compass detail.'
  } finally {
    loading.value = false
  }
}

onMounted(loadCard)
</script>
