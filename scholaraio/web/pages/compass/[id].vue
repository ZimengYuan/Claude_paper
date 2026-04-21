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
      <p>正在加载 Paper Compass...</p>
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
              <span class="aio-pill">{{ card.year || 'n.d.' }}</span>
            </div>
            <h1 class="aio-paper-title">{{ card.title }}</h1>
            <p class="aio-paper-meta">
              {{ compactAuthorsText }}
            </p>
          </div>
        </div>
      </header>

      <template v-if="hasCompassContent">
        <section
          v-if="heroSummaryText || heroMetricEntries.length"
          class="aio-compass-card"
          :class="{ 'is-single': !heroSummaryText || !heroMetricEntries.length }"
        >
          <div v-if="heroSummaryText" class="aio-verdict">
            <p class="aio-kicker">核心判断</p>
            <p class="aio-note-body">{{ heroSummaryText }}</p>
          </div>

          <div v-if="heroMetricEntries.length" class="aio-metric-panel">
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

        <section v-if="hasVisibleScoreContent" id="score" class="aio-note-section">
          <div class="aio-split-top">
            <div>
              <p class="aio-kicker">价值判断</p>
              <h2>为什么这样判断</h2>
              <p class="aio-muted">只保留能解释阅读价值的评分依据和对比信息。</p>
            </div>
          </div>

          <div v-if="visibleScoreConclusion.length" class="aio-cell">
            <h3>判断补充</h3>
            <div class="aio-note-body">
              <div
                v-for="entry in visibleScoreConclusion"
                :key="entry.label"
                class="aio-key-row"
              >
                <strong>{{ entry.label }}</strong>
                <span>{{ entry.value }}</span>
              </div>
            </div>
          </div>

          <div v-if="visibleScoringRows.length" class="aio-section-stack">
            <div>
              <p class="aio-kicker">评分拆解</p>
              <h3>分项评分</h3>
            </div>
            <div class="aio-two-col">
              <article
                v-for="row in visibleScoringRows"
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

          <div v-if="visiblePeers.length" class="aio-section-stack">
            <div>
              <p class="aio-kicker">对比集合</p>
              <h3>相似论文对比集合</h3>
            </div>
            <div class="aio-three-col">
              <article
                v-for="peer in visiblePeers"
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

          <div v-if="visibleObservations.length" class="aio-section-stack">
            <div>
              <p class="aio-kicker">横向观察</p>
              <h3>横向对比观察</h3>
            </div>
            <div class="aio-three-col">
              <div
                v-for="entry in visibleObservations"
                :key="entry.label"
                class="aio-cell"
              >
                <h3>{{ entry.label }}</h3>
                <p>{{ entry.value }}</p>
              </div>
            </div>
          </div>

          <div v-if="visibleReasons.length" class="aio-section-stack">
            <div>
              <p class="aio-kicker">评分原因</p>
              <h3>分数形成原因</h3>
            </div>
            <div class="aio-three-col">
              <div
                v-for="entry in visibleReasons"
                :key="entry.label"
                class="aio-cell"
              >
                <h3>{{ entry.label }}</h3>
                <p>{{ entry.value }}</p>
              </div>
            </div>
          </div>

          <div v-if="visiblePriority.length" class="aio-cell">
            <h3>是否值得优先读</h3>
            <div class="aio-note-body">
              <div
                v-for="entry in visiblePriority"
                :key="entry.label"
                class="aio-key-row"
              >
                <strong>{{ entry.label }}</strong>
                <span>{{ entry.value }}</span>
              </div>
            </div>
          </div>
        </section>

        <section v-if="hasVisibleReadableContent" id="report" class="aio-note-section">
          <div class="aio-split-top">
            <div>
              <p class="aio-kicker">阅读补充</p>
              <h2>读前补充</h2>
              <p class="aio-muted">只展示读懂这篇论文之前真正需要补的内容。</p>
            </div>
          </div>

          <div class="aio-section-stack">
            <div v-if="visibleQuickStartMarkdown" class="aio-two-col">
              <div class="aio-cell aio-cell-accent">
                <h3>30 分钟快速起步</h3>
                <div
                  class="aio-markdown compact"
                  v-html="renderMarkdown(visibleQuickStartMarkdown)"
                ></div>
              </div>
            </div>

            <div v-if="visiblePrerequisites.length" class="aio-section-stack">
              <div>
                <p class="aio-kicker">先修知识</p>
                <h3>必学先修知识</h3>
              </div>
              <div class="aio-two-col">
                <article
                  v-for="item in visiblePrerequisites"
                  :key="item.order + '-' + item.title"
                  class="aio-cell"
                >
                  <div class="aio-split-top">
                    <span class="aio-pill">第 {{ item.order || '-' }} 步</span>
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

            <div v-if="visibleBridges.length" class="aio-section-stack">
              <div>
                <p class="aio-kicker">桥接概念</p>
                <h3>桥接知识</h3>
              </div>
              <div class="aio-three-col">
                <article
                  v-for="item in visibleBridges"
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

            <div v-if="visiblePersonalizedMarkdown" class="aio-cell">
              <h3>个性化增量</h3>
              <div
                class="aio-markdown compact"
                v-html="renderMarkdown(visiblePersonalizedMarkdown)"
              ></div>
            </div>

            <div v-if="visibleLearningOrder.length" class="aio-section-stack">
              <div>
                <p class="aio-kicker">学习顺序</p>
                <h3>建议学习顺序</h3>
              </div>
              <div class="aio-inline-list">
                <div
                  v-for="(item, index) in visibleLearningOrder"
                  :key="index"
                  class="aio-learning-step"
                >
                  <span class="aio-step-index">{{ index + 1 }}</span>
                  <p>{{ item }}</p>
                </div>
              </div>
            </div>

            <div v-if="visibleResources.length" class="aio-section-stack">
              <div>
                <p class="aio-kicker">补充资源</p>
                <h3>推荐学习资源</h3>
              </div>
              <div class="aio-two-col">
                <article
                  v-for="resource in visibleResources"
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
          </div>
        </section>
      </template>

      <section v-else class="aio-compass-empty">
        <p class="aio-kicker">Compass 尚未生成</p>
        <h2>这篇论文目前没有可展示的 Compass 内容</h2>
        <p>
          评分依据和读前补充都为空时，页面不再显示占位灰块；先回到 Todo 摘要阅读，等静态快照补齐后这里会自动呈现完整 Compass。
        </p>
        <div class="aio-empty-actions">
          <NuxtLink class="aio-button" :to="todoDetailPath">回到 Todo 摘要</NuxtLink>
          <a
            v-if="sourceLink"
            class="aio-button-secondary"
            :href="sourceLink"
            target="_blank"
            rel="noopener noreferrer"
          >
            查看原论文
          </a>
        </div>
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

