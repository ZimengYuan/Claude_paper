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

      <section class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Compass Snapshot</p>
            <h2 class="mt-2 text-lg font-semibold text-slate-900">6. Paper Compass</h2>
            <p class="mt-2 text-sm text-slate-500">
              评分报告与学习路径已迁移到独立页面，Todo 详情页这里只保留摘要入口，避免长下拉。
            </p>
          </div>
          <a
            class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
            :href="compassDetailLink"
          >
            打开完整 Compass
          </a>
        </div>

        <div class="mt-6 grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
          <div class="rounded-[28px] border border-slate-900 bg-[radial-gradient(circle_at_top_left,_rgba(96,165,250,0.28),_transparent_42%),linear-gradient(135deg,_#020617,_#111827_52%,_#1e293b)] p-6 text-white shadow-sm">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-300">Quick Verdict</p>
                <p class="mt-4 text-4xl font-semibold leading-none" :class="ratingClass(paper?.rating?.overall_score)">
                  {{ overallRatingText }}
                </p>
              </div>
              <span class="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-slate-100">
                {{ paper?.rating ? '结构化评分已就绪' : '等待评分快照' }}
              </span>
            </div>
            <p class="mt-5 text-sm leading-8 text-slate-100">
              {{ ratingNote || '完整的评分理由、学习路径和原始报告已经拆到独立 Compass 页面。' }}
            </p>
            <div class="mt-5 flex flex-wrap gap-2">
              <span
                v-for="entry in compassMaterialEntries"
                :key="entry.label"
                class="rounded-full border px-2.5 py-1 text-xs"
                :class="materialClass(entry.ready)"
              >
                {{ entry.label }}
              </span>
            </div>
          </div>

          <div class="space-y-4">
            <div class="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">关联论文</p>
              <dl v-if="linkedPaperEntries.length" class="mt-4 space-y-3 text-sm">
                <div v-for="entry in linkedPaperEntries" :key="entry.label">
                  <dt class="text-slate-500">{{ entry.label }}</dt>
                  <dd class="mt-1 break-all text-slate-900">{{ entry.value }}</dd>
                </div>
              </dl>
              <p v-else class="mt-4 text-sm text-slate-500">当前还没读取到关联论文的静态详情。</p>
            </div>

            <div class="rounded-2xl border border-slate-200 bg-white p-5">
              <div class="flex items-center justify-between">
                <p class="text-sm font-semibold text-slate-900">评分维度</p>
                <span class="text-xs text-slate-400">{{ ratingEntries.length ? `${ratingEntries.length} 项` : '暂无' }}</span>
              </div>
              <div v-if="ratingEntries.length" class="mt-4 grid gap-3 sm:grid-cols-2">
                <div
                  v-for="entry in ratingEntries"
                  :key="entry.label"
                  class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
                >
                  <p class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ entry.label }}</p>
                  <p class="mt-2 text-lg font-semibold text-slate-900">{{ entry.value }}/10</p>
                </div>
              </div>
              <p v-else class="mt-4 text-sm text-slate-500">当前静态快照里还没有可展示的结构化评分。</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
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
const localReadStatuses = ref({})

const paperRouteId = computed(() => String(card.value?.paper_route_id || '').trim())
const appBaseUrl = computed(() => {
  const value = String(runtimeConfig.app.baseURL || '/')
  return value.endsWith('/') ? value : `${value}/`
})
const compassDetailLink = computed(() => `${appBaseUrl.value}compass/${routeId.value}`)

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
  if (score == null) return 'text-slate-300'
  if (score >= 8) return 'text-emerald-300'
  if (score >= 6) return 'text-amber-300'
  return 'text-rose-300'
}

const paperLink = (todoCard) => {
  const linkedPaperRouteId = String(todoCard?.paper_route_id || '').trim()
  if (linkedPaperRouteId) return `${appBaseUrl.value}paper/${linkedPaperRouteId}`
  const doi = String(todoCard?.doi || '').trim()
  if (doi) return `https://doi.org/${doi}`
  return '#'
}

const goBack = () => navigateTo(appBaseUrl.value)

const keepValue = (value) => value !== null && value !== undefined && value !== ''

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
    { label: '年份', value: paper.value.year },
    { label: '期刊 / Venue', value: paper.value.journal },
    { label: 'DOI', value: paper.value.doi },
    { label: 'Route ID', value: paperRouteId.value },
  ].filter((entry) => keepValue(entry.value))
})

const compassMaterialEntries = computed(() => [
  { label: 'Score Report', ready: Boolean(scoreReport.value) },
  { label: 'Report', ready: Boolean(readableReport.value) },
  { label: 'Rating', ready: Boolean(paper.value?.rating) },
])

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
