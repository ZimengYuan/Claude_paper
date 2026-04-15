<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <button class="mb-4 text-blue-600 hover:text-blue-800" @click="goBack">
      ← Back to Library
    </button>

    <div v-if="loading" class="py-12 text-center">
      <div class="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
    </div>

    <div v-else-if="errorMessage" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorMessage }}
    </div>

    <div v-else-if="paper" class="grid grid-cols-1 gap-8 lg:grid-cols-3">
      <div class="space-y-6 lg:col-span-2">
        <div class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          这是 GitHub Pages 上的只读快照页面。收藏、标签编辑、已读状态修改和写入 Knowledge 的操作已移除。
        </div>

        <div>
          <div class="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h1 class="text-2xl font-bold text-gray-900">{{ paper.title }}</h1>
              <p class="mt-2 text-gray-600">{{ paper.authors?.join(', ') }}</p>
              <p class="mt-1 text-sm text-gray-500">{{ paper.year }} · {{ paper.journal }}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                class="rounded-full border px-3 py-1 text-xs font-medium"
                :class="paper.is_close_read ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-gray-200 bg-gray-50 text-gray-500'"
              >
                {{ paper.is_close_read ? '精读快照' : '普通快照' }}
              </span>
              <span class="rounded-full border px-3 py-1 text-xs font-medium" :class="readStatusClass(paper.read_status)">
                {{ paper.read_status === 'read' ? '已读' : '未读' }}
              </span>
            </div>
          </div>
        </div>

        <section class="rounded-xl border border-gray-200 bg-white shadow-sm">
          <div class="flex border-b border-gray-200">
            <button
              v-for="tab in contentTabs"
              :key="tab.key"
              class="relative flex items-center gap-1.5 px-5 py-3 text-sm font-medium transition-colors"
              :class="activeTab === tab.key
                ? 'text-blue-600 after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-blue-600'
                : 'text-gray-500 hover:text-gray-700'"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
              <span
                class="inline-block h-1.5 w-1.5 rounded-full"
                :class="tab.ready ? 'bg-blue-500' : 'bg-gray-300'"
              ></span>
            </button>
          </div>

          <div class="p-5">
            <div v-if="activeTab === 'summary'">
              <div v-if="summary" class="markdown-body prose max-w-none" v-html="renderMarkdown(summary)"></div>
              <p v-else class="text-sm text-gray-500">No summary found for this paper.</p>
            </div>

            <div v-if="activeTab === 'method'">
              <div v-if="method" class="markdown-body prose max-w-none" v-html="renderMarkdown(method)"></div>
              <p v-else class="text-sm text-gray-500">No method summary found for this paper.</p>
            </div>

            <div v-if="activeTab === 'score-report'">
              <div v-if="scoreReport" class="markdown-body prose max-w-none" v-html="renderMarkdown(scoreReport)"></div>
              <p v-else class="text-sm text-gray-500">No score report found for this paper.</p>
            </div>

            <div v-if="activeTab === 'report'">
              <div v-if="readableReport" class="markdown-body prose max-w-none" v-html="renderMarkdown(readableReport)"></div>
              <p v-else class="text-sm text-gray-500">No readable report found for this paper.</p>
            </div>

            <div v-if="activeTab === 'sensemaking'">
              <div v-if="hasSensemaking" class="space-y-4">
                <div class="grid gap-3 md:grid-cols-2">
                  <div
                    v-for="entry in sensemakingShiftEntries"
                    :key="entry.label"
                    class="rounded-lg border border-gray-200 bg-gray-50 p-4"
                  >
                    <div class="text-xs font-medium uppercase tracking-wide text-gray-500">{{ entry.label }}</div>
                    <p class="mt-2 text-sm text-gray-700">{{ entry.value }}</p>
                  </div>
                </div>

                <div v-if="sensemakingCoreClaim" class="rounded-lg border border-blue-100 bg-blue-50 p-4">
                  <div class="text-xs font-medium uppercase tracking-wide text-blue-700">Core Claim</div>
                  <p class="mt-2 text-sm text-blue-900">{{ sensemakingCoreClaim }}</p>
                </div>

                <div v-if="sensemakingUserPerspective" class="rounded-lg border border-purple-100 bg-purple-50 p-4">
                  <div class="text-xs font-medium uppercase tracking-wide text-purple-700">User Perspective</div>
                  <p class="mt-2 text-sm text-purple-900">{{ sensemakingUserPerspective }}</p>
                </div>

                <div v-if="sensemakingDelta" class="rounded-lg border border-amber-100 bg-amber-50 p-4">
                  <div class="text-xs font-medium uppercase tracking-wide text-amber-700">Delta</div>
                  <p class="mt-2 text-sm text-amber-900">{{ sensemakingDelta }}</p>
                </div>

                <div v-if="sensemakingOneChange" class="rounded-lg border border-green-100 bg-green-50 p-4">
                  <div class="text-xs font-medium uppercase tracking-wide text-green-700">One Change</div>
                  <p class="mt-2 text-sm text-green-900">{{ sensemakingOneChange }}</p>
                </div>

                <div v-if="sensemakingProbes.length" class="space-y-3">
                  <div class="text-xs font-medium uppercase tracking-wide text-gray-500">Probe Exchange</div>
                  <div
                    v-for="(item, index) in sensemakingProbes"
                    :key="index"
                    class="rounded-lg border border-gray-200 p-4"
                  >
                    <p class="text-xs font-medium uppercase tracking-wide text-gray-500">Probe</p>
                    <p class="mt-1 text-sm text-gray-800">{{ item.probe }}</p>
                    <p class="mt-3 text-xs font-medium uppercase tracking-wide text-gray-500">Response</p>
                    <p class="mt-1 text-sm text-gray-700">{{ item.response }}</p>
                  </div>
                </div>
              </div>

              <p v-else class="text-sm text-gray-500">
                这篇论文在当前静态快照里还没有 sensemaking 内容。
              </p>
            </div>
          </div>
        </section>
      </div>

      <div class="lg:col-span-1">
        <div class="mb-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 class="font-semibold text-gray-900">Snapshot Status</h3>
          <div class="mt-4 space-y-3 text-sm">
            <div class="flex items-center justify-between">
              <span class="text-gray-500">Read Status</span>
              <span class="font-medium text-gray-900">{{ paper.read_status === 'read' ? '已读' : '未读' }}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-gray-500">Close Read</span>
              <span class="font-medium text-gray-900">{{ paper.is_close_read ? '是' : '否' }}</span>
            </div>
            <div v-if="paper.read_at" class="flex items-center justify-between">
              <span class="text-gray-500">Read At</span>
              <span class="font-medium text-gray-900">{{ paper.read_at }}</span>
            </div>
          </div>
        </div>

        <div class="mb-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 class="font-semibold text-gray-900">Materials</h3>
          <p class="mt-1 text-xs text-gray-500">summary / method / score report / report / rating / sensemaking</p>
          <div class="mt-3 flex flex-wrap gap-2">
            <span class="rounded-full border px-2 py-0.5 text-xs" :class="materialClass(Boolean(summary))">Summary</span>
            <span class="rounded-full border px-2 py-0.5 text-xs" :class="materialClass(Boolean(method))">Method</span>
            <span class="rounded-full border px-2 py-0.5 text-xs" :class="materialClass(Boolean(scoreReport))">Score Report</span>
            <span class="rounded-full border px-2 py-0.5 text-xs" :class="materialClass(Boolean(readableReport))">Report</span>
            <span class="rounded-full border px-2 py-0.5 text-xs" :class="materialClass(Boolean(paper.rating))">Rating</span>
            <span class="rounded-full border px-2 py-0.5 text-xs" :class="materialClass(hasSensemaking)">Sensemaking</span>
          </div>
        </div>

        <div v-if="paper.rating" class="mb-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 class="mb-3 font-semibold text-gray-900">Rating</h3>
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600">Overall</span>
              <span class="font-bold" :class="ratingClass(paper.rating.overall_score)">
                {{ overallRatingText }}
              </span>
            </div>
            <div v-for="entry in ratingEntries" :key="entry.label" class="flex items-center justify-between text-sm">
              <span class="text-gray-500">{{ entry.label }}</span>
              <span>{{ entry.value }}/10</span>
            </div>
          </div>
          <div v-if="ratingNote" class="mt-3 text-sm italic text-gray-600">
            "{{ ratingNote }}"
          </div>
        </div>

        <div class="mb-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 class="mb-3 font-semibold text-gray-900">Tags</h3>
          <div v-if="paper.tags?.length" class="flex flex-wrap gap-2">
            <span
              v-for="tag in paper.tags"
              :key="tag"
              class="rounded bg-gray-100 px-2 py-1 text-sm text-gray-600"
            >
              {{ tag }}
            </span>
          </div>
          <p v-else class="text-sm text-gray-500">No tags recorded in this snapshot.</p>
        </div>

        <div v-if="parsedSource" class="mb-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 class="mb-3 font-semibold text-gray-900">Parsed Source</h3>
          <div class="space-y-3 text-sm">
            <div class="flex flex-wrap gap-2">
              <span
                v-for="file in parsedSource.files"
                :key="file.name"
                class="rounded-full border border-gray-200 bg-gray-50 px-2.5 py-1 text-xs text-gray-700"
              >
                {{ file.name }}
              </span>
            </div>
            <div class="grid grid-cols-2 gap-3 text-xs text-gray-600">
              <div>Lines: {{ parsedSource.markdown_stats?.lines || 0 }}</div>
              <div>Words: {{ parsedSource.markdown_stats?.words || 0 }}</div>
              <div>Headings: {{ parsedSource.markdown_stats?.headings || 0 }}</div>
              <div>Images: {{ parsedSource.assets?.images || 0 }}</div>
            </div>
            <div v-if="parsedFieldEntries.length" class="space-y-2">
              <div class="text-xs uppercase tracking-wide text-gray-500">Recognized Fields</div>
              <div
                v-for="entry in parsedFieldEntries"
                :key="entry.key"
                class="flex items-start justify-between gap-3 text-xs"
              >
                <span class="text-gray-500">{{ entry.key }}</span>
                <span class="break-all text-right text-gray-800">{{ entry.value }}</span>
              </div>
            </div>
            <p class="text-xs text-gray-500">{{ parsedSource.generator_input?.note }}</p>
          </div>
        </div>

        <div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 class="mb-3 font-semibold text-gray-900">Metadata</h3>
          <dl v-if="metadataEntries.length" class="space-y-2 text-sm">
            <div v-for="entry in metadataEntries" :key="entry.label">
              <dt class="text-gray-500">{{ entry.label }}</dt>
              <dd class="text-gray-900" :class="entry.label === 'DOI' ? 'break-all' : ''">{{ entry.value }}</dd>
            </div>
          </dl>
          <p v-else class="text-sm text-gray-500">No structured metadata available.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'
