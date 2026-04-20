<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <button class="text-sm font-medium text-blue-600 transition hover:text-blue-800" @click="goBack">
        ← 返回 Todo 列表
      </button>

      <div class="flex flex-wrap gap-3">
        <button
          v-if="card && githubWritebackReady"
          class="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="savingReadStatus"
          @click="toggleReadStatus"
        >
          {{ savingReadStatus ? '保存中...' : ((card.read_status || 'unread') === 'read' ? '标记未读' : '标记已读') }}
        </button>
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
              <span class="rounded-full px-3 py-1 text-xs font-medium" :class="statusClass(card.read_status || 'unread')">
                {{ readStatusLabel(card.read_status) }}
              </span>
            </div>
            <h1 class="mt-4 text-3xl font-semibold leading-tight text-slate-900">{{ card.title }}</h1>
            <p class="mt-3 text-sm text-slate-600">{{ card.authors?.join(', ') || '作者信息缺失' }}</p>
            <p class="mt-1 text-xs text-slate-500">
              {{ card.year || '年份未知' }}<span v-if="card.journal"> · {{ card.journal }}</span>
              <span v-if="card.doi"> · DOI: {{ card.doi }}</span>
            </p>
            <p v-if="readStatusError" class="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {{ readStatusError }}
            </p>
            <p v-if="readStatusMessage" class="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
              {{ readStatusMessage }}
            </p>
            <div v-if="showGithubTokenInput" class="mt-3 rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-sm">
              <label class="block text-xs font-medium text-slate-500" for="todo-github-token">GitHub token</label>
              <div class="mt-2 flex flex-col gap-2 sm:flex-row">
                <input
                  id="todo-github-token"
                  v-model="githubTokenDraft"
                  type="password"
                  autocomplete="off"
                  class="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="repo/workflow token"
                >
                <button
                  class="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-700"
                  @click="saveGithubToken"
                >
                  保存
                </button>
                <button
                  v-if="githubToken"
                  class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                  @click="clearGithubToken"
                >
                  清除
                </button>
              </div>
              <p class="mt-2 text-xs text-slate-500">令牌只保存在当前浏览器，用来触发仓库 workflow_dispatch。</p>
            </div>
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
            :key="card.route_id + '-' + index"
            class="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          >
            <p class="text-sm font-semibold text-slate-900">{{ item.title || ('创新点 ' + (index + 1)) }}</p>
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
              评分报告与学习路径已经单独拆到 Compass 页面。Todo 详情这里只保留一个紧凑入口，避免继续往下堆内容。
            </p>
          </div>
          <a
            class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
            :href="compassDetailLink"
          >
            打开完整 Compass
          </a>
        </div>

        <div class="mt-6 grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)]">
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
              {{ ratingNote || '完整的评分依据与学习路径已经拆到独立 Compass 页面。' }}
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

          <div class="rounded-2xl border border-slate-200 bg-white p-5">
            <div class="flex items-center justify-between">
              <p class="text-sm font-semibold text-slate-900">评分维度</p>
              <span class="text-xs text-slate-400">{{ ratingEntries.length ? (ratingEntries.length + ' 项') : '暂无' }}</span>
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
      </section>
    </div>
  </div>
</template>

<script setup>
const { fetchJson, applyReadStatusOverride, setReadStatusOverride } = useStaticSiteData()
const runtimeConfig = useRuntimeConfig()
const route = useRoute()
const routeId = computed(() => String(route.params.id || '').trim())

const loading = ref(true)
const errorMessage = ref('')
const readStatusError = ref('')
const readStatusMessage = ref('')
const savingReadStatus = ref(false)
const card = ref(null)
const paper = ref(null)
const scoreReport = ref('')
const readableReport = ref('')
const githubToken = ref('')
const githubTokenDraft = ref('')
const showGithubTokenInput = ref(false)
const browserGithubOwner = ref('')
const browserGithubRepo = ref('')

const appBaseUrl = computed(() => {
  const value = String(runtimeConfig.app.baseURL || '/')
  return value.endsWith('/') ? value : value + '/'
})
const compassDetailLink = computed(() => appBaseUrl.value + 'compass/' + routeId.value)
const githubOwner = computed(() => String(runtimeConfig.public?.githubOwner || browserGithubOwner.value || '').trim())
const githubRepo = computed(() => String(runtimeConfig.public?.githubRepo || browserGithubRepo.value || '').trim())
const githubRef = computed(() => String(runtimeConfig.public?.githubRef || 'main').trim())
const githubReadStatusWorkflow = computed(() => String(runtimeConfig.public?.githubReadStatusWorkflow || 'read-status.yml').trim())
const githubWritebackReady = computed(() => Boolean(
  githubOwner.value
  && githubRepo.value
  && githubRef.value
  && githubReadStatusWorkflow.value
))

useHead(() => ({
  title: card.value ? card.value.title + ' | Todo Reading Card' : 'Todo Reading Card',
}))

const statusClass = (status) => {
  const classes = {
    unread: 'bg-slate-100 text-slate-600',
    read: 'bg-emerald-100 text-emerald-700',
  }
  return classes[status] || classes.unread
}

const readStatusLabel = (status) => status === 'read' ? '已读' : '未读'

const errorText = (error, fallback) => {
  return error?.data?.message
    || error?.data?.statusMessage
    || error?.statusMessage
    || error?.message
    || fallback
}

