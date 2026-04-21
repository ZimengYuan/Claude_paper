<template>
  <div class="aio-detail-page">
    <div class="aio-detail-topbar">
      <button class="aio-text-link" @click="goBack">
        ← 返回 Todo 列表
      </button>

      <button
        v-if="card"
        class="aio-button"
        :disabled="savingReadStatus || !githubWritebackReady"
        @click="toggleReadStatus"
      >
        {{ readStatusButtonLabel }}
      </button>
    </div>

    <div v-if="loading" class="aio-state">
      <div class="aio-spinner"></div>
      <p>Loading Todo detail...</p>
    </div>

    <div v-else-if="errorMessage" class="aio-state error">
      {{ errorMessage }}
    </div>

    <article v-else-if="card">
      <header class="aio-paper-header">
        <div class="aio-split-top">
          <div>
            <div class="aio-pill-row">
              <span class="aio-pill is-ready">Todo Detail</span>
              <span class="aio-pill" :class="statusClass(card.read_status || 'unread')">
                {{ readStatusLabel(card.read_status) }}
              </span>
              <span v-if="readStatusPending" class="aio-pill is-syncing">
                等待部署
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
            生成模型：{{ card.generated_with_model || 'gpt-5.4-mini' }}
          </div>
        </div>

        <p v-if="readStatusError" class="aio-message error">
          {{ readStatusError }}
        </p>
        <p v-if="readStatusMessage" class="aio-message success">
          {{ readStatusMessage }}
        </p>

        <div class="aio-writeback-panel aio-detail-writeback">
          <div>
            <p class="aio-kicker">已读状态同步</p>
            <p class="aio-muted">{{ readStatusHint }}</p>
          </div>
          <div class="aio-token-actions">
            <button class="aio-button-secondary" @click="showGithubTokenInput = !showGithubTokenInput">
              {{ githubToken ? '更换令牌' : '配置令牌' }}
            </button>
            <button
              v-if="githubToken"
              class="aio-button-secondary"
              @click="clearGithubToken"
            >
              清除令牌
            </button>
            <a
              v-if="githubActionsUrl"
              class="aio-button-secondary"
              :href="githubActionsUrl"
              target="_blank"
              rel="noopener noreferrer"
            >
              查看 Actions
            </a>
          </div>
        </div>

        <div v-if="showGithubTokenInput" class="aio-token-box">
          <label class="aio-field" for="todo-github-token">
            <span>GitHub token</span>
            <input
              id="todo-github-token"
              v-model="githubTokenDraft"
              type="password"
              autocomplete="off"
              class="aio-input"
              placeholder="repo/workflow token"
            >
          </label>
          <div class="aio-token-actions">
            <button class="aio-button" @click="saveGithubToken">保存</button>
            <button
              v-if="githubToken"
              class="aio-button-secondary"
              @click="clearGithubToken"
            >
              清除
            </button>
          </div>
          <p class="aio-muted aio-token-note">
            令牌只保存在当前浏览器，用来触发仓库 workflow_dispatch。换浏览器、无痕窗口或清理浏览器数据后，需要重新填写。
          </p>
        </div>
      </header>

      <section class="aio-callout aio-callout-accent">
        <p class="aio-kicker">One-line summary</p>
        <p>{{ card.one_line_summary }}</p>
      </section>

      <section class="aio-note-section">
        <p class="aio-kicker">01</p>
        <h2>核心创新点</h2>
        <p class="aio-note-body">{{ card.core_innovation }}</p>
      </section>

      <section class="aio-note-section">
        <p class="aio-kicker">02</p>
        <h2>技术创新拆解</h2>
        <div class="aio-two-col">
          <div
            v-for="(item, index) in card.technical_contributions"
            :key="card.route_id + '-' + index"
            class="aio-cell"
          >
            <h3>{{ item.title || ('创新点 ' + (index + 1)) }}</h3>
            <p>{{ item.body }}</p>
          </div>
        </div>
      </section>

      <section class="aio-note-section">
        <p class="aio-kicker">03</p>
        <h2>方法论突破</h2>
        <div class="aio-note-body">
          <div class="aio-key-row">
            <strong>新颖性</strong>
            <span>{{ card.methodological_breakthrough?.novelty }}</span>
          </div>
          <div class="aio-key-row">
            <strong>关键技术</strong>
            <span>{{ card.methodological_breakthrough?.key_technique }}</span>
          </div>
          <div class="aio-key-row">
            <strong>理论支撑</strong>
            <span>{{ card.methodological_breakthrough?.theory }}</span>
          </div>
        </div>
      </section>

      <section class="aio-note-section">
        <p class="aio-kicker">04</p>
        <h2>实验验证</h2>
        <div class="aio-note-body">
          <div class="aio-key-row">
            <strong>Benchmark</strong>
            <span>{{ card.key_results?.benchmarks }}</span>
          </div>
          <div class="aio-key-row">
            <strong>性能提升</strong>
            <span>{{ card.key_results?.improvements }}</span>
          </div>
          <div class="aio-key-row">
            <strong>消融组件</strong>
            <span>{{ card.key_results?.ablation }}</span>
          </div>
        </div>
      </section>

      <section class="aio-note-section">
        <p class="aio-kicker">05</p>
        <h2>局限与启发</h2>
        <div class="aio-three-col">
          <div class="aio-cell">
            <h3>当前局限</h3>
            <p>{{ card.limitations?.current }}</p>
          </div>
          <div class="aio-cell">
            <h3>未来方向</h3>
            <p>{{ card.limitations?.future }}</p>
          </div>
          <div class="aio-cell">
            <h3>可迁移性</h3>
            <p>{{ card.limitations?.transferability }}</p>
          </div>
        </div>
      </section>

      <section class="aio-note-section">
        <div class="aio-split-top">
          <div>
            <p class="aio-kicker">06</p>
            <h2>Paper Compass</h2>
          </div>
          <NuxtLink class="aio-button" :to="compassDetailLink">打开完整 Compass</NuxtLink>
        </div>

        <div class="aio-compass-card" :class="{ 'is-single': !todoMetricEntries.length }">
          <div class="aio-verdict">
            <div class="aio-split-top">
              <p class="aio-kicker">Quick Verdict</p>
              <span class="aio-pill" :class="paper?.rating ? 'is-ready' : 'is-muted'">
                {{ paper?.rating ? '评分已就绪' : '等待评分' }}
              </span>
            </div>
            <p class="aio-score" :class="ratingClass(paper?.rating?.overall_score)">
              {{ overallRatingText }}
            </p>
            <p class="aio-note-body">
              {{ ratingNote || '完整的评分依据与学习路径已经拆到独立 Compass 页面。' }}
            </p>
            <div class="aio-pill-row">
              <span
                v-for="entry in compassMaterialEntries"
                :key="entry.label"
                class="aio-pill"
                :class="materialClass(entry.ready)"
              >
                {{ entry.label }}
              </span>
            </div>
          </div>

          <div v-if="todoMetricEntries.length" class="aio-metric-panel">
            <div
              v-for="entry in todoMetricEntries"
              :key="entry.label"
              class="aio-metric"
              :class="{ primary: entry.primary }"
            >
              <span>{{ entry.label }}</span>
              <strong>{{ entry.value }}</strong>
            </div>
          </div>
        </div>
      </section>
    </article>
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
const readStatusPending = ref(false)
const card = ref(null)
const paper = ref(null)
const scoreReport = ref('')
const readableReport = ref('')
const githubToken = ref('')
const githubTokenDraft = ref('')
const showGithubTokenInput = ref(false)
const browserGithubOwner = ref('')
const browserGithubRepo = ref('')