import katex from 'katex'

const { fetchJson } = useStaticSiteData()
const route = useRoute()
const paperId = computed(() => String(route.params.id || '').trim())

const loading = ref(true)
const errorMessage = ref('')
const paper = ref(null)
const summary = ref('')
const method = ref('')
const scoreReport = ref('')
const readableReport = ref('')
const activeTab = ref('summary')

const contentTabs = computed(() => [
  { key: 'summary', label: 'Summary', ready: Boolean(summary.value) },
  { key: 'method', label: 'Method', ready: Boolean(method.value) },
  { key: 'score-report', label: 'Score Report', ready: Boolean(scoreReport.value) },
  { key: 'report', label: 'Report', ready: Boolean(readableReport.value) },
  { key: 'sensemaking', label: 'Sensemaking', ready: hasSensemaking.value },
])

const goBack = () => navigateTo('/')

const applyPaperPayload = (payload) => {
  paper.value = payload
  summary.value = payload.summary || ''
  method.value = payload.method_summary || ''
  scoreReport.value = payload.score_report || ''
  readableReport.value = payload.readable_report || ''
}

const ratingClass = (score) => {
  if (score == null) return 'text-gray-400'
  if (score >= 8) return 'text-green-600'
  if (score >= 6) return 'text-yellow-600'
  return 'text-red-600'
}

