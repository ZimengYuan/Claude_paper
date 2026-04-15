<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <button class="text-sm font-medium text-blue-600 transition hover:text-blue-800" @click="goBack">
        ← 返回 Todo 列表
      </button>

      <div class="flex flex-wrap gap-3">
        <a
          v-if="card"
          class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
          :href="paperLink(card)"
          :target="paperLink(card).startsWith('http') ? '_blank' : null"
          :rel="paperLink(card).startsWith('http') ? 'noopener noreferrer' : null"
        >
          查看论文
        </a>
      </div>
    </div>

    <div v-if="loading" class="py-16 text-center">
      <div class="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
      <p class="mt-4 text-sm text-slate-500">Loading Todo detail...</p>
    </div>

    <div v-else-if="errorMessage" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorMessage }}
    </div>

    <div v-else-if="card" class="space-y-6">
      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <span class="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-blue-700">
                Todo Detail
              </span>
              <span class="rounded-full px-3 py-1 text-xs font-medium" :class="statusClass(resolvedReadStatus)">
                {{ resolvedReadStatus === 'read' ? '已读' : '未读' }}
              </span>
            </div>
            <h1 class="mt-4 text-3xl font-semibold leading-tight text-slate-900">{{ card.title }}</h1>
            <p class="mt-3 text-sm text-slate-600">{{ card.authors?.join(', ') || '作者信息缺失' }}</p>
            <p class="mt-1 text-xs text-slate-500">
              {{ card.year || '年份未知' }}<span v-if="card.journal"> · {{ card.journal }}</span>
              <span v-if="card.doi"> · DOI: {{ card.doi }}</span>
            </p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-500">
            生成模型：{{ card.generated_with_model || 'gpt-5.4-mini' }}
          </div>
        </div>
      </section>

      <section class="rounded-3xl border border-slate-900 bg-slate-950 p-6 text-white shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-300">一句话总结</p>
        <p class="mt-3 text-base leading-8 text-slate-100">{{ card.one_line_summary }}</p>
      </section>

      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="text-lg font-semibold text-slate-900">1. 核心创新点</h2>
        <p class="mt-4 text-sm leading-8 text-slate-700">{{ card.core_innovation }}</p>
      </section>

      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="text-lg font-semibold text-slate-900">2. 技术创新拆解</h2>
        <div class="mt-4 grid gap-4">
          <div
            v-for="(item, index) in card.technical_contributions"
            :key="`${card.route_id}-${index}`"
            class="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <p class="text-sm font-semibold text-slate-900">{{ item.title || `创新点 ${index + 1}` }}</p>
            <p class="mt-2 text-sm leading-7 text-slate-700">{{ item.body }}</p>
          </div>
        </div>
      </section>

      <section class="grid gap-6 xl:grid-cols-2">
        <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 class="text-lg font-semibold text-slate-900">3. 方法论突破</h2>
          <div class="mt-4 space-y-4 text-sm leading-7 text-slate-700">
            <p><span class="font-semibold text-slate-900">新颖性：</span>{{ card.methodological_breakthrough.novelty }}</p>
            <p><span class="font-semibold text-slate-900">关键技术：</span>{{ card.methodological_breakthrough.key_technique }}</p>
            <p><span class="font-semibold text-slate-900">理论支撑：</span>{{ card.methodological_breakthrough.theory }}</p>
          </div>
        </div>

        <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 class="text-lg font-semibold text-slate-900">4. 实验验证</h2>
          <div class="mt-4 space-y-4 text-sm leading-7 text-slate-700">
            <p><span class="font-semibold text-slate-900">主要 benchmark：</span>{{ card.key_results.benchmarks }}</p>
            <p><span class="font-semibold text-slate-900">性能提升：</span>{{ card.key_results.improvements }}</p>
            <p><span class="font-semibold text-slate-900">关键贡献组件：</span>{{ card.key_results.ablation }}</p>
          </div>
        </div>
      </section>

      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 class="text-lg font-semibold text-slate-900">5. 局限与启发</h2>
        <div class="mt-4 grid gap-4 md:grid-cols-3">
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">当前局限</p>
            <p class="mt-2 text-sm leading-7 text-slate-700">{{ card.limitations.current }}</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">未来方向</p>
            <p class="mt-2 text-sm leading-7 text-slate-700">{{ card.limitations.future }}</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p class="text-sm font-semibold text-slate-900">可迁移性</p>
            <p class="mt-2 text-sm leading-7 text-slate-700">{{ card.limitations.transferability }}</p>
          </div>
        </div>
      </section>

      <section class="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,0.9fr)]">
        <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 class="text-lg font-semibold text-slate-900">6. Paper Compass</h2>
              <p class="mt-2 text-sm text-slate-500">
                这里直接挂出该 Todo 对应论文的评分报告与可读报告，不用再跳去普通论文详情页。
              </p>
            </div>
            <a
              v-if="paperDetailLink"
              class="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
              :href="paperDetailLink"
            >
              打开论文详情页
            </a>
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <span class="rounded-full border px-2.5 py-1 text-xs" :class="materialClass(Boolean(scoreReport))">Score Report</span>
            <span class="rounded-full border px-2.5 py-1 text-xs" :class="materialClass(Boolean(readableReport))">Report</span>
            <span class="rounded-full border px-2.5 py-1 text-xs" :class="materialClass(Boolean(paper?.rating))">Rating</span>
          </div>

          <div class="mt-6 flex flex-wrap border-b border-slate-200">
            <button
              v-for="tab in compassTabs"
              :key="tab.key"
              class="relative px-5 py-3 text-sm font-medium transition-colors"
              :class="activeCompassTab === tab.key
                ? 'text-blue-600 after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-blue-600'
                : 'text-slate-500 hover:text-slate-700'"
              @click="activeCompassTab = tab.key"
            >
              {{ tab.label }}
              <span
                class="ml-2 inline-block h-1.5 w-1.5 rounded-full align-middle"
                :class="tab.ready ? 'bg-blue-500' : 'bg-slate-300'"
              ></span>
            </button>
          </div>

          <div class="mt-5">
            <div v-if="activeCompassTab === 'score-report'">
              <div v-if="scoreReport" class="markdown-body prose max-w-none" v-html="renderMarkdown(scoreReport)"></div>
              <p v-else class="text-sm text-slate-500">当前静态快照里还没有这篇论文的评分报告。</p>
            </div>

            <div v-if="activeCompassTab === 'report'">
              <div v-if="readableReport" class="markdown-body prose max-w-none" v-html="renderMarkdown(readableReport)"></div>
              <p v-else class="text-sm text-slate-500">当前静态快照里还没有这篇论文的可读报告。</p>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">7. 评分概览</h2>
            <div v-if="paper?.rating" class="mt-4 space-y-3">
              <div class="flex items-center justify-between">
                <span class="text-sm text-slate-500">总分</span>
                <span class="text-lg font-semibold" :class="ratingClass(paper.rating.overall_score)">
                  {{ overallRatingText }}
                </span>
              </div>
              <div
                v-for="entry in ratingEntries"
                :key="entry.label"
                class="flex items-center justify-between text-sm"
              >
                <span class="text-slate-500">{{ entry.label }}</span>
                <span class="font-medium text-slate-900">{{ entry.value }}/10</span>
              </div>
              <p v-if="ratingNote" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm italic text-slate-600">
                "{{ ratingNote }}"
              </p>
            </div>
            <p v-else class="mt-4 text-sm text-slate-500">当前静态快照里还没有可展示的结构化评分。</p>
          </section>

          <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 class="text-lg font-semibold text-slate-900">8. 关联论文快照</h2>
            <dl v-if="linkedPaperEntries.length" class="mt-4 space-y-3 text-sm">
              <div v-for="entry in linkedPaperEntries" :key="entry.label">
                <dt class="text-slate-500">{{ entry.label }}</dt>
                <dd class="mt-1 break-all text-slate-900">{{ entry.value }}</dd>
              </div>
            </dl>
            <p v-else class="mt-4 text-sm text-slate-500">当前还没读取到关联论文的静态详情。</p>
          </section>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'