const normalizeReadableText = (value) => cleanInlineMarkdown(value)
  .replace(/\s+/g, ' ')
  .trim()

const LOW_INFORMATION_VALUES = new Set([
  '',
  '-',
  '0',
  'n/a',
  'na',
  'none',
  'null',
  '信息不足',
  '暂无',
  '无',
  '待补全',
  '待判断',
])

const isLowInformationText = (value) => {
  const text = normalizeReadableText(value)
  if (!text) return true
  return LOW_INFORMATION_VALUES.has(text.toLowerCase())
}

const hasUsefulText = (value) => !isLowInformationText(value)

const hasUsefulEntry = (entry) => hasUsefulText(entry?.value)

const TEXT_TRANSLATIONS = [
  ['weak field-shaping evidence so far', '目前还没有足够证据支持其具备奠基性影响'],
  ['early promise, not yet established', '有早期潜力，但尚未形成稳定共识'],
  ['lower priority unless the user has a narrow reason to read it', '低优先级，除非你正好关注这条技术线'],
  ['solid and worth reading', '质量较稳，值得阅读'],
  ['high priority', '高优先级'],
  ['medium priority', '中等优先级'],
  ['low priority', '低优先级'],
  ['strong field-shaping evidence', '有较强的方向影响证据'],
  ['weak field-shaping evidence', '方向影响证据偏弱'],
  ['not yet established', '尚未形成稳定共识'],
  ['above median', '高于中位水平'],
  ['around median', '接近中位水平'],
  ['below median', '低于中位水平'],
  ['incomplete', '不完整'],
  ['low confidence', '低置信度'],
]

const CATEGORY_TRANSLATIONS = {
  classic: '经典',
  recent: '近期',
  survey: '综述',
  review: '综述',
}

const escapeRegExp = (value) => String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

const localizeCompassText = (value) => {
  let text = cleanInlineMarkdown(value)
  if (!text) return ''

  const exactMatch = TEXT_TRANSLATIONS.find(([source]) => text.toLowerCase() === source)
  if (exactMatch) return exactMatch[1]

  for (const [source, target] of TEXT_TRANSLATIONS) {
    text = text.replace(new RegExp(escapeRegExp(source), 'gi'), target)
  }
  return text
}

const displayEntry = (entry) => ({
  ...entry,
  value: localizeCompassText(entry.value),
})

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

const compactAuthorsText = computed(() => {
  const authors = Array.isArray(card.value?.authors) ? card.value.authors.filter(Boolean) : []
  if (!authors.length) return '作者信息缺失'
  if (authors.length <= 3) return authors.join(', ')
  return authors.slice(0, 3).join(', ') + ` 等 ${authors.length} 位作者`
})

