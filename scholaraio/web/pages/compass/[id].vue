<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,_#f8fafc_0%,_#eef2ff_32%,_#f8fafc_100%)]">
    <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <button class="text-sm font-medium text-blue-600 transition hover:text-blue-800" @click="goBackToTodo">
          ← 返回 Todo 详情
        </button>

        <div class="flex flex-wrap gap-3">
          <a
            v-if="paperDetailLink"
            class="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
            :href="paperDetailLink"
          >
            论文详情
          </a>
          <a
            v-if="sourceLink"
            class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
            :href="sourceLink"
            :target="sourceLink.startsWith('http') ? '_blank' : null"
            :rel="sourceLink.startsWith('http') ? 'noopener noreferrer' : null"
          >
            查看原论文
          </a>
        </div>
      </div>

      <div v-if="loading" class="py-20 text-center">
        <div class="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
        <p class="mt-4 text-sm text-slate-500">Loading Paper Compass...</p>
      </div>

      <div v-else-if="errorMessage" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ errorMessage }}
      </div>

      <div v-else-if="card" class="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_320px]">
        <div class="space-y-6">
          <section id="overview" class="relative overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-sm">
            <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.16),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(15,23,42,0.08),_transparent_32%)]"></div>
            <div class="relative p-8">
              <div class="flex flex-wrap items-start justify-between gap-6">
                <div class="max-w-3xl">
                  <div class="flex flex-wrap items-center gap-2">
                    <span class="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-blue-700">
                      Paper Compass
                    </span>
                    <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-500">
                      {{ card.generated_with_model || 'gpt-5.4-mini' }}
                    </span>
                    <span
                      class="rounded-full px-3 py-1 text-xs font-medium"
                      :class="paper?.rating ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'"
                    >
                      {{ paper?.rating ? '评分已导出' : '评分待补全' }}
                    </span>
                  </div>

                  <h1 class="mt-5 text-4xl font-semibold leading-tight text-slate-950">{{ card.title }}</h1>
                  <p class="mt-4 text-sm text-slate-600">{{ card.authors?.join(', ') || '作者信息缺失' }}</p>
                  <p class="mt-1 text-xs text-slate-500">
                    {{ card.year || '年份未知' }}<span v-if="card.journal"> · {{ card.journal }}</span>
                    <span v-if="card.doi"> · DOI: {{ card.doi }}</span>
                  </p>

                  <div class="mt-8 grid gap-4 lg:grid-cols-2">
                    <div class="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                      <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Todo Summary</p>
                      <p class="mt-3 text-base leading-8 text-slate-800">{{ card.one_line_summary }}</p>
                    </div>
                    <div class="rounded-3xl border border-slate-200 bg-white p-5">
                      <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Compass Verdict</p>
                      <p class="mt-3 text-base leading-8 text-slate-800">
                        {{ ratingNote || '当前静态快照里还没有更细的 verdict，完整内容会随着评分报告一并更新。' }}
                      </p>
                    </div>
                  </div>
                </div>

                <div class="w-full max-w-sm rounded-[28px] border border-slate-900 bg-[linear-gradient(135deg,_#020617,_#111827_54%,_#1d4ed8)] p-6 text-white shadow-lg">
                  <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-300">Overall Score</p>
                  <div class="mt-4 flex items-end gap-3">
                    <p class="text-5xl font-semibold leading-none">{{ overallRatingText }}</p>
                    <span class="pb-1 text-sm text-slate-300">/ 10</span>
                  </div>
                  <p class="mt-5 text-sm leading-8 text-slate-100">
                    {{ overallSummaryText }}
                  </p>
                  <div class="mt-6 grid grid-cols-3 gap-3">
                    <div
                      v-for="entry in materialEntries"
                      :key="entry.label"
                      class="rounded-2xl border border-white/10 bg-white/10 px-3 py-3 text-center"
                    >
                      <p class="text-[11px] uppercase tracking-wide text-slate-300">{{ entry.label }}</p>
                      <p class="mt-2 text-sm font-semibold text-white">{{ entry.ready ? 'Ready' : 'Pending' }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section id="score" class="rounded-[32px] border border-slate-200 bg-white p-6 shadow-sm scroll-mt-24">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Rubric Grid</p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-950">评分概览</h2>
                <p class="mt-2 text-sm text-slate-500">把整体判断拆成维度，先看 score shape，再决定是否细读原始报告。</p>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                {{ ratingEntries.length ? `${ratingEntries.length} 个维度` : '暂无结构化评分' }}
              </div>
            </div>

            <div v-if="ratingEntries.length" class="mt-6 grid gap-4 md:grid-cols-2">
              <div
                v-for="entry in ratingEntries"
                :key="entry.label"
                class="rounded-3xl border border-slate-200 bg-slate-50 p-5"
              >
                <div class="flex items-center justify-between gap-4">
                  <p class="text-sm font-semibold text-slate-900">{{ entry.label }}</p>
                  <p class="text-lg font-semibold text-slate-950">{{ entry.value }}/10</p>
                </div>
                <div class="mt-4 h-2 overflow-hidden rounded-full bg-slate-200">
                  <div
                    class="h-full rounded-full bg-[linear-gradient(90deg,_#1d4ed8,_#60a5fa)]"
                    :style="{ width: scoreBarWidth(entry.value) }"
                  ></div>
                </div>
              </div>
            </div>
            <p v-else class="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-500">
              当前静态快照里还没有结构化评分，但独立页面已经预留好位置；后续补评分后会直接落到这里。
            </p>
          </section>

          <section id="score-report" class="rounded-[32px] border border-slate-200 bg-white p-6 shadow-sm scroll-mt-24">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Primary Report</p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-950">Score Report</h2>
                <p class="mt-2 text-sm text-slate-500">保留原始评分报告，方便直接核对判断依据，而不是只看最终分数。</p>
              </div>
              <span class="rounded-full border px-3 py-1 text-xs font-medium" :class="materialClass(Boolean(scoreReport))">
                {{ scoreReport ? '已就绪' : '缺失' }}
              </span>
            </div>

            <div
              v-if="scoreReport"
              class="markdown-body prose prose-slate mt-6 max-w-none rounded-[28px] border border-slate-200 bg-slate-50/80 p-6 prose-headings:font-semibold prose-h1:text-2xl prose-h2:mt-8 prose-p:leading-8 prose-li:leading-7"
              v-html="renderMarkdown(scoreReport)"
            ></div>
            <p v-else class="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-500">
              当前静态快照里还没有这篇论文的评分报告。
            </p>
          </section>

          <section id="report" class="rounded-[32px] border border-slate-200 bg-white p-6 shadow-sm scroll-mt-24">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Readable Layer</p>
                <h2 class="mt-2 text-2xl font-semibold text-slate-950">Report / Learnpath</h2>
                <p class="mt-2 text-sm text-slate-500">把学习路径和可读报告单独放一层，避免和评分逻辑混在一起。</p>
              </div>
              <span class="rounded-full border px-3 py-1 text-xs font-medium" :class="materialClass(Boolean(readableReport))">
                {{ readableReport ? '已就绪' : '缺失' }}
              </span>
            </div>

            <div
              v-if="readableReport"
              class="markdown-body prose prose-slate mt-6 max-w-none rounded-[28px] border border-slate-200 bg-white p-6 prose-headings:font-semibold prose-h1:text-2xl prose-h2:mt-8 prose-p:leading-8 prose-li:leading-7"
              v-html="renderMarkdown(readableReport)"
            ></div>
            <p v-else class="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-500">
              当前静态快照里还没有这篇论文的可读报告。
            </p>
          </section>
        </div>

        <aside class="space-y-6 xl:sticky xl:top-8 xl:self-start">
          <section class="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Quick Nav</p>
            <div class="mt-4 space-y-2">
              <a
                v-for="item in sectionLinks"
                :key="item.href"
                class="block rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                :href="item.href"
              >
                {{ item.label }}
              </a>
            </div>
          </section>

          <section class="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm">
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Snapshot Status</p>
            <div class="mt-4 space-y-3 text-sm">
              <div class="flex items-center justify-between">
                <span class="text-slate-500">Score Report</span>
                <span class="font-medium text-slate-900">{{ scoreReport ? 'Ready' : 'Pending' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-500">Report</span>
                <span class="font-medium text-slate-900">{{ readableReport ? 'Ready' : 'Pending' }}</span>
              </div>
              <div class="flex items-center justify-between">
                <span class="text-slate-500">Rating</span>
                <span class="font-medium text-slate-900">{{ paper?.rating ? overallRatingText : 'Pending' }}</span>
              </div>
            </div>
          </section>

          <section id="snapshot" class="rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm scroll-mt-24">
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Linked Paper Snapshot</p>
            <dl v-if="linkedPaperEntries.length" class="mt-4 space-y-3 text-sm">
              <div v-for="entry in linkedPaperEntries" :key="entry.label">
                <dt class="text-slate-500">{{ entry.label }}</dt>
                <dd class="mt-1 break-all text-slate-900">{{ entry.value }}</dd>
              </div>
            </dl>
            <p v-else class="mt-4 text-sm text-slate-500">当前还没读取到关联论文的静态详情。</p>
          </section>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'

const { fetchJson } = useStaticSiteData()
const runtimeConfig = useRuntimeConfig()
const route = useRoute()
const routeId = computed(() => String(route.params.id || '').trim())

const loading = ref(true)
const errorMessage = ref('')
const card = ref(null)
const paper = ref(null)
const scoreReport = ref('')
const readableReport = ref('')

const paperRouteId = computed(() => String(card.value?.paper_route_id || '').trim())
const appBaseUrl = computed(() => {
  const value = String(runtimeConfig.app.baseURL || '/')
  return value.endsWith('/') ? value : `${value}/`
})
const todoDetailLink = computed(() => `${appBaseUrl.value}todo/${routeId.value}`)
const paperDetailLink = computed(() => {
  if (!paperRouteId.value) return ''
  return `${appBaseUrl.value}paper/${paperRouteId.value}`
})

useHead(() => ({
  title: card.value ? `${card.value.title} | Paper Compass` : 'Paper Compass',
}))

const keepValue = (value) => value !== null && value !== undefined && value !== ''

const materialClass = (enabled) => {
  return enabled
    ? 'border-blue-200 bg-blue-50 text-blue-700'
    : 'border-slate-200 bg-slate-50 text-slate-400'
}

const sourceLink = computed(() => {
  const doi = String(card.value?.doi || '').trim()
  if (doi) return `https://doi.org/${doi}`
  return paperDetailLink.value
})

const materialEntries = computed(() => [
  { label: 'Score', ready: Boolean(scoreReport.value) },
  { label: 'Report', ready: Boolean(readableReport.value) },
  { label: 'Rating', ready: Boolean(paper.value?.rating) },
])

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

const linkedPaperEntries = computed(() => {
  if (paper.value == null) return []
  return [
    { label: '标题', value: paper.value.title },
    { label: '作者', value: Array.isArray(paper.value.authors) ? paper.value.authors.join(', ') : paper.value.authors },
    { label: '年份', value: paper.value.year },
    { label: '期刊 / Venue', value: paper.value.journal },
    { label: 'DOI', value: paper.value.doi },
    { label: 'Route ID', value: paperRouteId.value },
  ].filter((entry) => keepValue(entry.value))
})

const ratingNote = computed(() => paper.value?.rating?.one_line_verdict || paper.value?.rating?.notes || '')
const overallScore = computed(() => paper.value?.rating?.overall_score)
const overallRatingText = computed(() => {
  if (overallScore.value == null) return 'n/a'
  return Number(overallScore.value).toFixed(1)
})
const overallSummaryText = computed(() => {
  if (ratingNote.value) return ratingNote.value
  if (overallScore.value == null) {
    return '当前还没有完整的结构化评分，但相关入口和版式已经独立出来，后续补内容时不会再挤在 Todo 详情页。'
  }
  return '评分已经落到静态快照里，下面可以直接看维度拆解和完整报告正文。'
})

const sectionLinks = computed(() => [
  { href: '#overview', label: '总览' },
  { href: '#score', label: '评分概览' },
  { href: '#score-report', label: 'Score Report' },
  { href: '#report', label: 'Report / Learnpath' },
  { href: '#snapshot', label: '关联论文快照' },
])

const scoreBarWidth = (value) => {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return '0%'
  return `${Math.min(Math.max(numeric, 0), 10) * 10}%`
}

const goBackToTodo = () => navigateTo(todoDetailLink.value)

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
    const payload = await fetchJson(`papers/${linkedRouteId}.json`)
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
    card.value = matched
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