const TODO_READ_STATUS_STORAGE_KEY = 'scholaraio:todo-read-statuses:v2'

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
const activeCompassTab = ref('score-report')
const localReadStatuses = ref({})

const paperRouteId = computed(() => String(card.value?.paper_route_id || '').trim())
const appBaseUrl = computed(() => {
  const value = String(runtimeConfig.app.baseURL || '/')
  return value.endsWith('/') ? value : `${value}/`
})
const paperDetailLink = computed(() => {
  if (!paperRouteId.value) return ''
  return `${appBaseUrl.value}paper/${paperRouteId.value}`
})
const compassTabs = computed(() => [
  { key: 'score-report', label: 'Score Report', ready: Boolean(scoreReport.value) },
  { key: 'report', label: 'Report', ready: Boolean(readableReport.value) },
])

const resolvedReadStatus = computed(() => {
  if (!card.value) return 'unread'
  const localStatus = localReadStatuses.value[card.value.route_id]
  if (localStatus === 'read' || localStatus === 'unread') {
    return localStatus
  }
  return card.value.read_status || 'unread'
})

useHead(() => ({
  title: card.value ? `${card.value.title} | Todo Reading Card` : 'Todo Reading Card',
}))

const restoreReadStatuses = () => {
  if (!import.meta.client) return

  try {
    const raw = window.localStorage.getItem(TODO_READ_STATUS_STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object') {
      localReadStatuses.value = parsed
    }
  } catch (error) {
    console.error('Failed to restore todo read statuses:', error)
  }
}