const materialClass = (enabled) => {
  return enabled
    ? 'border-blue-200 bg-blue-50 text-blue-700'
    : 'border-gray-200 bg-gray-50 text-gray-400'
}

const readStatusClass = (status) => {
  return status === 'read'
    ? 'border-green-200 bg-green-50 text-green-700'
    : 'border-gray-200 bg-gray-50 text-gray-500'
}

const parsedSource = computed(() => paper.value?.parsed_source || null)
const hasSensemaking = computed(() => Boolean(paper.value?.sensemaking))
const parsedFieldEntries = computed(() => {
  return Object.entries(parsedSource.value?.recognized_fields || {}).map(([key, value]) => ({
    key,
    value: Array.isArray(value) ? value.join(', ') : String(value),
  }))
})

const sensemakingShiftEntries = computed(() => {
  const reconstruction = paper.value?.sensemaking?.act3_reconstruction || {}
  return [
    { label: 'Before', value: reconstruction.before },
    { label: 'After', value: reconstruction.after },
  ].filter((entry) => keepValue(entry.value))
})

const sensemakingCoreClaim = computed(() => paper.value?.sensemaking?.act1_comprehension?.core_claim || '')
const sensemakingUserPerspective = computed(() => paper.value?.sensemaking?.act1_comprehension?.user_perspective || '')
const sensemakingDelta = computed(() => paper.value?.sensemaking?.act3_reconstruction?.delta || '')
const sensemakingOneChange = computed(() => paper.value?.sensemaking?.act3_reconstruction?.one_change || '')
const sensemakingProbes = computed(() => {
  const exchange = paper.value?.sensemaking?.act2_collision?.probe_exchange
  return Array.isArray(exchange) ? exchange.filter((item) => keepValue(item?.probe) || keepValue(item?.response)) : []
})