const compassDetailLink = computed(() => '/compass/' + routeId.value)
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
const githubActionsUrl = computed(() => {
  if (!githubOwner.value || !githubRepo.value) return ''
  return `https://github.com/${githubOwner.value}/${githubRepo.value}/actions/workflows/${githubReadStatusWorkflow.value}`
})
const readStatusButtonLabel = computed(() => {
  if (!githubWritebackReady.value) return '写回未配置'
  if (savingReadStatus.value) return '提交中...'
  return (card.value?.read_status || 'unread') === 'read' ? '标记未读' : '标记已读'
})
const readStatusHint = computed(() => {
  if (!githubWritebackReady.value) return '当前静态页缺少仓库或 workflow 配置，只能浏览快照。'
  if (savingReadStatus.value) return '正在触发 workflow_dispatch；当前浏览器会先显示新状态。'
  if (readStatusPending.value) return '已提交写回，等待 GitHub Pages 重新部署后静态快照会同步。'
  if (!githubToken.value) return '首次标记已读前需要配置一次 GitHub token。'
  return '令牌已在当前浏览器保存；点击按钮即可触发 GitHub Actions 写回。'
})

useHead(() => ({
  title: card.value ? card.value.title + ' | Todo Reading Card' : 'Todo Reading Card',
}))

const statusClass = (status) => {
  const classes = {
    unread: 'is-unread',
    read: 'is-read',
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
  if (response.status === 401) return 'GitHub token 无效或已过期，请重新保存 token。'
  if (response.status === 403) return 'GitHub token 权限不足；需要能触发 Actions workflow_dispatch。'
  if (response.status === 404) return '找不到仓库或 read-status workflow，请检查部署配置。'

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
  readStatusMessage.value = '令牌已保存在当前浏览器。'
}

const clearGithubToken = () => {
  githubToken.value = ''
  githubTokenDraft.value = ''
  if (import.meta.client) {
    window.localStorage.removeItem('scholaraio.githubToken')
  }
  readStatusMessage.value = '已清除当前浏览器里的 GitHub token。'
}

const materialClass = (enabled) => {
  return enabled
    ? 'is-ready'
    : 'is-muted'
}

const ratingClass = (score) => {
  if (score == null) return 'score-empty'
  if (score >= 8) return 'score-high'
  if (score >= 6) return 'score-mid'
  return 'score-low'
}

const goBack = () => navigateTo('/')

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

const todoMetricEntries = computed(() => {
  const entries = []
  const score = paper.value?.rating?.overall_score
  if (score != null) {
    entries.push({ label: 'Overall Score', value: Number(score).toFixed(1) + '/10', primary: true })
  }
  for (const entry of ratingEntries.value) {
    entries.push({ label: entry.label, value: entry.value + '/10' })
  }
  return entries
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
  readStatusPending.value = false
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
  readStatusPending.value = false
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

    readStatusPending.value = true
    readStatusMessage.value = '已提交 GitHub Actions 写回；当前浏览器已先显示新状态，部署完成后静态快照会同步。'
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
    readStatusPending.value = false
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