const ratingNote = computed(() => paper.value?.rating?.one_line_verdict || paper.value?.rating?.notes || '')
const overallScore = computed(() => paper.value?.rating?.overall_score)
const overallRatingText = computed(() => {
  if (overallScore.value == null) return 'n/a'
  return Number(overallScore.value).toFixed(1)
})
const overallGradeText = computed(() => conclusionValue('等级'))
const readingPriorityText = computed(() => conclusionValue('阅读优先级'))
const heroSummaryText = computed(() => {
  if (structuredScore.value.oneLine) return localizeCompassText(structuredScore.value.oneLine)
  if (ratingNote.value) return localizeCompassText(ratingNote.value)
  return ''
})
const heroMetricEntries = computed(() => {
  const entries = []
  if (overallScore.value != null) {
    entries.push({ label: '综合评分', value: overallRatingText.value + '/10', primary: true })
  }
  if (overallGradeText.value) entries.push({ label: '等级', value: localizeCompassText(overallGradeText.value) })
  if (readingPriorityText.value) entries.push({ label: '阅读优先级', value: localizeCompassText(readingPriorityText.value) })
  return entries
})

const visibleScoreConclusion = computed(() => {
  const duplicatedLabels = new Set(['总分', '等级', '阅读优先级', '一句话判断'])
  return structuredScore.value.conclusion
    .filter((entry) => !duplicatedLabels.has(entry.label))
    .filter(hasUsefulEntry)
    .map(displayEntry)
})

const visibleScoringRows = computed(() => structuredScore.value.scoringRows.filter((row) => (
  hasUsefulText(row.dimension) &&
  (hasUsefulText(row.rationale) || hasUsefulText(row.evidence) || Number.isFinite(Number(row.score)))
)).map((row) => ({
  ...row,
  rationale: localizeCompassText(row.rationale),
  evidence: localizeCompassText(row.evidence),
})))

const visiblePeers = computed(() => structuredScore.value.peers.filter((peer) => (
  hasUsefulText(peer.title) &&
  (hasUsefulText(peer.reason) || hasUsefulText(peer.arxiv) || hasUsefulText(peer.venue))
)).map((peer) => ({
  ...peer,
  category: CATEGORY_TRANSLATIONS[String(peer.category || '').toLowerCase()] || localizeCompassText(peer.category),
  citations: localizeCompassText(peer.citations),
  reason: localizeCompassText(peer.reason),
})))

const visibleObservations = computed(() => structuredScore.value.observations.filter(hasUsefulEntry).map(displayEntry))
const visibleReasons = computed(() => structuredScore.value.reasons.filter(hasUsefulEntry).map(displayEntry))
const visiblePriority = computed(() => structuredScore.value.priority.filter(hasUsefulEntry).map(displayEntry))
const hasVisibleScoreContent = computed(() => (
  visibleScoreConclusion.value.length > 0 ||
  visibleScoringRows.value.length > 0 ||
  visiblePeers.value.length > 0 ||
  visibleObservations.value.length > 0 ||
  visibleReasons.value.length > 0 ||
  visiblePriority.value.length > 0
))

const visibleQuickStartMarkdown = computed(() => {
  const body = String(structuredReport.value.quickStartMarkdown || '').trim()
  if (!hasUsefulText(body)) return ''
  if (/#\s*论文总结|##\s*\d+\./.test(body)) return ''
  return body
})

const visiblePrerequisites = computed(() => structuredReport.value.prerequisites.filter((item) => (
  hasUsefulText(item.title) &&
  (hasUsefulText(item.reason) || hasUsefulText(item.goal) || hasUsefulText(item.evidence))
)))

const visibleBridges = computed(() => structuredReport.value.bridges.filter((item) => (
  hasUsefulText(item.title) &&
  (hasUsefulText(item.role) || hasUsefulText(item.action) || hasUsefulText(item.evidence))
)))

const visiblePersonalizedMarkdown = computed(() => {
  const body = String(structuredReport.value.personalizedMarkdown || '').trim()
  if (!hasUsefulText(body)) return ''
  if (body.includes('暂无明确已掌握项') || body.includes('按默认先修序列处理')) return ''
  return body
})

const visibleLearningOrder = computed(() => structuredReport.value.learningOrder.filter(hasUsefulText))
const visibleResources = computed(() => structuredReport.value.resources.filter((resource) => {
  const body = String(resource.body || '').trim()
  if (!hasUsefulText(resource.title) || !hasUsefulText(body)) return false
  return !/信息不足|暂无|待补全/.test(resource.title + body)
}))
const hasVisibleReadableContent = computed(() => (
  Boolean(visibleQuickStartMarkdown.value) ||
  visiblePrerequisites.value.length > 0 ||
  visibleBridges.value.length > 0 ||
  Boolean(visiblePersonalizedMarkdown.value) ||
  visibleLearningOrder.value.length > 0 ||
  visibleResources.value.length > 0
))
const hasCompassContent = computed(() => (
  Boolean(heroSummaryText.value) ||
  heroMetricEntries.value.length > 0 ||
  hasVisibleScoreContent.value ||
  hasVisibleReadableContent.value
))

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