const githubApiErrorText = async (response) => {
  try {
    const payload = await response.json()
    if (payload?.message) return payload.message
  } catch {}
  return `GitHub API returned ${response.status}`
}

const inferGithubRepository = () => {
  if (!import.meta.client) return

  const host = window.location.hostname
  const ownerMatch = host.match(/^(.+)\.github\.io$/)
  if (ownerMatch && !browserGithubOwner.value) {
    browserGithubOwner.value = ownerMatch[1]
  }

  const segments = window.location.pathname.split('/').filter(Boolean)
  if (segments.length && !browserGithubRepo.value) {
    browserGithubRepo.value = segments[0]
  }
}

const loadGithubToken = () => {
  if (!import.meta.client) return
  const saved = window.localStorage.getItem('scholaraio.githubToken') || ''
  githubToken.value = saved
  githubTokenDraft.value = saved
}

const saveGithubToken = () => {
  const token = githubTokenDraft.value.trim()
  if (!token) {
    readStatusError.value = '请输入可触发 Actions 的 GitHub token。'
    return
  }
  githubToken.value = token
  if (import.meta.client) {
    window.localStorage.setItem('scholaraio.githubToken', token)
  }
  showGithubTokenInput.value = false
  readStatusError.value = ''
}

const clearGithubToken = () => {
  githubToken.value = ''
  githubTokenDraft.value = ''
  if (import.meta.client) {
    window.localStorage.removeItem('scholaraio.githubToken')
  }
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
  if (linkedPaperRouteId) return appBaseUrl.value + 'paper/' + linkedPaperRouteId
  const doi = String(todoCard?.doi || '').trim()
  if (doi) return 'https://doi.org/' + doi
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
  return Number(score).toFixed(1) + '/10'
})

const compassMaterialEntries = computed(() => [
  { label: 'Score Report', ready: Boolean(scoreReport.value) },
  { label: 'Report', ready: Boolean(readableReport.value) },
  { label: 'Rating', ready: Boolean(paper.value?.rating) },
])

const applyPaperPayload = (payload) => {
  const hydrated = applyReadStatusOverride({
    route_id: card.value?.paper_route_id || routeId.value,
    ...payload,
  })
  paper.value = hydrated
  scoreReport.value = hydrated?.score_report || ''
  readableReport.value = hydrated?.readable_report || ''
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
  readStatusError.value = ''
  readStatusMessage.value = ''
  try {
    const todoData = await fetchJson('todo-cards.json')
    const cards = Array.isArray(todoData?.cards) ? todoData.cards : []
    const matched = cards.find((item) => item.route_id === routeId.value)
    if (!matched) {
      throw new Error('Todo reading card not found in snapshot.')
    }
    card.value = applyReadStatusOverride({
      ...matched,
      read_status: matched.read_status || 'unread',
    })
    await loadLinkedPaper(matched)
  } catch (error) {
    console.error('Failed to load todo detail:', error)
    errorMessage.value = 'Failed to load Todo detail.'
  } finally {
    loading.value = false
  }
}

const toggleReadStatus = async () => {
  if (!card.value || savingReadStatus.value) return
  if (!githubWritebackReady.value) {
    readStatusError.value = '当前页面没有 GitHub 写回配置。'
    return
  }

  const previousCardStatus = card.value.read_status || 'unread'
  const previousPaperStatus = paper.value?.read_status || previousCardStatus
  const previousPaperReadAt = paper.value?.read_at
  const nextStatus = previousCardStatus === 'read' ? 'unread' : 'read'
  const token = githubToken.value.trim()
  if (!token) {
    showGithubTokenInput.value = true
    readStatusError.value = '首次写回需要 GitHub token。'
    return
  }

  savingReadStatus.value = true
  readStatusError.value = ''
  readStatusMessage.value = ''
  card.value = {
    ...card.value,
    read_status: nextStatus,
  }
  if (paper.value) {
    paper.value = {
      ...paper.value,
      read_status: nextStatus,
    }
  }
  setReadStatusOverride([routeId.value, card.value, paper.value].filter(Boolean), nextStatus)

  try {
    const response = await fetch(`https://api.github.com/repos/${githubOwner.value}/${githubRepo.value}/actions/workflows/${githubReadStatusWorkflow.value}/dispatches`, {
      method: 'POST',
      headers: {
        Accept: 'application/vnd.github+json',
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
      body: JSON.stringify({
        ref: githubRef.value,
        inputs: {
          paper_ref: routeId.value,
          status: nextStatus,
          title: card.value.title || '',
        },
      }),
    })

    if (!response.ok) {
      throw new Error(await githubApiErrorText(response))
    }

    readStatusMessage.value = '已提交 GitHub Actions 写回；部署完成后静态快照会同步。'
  } catch (error) {
    card.value = {
      ...card.value,
      read_status: previousCardStatus,
    }
    if (paper.value) {
      paper.value = {
        ...paper.value,
        read_status: previousPaperStatus,
        read_at: previousPaperReadAt,
      }
    }
    setReadStatusOverride([routeId.value, card.value, paper.value].filter(Boolean), previousCardStatus)
    readStatusError.value = errorText(error, 'Failed to update read status.')
  } finally {
    savingReadStatus.value = false
  }
}

onMounted(() => {
  inferGithubRepository()
  loadGithubToken()
  loadCard()
})
</script>