function keepValue(value) {
  return value !== null && value !== undefined && value !== ''
}

const metadataEntries = computed(() => {
  if (paper.value == null) return []
  return [
    { label: 'Year', value: paper.value.year },
    { label: 'Journal', value: paper.value.journal },
    { label: 'Paper Type', value: paper.value.paper_type },
    { label: 'Publisher', value: paper.value.publisher },
    { label: 'ISSN', value: paper.value.issn },
    { label: 'Volume', value: paper.value.volume },
    { label: 'Issue', value: paper.value.issue },
    { label: 'Pages', value: paper.value.pages },
    { label: 'DOI', value: paper.value.doi },
    { label: 'Citations', value: paper.value.citation_count },
  ].filter((entry) => keepValue(entry.value))
})

const ratingEntries = computed(() => {
  const rating = paper.value?.rating
  if (rating == null) return []

  const compassEntries = [
    { label: '发表信号', value: rating.publication_signal },
    { label: '作者信号', value: rating.author_signal },
    { label: '引用牵引', value: rating.citation_traction },
    { label: '被引质量', value: rating.citation_quality },
    { label: '新颖性', value: rating.novelty },
    { label: '业界信号', value: rating.industry_signal },
    { label: '方向影响', value: rating.field_shaping },
  ].filter((entry) => keepValue(entry.value))

  if (compassEntries.length) return compassEntries

  return [
    { label: '创新性', value: rating.innovation },
    { label: '技术质量', value: rating.technical_quality },
    { label: '实验验证', value: rating.experimental_validation },
    { label: '写作质量', value: rating.writing_quality },
    { label: '相关性', value: rating.relevance },
  ].filter((entry) => keepValue(entry.value))
})

const ratingNote = computed(() => paper.value?.rating?.one_line_verdict || paper.value?.rating?.notes || '')

const overallRatingText = computed(() => {
  const score = paper.value?.rating?.overall_score
  if (score == null) return 'n/a'
  return `${Number(score).toFixed(1)}/10`
})

const loadPaper = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const payload = await fetchJson(`papers/${paperId.value}.json`)
    applyPaperPayload(payload)
  } catch (error) {
    console.error('Failed to load paper snapshot:', error)
    errorMessage.value = 'Failed to load this paper from the static snapshot.'
  } finally {
    loading.value = false
  }
}

const renderMathFragment = (formula, displayMode, fallback) => {
  const trimmed = String(formula || '').trim()
  if (trimmed === '') return fallback

  try {
    const rendered = katex.renderToString(trimmed, {
      displayMode,
      throwOnError: false,
    })
    return displayMode ? `<div class="math-display">${rendered}</div>` : rendered
  } catch {
    return fallback
  }
}