const statusClass = (status) => {
  const classes = {
    unread: 'bg-slate-100 text-slate-600',
    read: 'bg-emerald-100 text-emerald-700',
  }
  return classes[status] || classes.unread
}

const materialClass = (enabled) => {
  return enabled
    ? 'border-blue-200 bg-blue-50 text-blue-700'
    : 'border-slate-200 bg-slate-50 text-slate-400'
}

const ratingClass = (score) => {
  if (score == null) return 'text-slate-400'
  if (score >= 8) return 'text-emerald-600'
  if (score >= 6) return 'text-amber-600'
  return 'text-red-600'
}

const paperLink = (card) => {
  const linkedPaperRouteId = String(card?.paper_route_id || '').trim()
  if (linkedPaperRouteId) return `${appBaseUrl.value}paper/${linkedPaperRouteId}`
  const doi = String(card?.doi || '').trim()
  if (doi) return `https://doi.org/${doi}`
  return '#'
}

const goBack = () => navigateTo(appBaseUrl.value)

function keepValue(value) {
  return value !== null && value !== undefined && value !== ''
}

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

const linkedPaperEntries = computed(() => {
  if (paper.value == null) return []
  return [
    { label: '标题', value: paper.value.title },
    { label: '作者', value: Array.isArray(paper.value.authors) ? paper.value.authors.join(', ') : paper.value.authors },
    { label: '年份', value: paper.value.year },
    { label: '期刊 / Venue', value: paper.value.journal },
    { label: 'DOI', value: paper.value.doi },
    { label: '论文类型', value: paper.value.paper_type },
    { label: 'Route ID', value: paperRouteId.value },
  ].filter((entry) => keepValue(entry.value))
})

const applyPaperPayload = (payload) => {
  paper.value = payload
  scoreReport.value = payload?.score_report || ''
  readableReport.value = payload?.readable_report || ''
  activeCompassTab.value = (scoreReport.value || !readableReport.value) ? 'score-report' : 'report'
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

const renderMarkdown = (text) => {
  if (text == null || text === '') return ''

  try {
    return marked.parse(String(text))
  } catch (error) {
    console.error('Markdown rendering error:', error)
    return ''
  }
}

const loadCard = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const todoData = await fetchJson('todo-cards.json')
    const cards = Array.isArray(todoData?.cards) ? todoData.cards : []
    const matched = cards.find(item => item.route_id === routeId.value)
    if (!matched) {
      throw new Error('Todo reading card not found in snapshot.')
    }
    card.value = matched
    await loadLinkedPaper(matched)
  } catch (error) {
    console.error('Failed to load todo detail:', error)
    errorMessage.value = 'Failed to load Todo detail.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  restoreReadStatuses()
  await loadCard()
})
</script>