const protectInlineDollarMath = (text, replacements) => {
  let output = ''
  let index = 0

  while (index < text.length) {
    const current = text[index]
    if (current !== '$') {
      output += current
      index += 1
      continue
    }

    const previous = index > 0 ? text[index - 1] : ''
    const next = index + 1 < text.length ? text[index + 1] : ''
    if (previous === '\\' || next === '$' || next === ' ' || next === '\n' || next === '\t') {
      output += current
      index += 1
      continue
    }

    let cursor = index + 1
    let endIndex = -1
    while (cursor < text.length) {
      const char = text[cursor]
      if (char === '\n') break
      if (char === '$' && text[cursor - 1] !== '\\') {
        endIndex = cursor
        break
      }
      cursor += 1
    }

    if (endIndex === -1) {
      output += current
      index += 1
      continue
    }

    const rawFormula = text.slice(index + 1, endIndex)
    const formula = rawFormula.trim()
    if (formula === '' || formula.length > 400 || formula.includes('<') || formula.includes('>')) {
      output += text.slice(index, endIndex + 1)
      index = endIndex + 1
      continue
    }

    const token = `__SCHOLARAIO_MATH_${replacements.length}__`
    replacements.push({
      token,
      displayMode: false,
      html: renderMathFragment(formula, false, `$${rawFormula}$`),
    })
    output += token
    index = endIndex + 1
  }

  return output
}

const protectMathExpressions = (text) => {
  const replacements = []
  const createToken = (formula, displayMode, fallback) => {
    const token = `__SCHOLARAIO_MATH_${replacements.length}__`
    replacements.push({
      token,
      displayMode,
      html: renderMathFragment(formula, displayMode, fallback),
    })
    return token
  }

  let prepared = String(text || '')
  prepared = prepared.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => createToken(formula, true, match))
  prepared = prepared.replace(/\\\[([\s\S]+?)\\\]/g, (match, formula) => createToken(formula, true, match))
  prepared = prepared.replace(/\\\(([\s\S]+?)\\\)/g, (match, formula) => createToken(formula, false, match))
  prepared = protectInlineDollarMath(prepared, replacements)

  return { prepared, replacements }
}

const escapeRegExp = (value) => value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

const replaceMathTokens = (html, replacements) => {
  let output = html
  for (const item of replacements) {
    if (item.displayMode) {
      const blockPattern = new RegExp(`<p>\\s*${escapeRegExp(item.token)}\\s*</p>`, 'g')
      output = output.replace(blockPattern, item.html)
    }
    output = output.split(item.token).join(item.html)
  }
  return output
}

const renderMarkdown = (text) => {
  if (text == null || text === '') return ''

  try {
    const { prepared, replacements } = protectMathExpressions(text)
    const html = marked.parse(prepared)
    return replaceMathTokens(html, replacements)
  } catch (error) {
    console.error('Markdown rendering error:', error)
    return marked.parse(text)
  }
}

onMounted(() => {
  loadPaper()
})
</script>

<style>
.markdown-body {
  line-height: 1.6;
}
.markdown-body h1 {
  font-size: 1.5em;
  font-weight: bold;
  margin-top: 1em;
  margin-bottom: 0.5em;
}
.markdown-body h2 {
  font-size: 1.3em;
  font-weight: bold;
  margin-top: 1em;
  margin-bottom: 0.5em;
}
.markdown-body h3 {
  font-size: 1.1em;
  font-weight: bold;
  margin-top: 0.8em;
  margin-bottom: 0.4em;
}
.markdown-body p {
  margin-bottom: 1em;
}
.markdown-body ul,
.markdown-body ol {
  margin-left: 1.5em;
  margin-bottom: 1em;
}
.markdown-body li {
  margin-bottom: 0.25em;
}
.markdown-body code {
  background-color: #f3f4f6;
  padding: 0.125em 0.25em;
  border-radius: 0.25rem;
  font-size: 0.875em;
}
.markdown-body pre {
  background-color: #111827;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 1em;
}
.markdown-body blockquote {
  border-left: 4px solid #d1d5db;
  padding-left: 1em;
  color: #6b7280;
  margin-bottom: 1em;
}
.markdown-body hr {
  margin: 1.5em 0;
  border: 0;
  border-top: 1px solid #e5e7eb;
}
.markdown-body table {
  display: block;
  width: 100%;
  overflow-x: auto;
  border-collapse: collapse;
  margin-bottom: 1em;
}
.markdown-body th,
.markdown-body td {
  border: 1px solid #e5e7eb;
  padding: 0.5rem 0.75rem;
  text-align: left;
}
.markdown-body th {
  background-color: #f8fafc;
  font-weight: 600;
}
.markdown-body .math-display {
  margin: 1.25em 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.125rem 0.25rem;
}
.markdown-body .katex-display {
  margin: 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding: 0.25rem 0;
}
.markdown-body .katex {
  max-width: 100%;
}
</style>
