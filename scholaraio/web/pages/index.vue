<template>
  <div class="aio-content">
    <section class="aio-hero">
      <div>
        <h1 class="aio-title">Todo 阅读卡片</h1>
      </div>
      <div class="aio-hero-stats">
        <div class="aio-stat">
          <div class="aio-stat-value">{{ filteredTodoCards.length }}</div>
          <div class="aio-stat-label">当前显示</div>
        </div>
        <div class="aio-stat">
          <div class="aio-stat-value">{{ todoCards.length }}</div>
          <div class="aio-stat-label">全部 Todo</div>
        </div>
        <div class="aio-stat">
          <div class="aio-stat-value">{{ unreadCount }}</div>
          <div class="aio-stat-label">未读</div>
        </div>
      </div>
    </section>

    <section class="aio-panel aio-filter-panel">
      <div class="aio-field-grid primary">
        <label class="aio-field">
          <span>搜索</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索标题、作者、术语、结论..."
            class="aio-input"
          >
        </label>

        <label class="aio-field">
          <span>排序</span>
          <select v-model="sortBy" class="aio-select">
            <option value="">Todo 顺序</option>
            <option value="year">按年份</option>
            <option value="title">按标题</option>
          </select>
        </label>
      </div>

      <div class="aio-field-grid secondary">
        <label class="aio-field">
          <span>作者</span>
          <input
            v-model="authorFilter"
            type="text"
            placeholder="例如 Hutter"
            class="aio-input"
          >
        </label>

        <label class="aio-field">
          <span>起始年份</span>
          <input
            v-model.number="yearFrom"
            type="number"
            min="1900"
            max="2100"
            placeholder="例如 2020"
            class="aio-input"
          >
        </label>

        <label class="aio-field">
          <span>结束年份</span>
          <input
            v-model.number="yearTo"
            type="number"
            min="1900"
            max="2100"
            placeholder="例如 2026"
            class="aio-input"
          >
        </label>

        <label class="aio-field">
          <span>DOI</span>
          <select v-model="doiFilter" class="aio-select">
            <option value="">全部</option>
            <option value="has">仅有 DOI</option>
            <option value="missing">仅无 DOI</option>
          </select>
        </label>
      </div>

      <div class="aio-filter-actions">
        <button class="aio-button-secondary" @click="clearFilters">清空筛选</button>
        <button class="aio-button-secondary" @click="loadTodoCards">刷新数据</button>
        <span class="aio-muted">匹配 {{ filteredTodoCards.length }} / {{ todoCards.length }}</span>
      </div>

      <div class="aio-writeback-panel">
        <div>
          <p class="aio-kicker">已读状态同步</p>
          <p class="aio-muted">{{ writebackHint }}</p>
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

      <p v-if="readStatusError" class="aio-message error">
        {{ readStatusError }}
      </p>
      <p v-if="readStatusMessage" class="aio-message success">
        {{ readStatusMessage }}
      </p>

      <div v-if="showGithubTokenInput" class="aio-token-box">
        <label class="aio-field" for="todo-index-github-token">
          <span>GitHub token</span>
          <input
            id="todo-index-github-token"
            v-model="githubTokenDraft"
            type="password"
            autocomplete="off"
            class="aio-input"
            placeholder="repo/workflow token"
          >
        </label>
        <div class="aio-token-actions">
          <button class="aio-button" @click="saveGithubToken">保存令牌</button>
          <button class="aio-button-secondary" @click="showGithubTokenInput = false">取消</button>
        </div>
        <p class="aio-muted aio-token-note">
          令牌只保存在当前浏览器。换浏览器、无痕窗口或清理浏览器数据后，需要重新填写。
        </p>
      </div>
    </section>

    <div v-if="loading" class="aio-state">
      <div class="aio-spinner"></div>
      <p>正在加载阅读卡片...</p>
    </div>

    <div v-else-if="errorMessage" class="aio-state error">
      {{ errorMessage }}
    </div>

    <template v-else>
      <section class="aio-section-header">
        <h2>阅读队列</h2>
        <span class="aio-muted">第 {{ currentPage }} / {{ totalPages }} 页</span>
      </section>

      <div v-if="filteredTodoCards.length" class="aio-card-grid">
        <article
          v-for="card in pagedTodoCards"
          :key="card.route_id"
          class="aio-card aio-todo-card"
        >
          <NuxtLink class="aio-card-main" :to="todoDetailLink(card.route_id)">
            <div class="aio-card-top">
              <div class="aio-pill-row">
                <span class="aio-pill is-ready">Todo</span>
                <span class="aio-pill" :class="statusClass(card.read_status)">
                  {{ card.read_status === 'read' ? '已读' : '未读' }}
                </span>
                <span
                  v-if="pendingRouteId === card.route_id"
                  class="aio-pill is-syncing"
                >
                  等待部署
                </span>
              </div>
              <span class="aio-pill">{{ card.year || 'n.d.' }}</span>
            </div>

            <h2 class="aio-card-title" v-html="highlightText(card.title)"></h2>
            <p class="aio-card-authors" v-html="highlightText(card.authors?.join(', ') || '作者信息缺失')"></p>
            <p class="aio-card-meta">
              <span v-if="card.journal">{{ card.journal }}</span>
              <span v-else>期刊信息缺失</span>
              <span v-if="card.doi"> · DOI: {{ card.doi }}</span>
            </p>

            <div class="aio-card-summary">
              <p v-html="highlightText(card.one_line_summary)"></p>
              <div v-if="previewText(card)" class="aio-card-preview">
                {{ previewText(card) }}
              </div>
            </div>
          </NuxtLink>

          <div class="aio-card-footer">
            <NuxtLink class="aio-card-open" :to="todoDetailLink(card.route_id)">查看总结</NuxtLink>
            <button
              type="button"
              class="aio-read-toggle"
              :class="statusClass(card.read_status)"
              :disabled="savingRouteId === card.route_id"
              @click.stop.prevent="toggleCardReadStatus(card)"
            >
              <span v-if="savingRouteId === card.route_id">提交中...</span>
              <span v-else>{{ card.read_status === 'read' ? '标记未读' : '标记已读' }}</span>
            </button>
          </div>
        </article>
      </div>

      <div v-if="filteredTodoCards.length" class="aio-pagination">
        <span class="aio-muted">第 {{ currentPage }} / {{ totalPages }} 页 · 每页 {{ pageSize }} 条</span>
        <div class="aio-pagination-controls">
          <button
            class="aio-button-secondary"
            :disabled="currentPage <= 1"
            @click="currentPage = Math.max(1, currentPage - 1)"
          >上一页</button>
          <button
            class="aio-button-secondary"
            :disabled="currentPage >= totalPages"
            @click="currentPage = Math.min(totalPages, currentPage + 1)"
          >下一页</button>
        </div>
      </div>

      <div v-else class="aio-state">
        当前筛选条件下没有匹配到 Todo 卡片。
      </div>
    </template>
  </div>
</template>

<script setup>
const { fetchJson, applyReadStatusOverride, setReadStatusOverride } = useStaticSiteData()
const runtimeConfig = useRuntimeConfig()

const searchQuery = ref('')
const authorFilter = ref('')
const yearFrom = ref(null)
const yearTo = ref(null)
const doiFilter = ref('')
const sortBy = ref('')
const todoCards = ref([])
const loading = ref(true)
const errorMessage = ref('')
const readStatusError = ref('')
const readStatusMessage = ref('')
const currentPage = ref(1)
const savingRouteId = ref('')
const pendingRouteId = ref('')
const githubToken = ref('')
const githubTokenDraft = ref('')
const showGithubTokenInput = ref(false)
const browserGithubOwner = ref('')
const browserGithubRepo = ref('')
const pageSize = 24

const appBaseUrl = computed(() => {
  const value = String(runtimeConfig.app.baseURL || '/')
  return value.endsWith('/') ? value : value + '/'
})
const normalizedQuery = computed(() => searchQuery.value.trim().toLowerCase())
const normalizedAuthorFilter = computed(() => authorFilter.value.trim().toLowerCase())
const unreadCount = computed(() => todoCards.value.filter((card) => (card.read_status || 'unread') !== 'read').length)
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
const writebackHint = computed(() => {
  if (!githubWritebackReady.value) return '当前静态页缺少仓库或 workflow 配置，只能浏览快照。'
  if (savingRouteId.value) return '正在触发 workflow_dispatch；当前浏览器会先显示新状态。'
  if (pendingRouteId.value) return '已提交写回，等待 GitHub Pages 重新部署后静态快照会同步。'
  if (!githubToken.value) return '首次标记已读前需要配置一次 GitHub token。'
  return '令牌已在当前浏览器保存；点击卡片按钮即可触发 GitHub Actions 写回。'
})

const matchesSearch = (values) => {
  const query = normalizedQuery.value
  if (!query) return true
  return values.some((value) => String(value || '').toLowerCase().includes(query))
}

const filteredTodoCards = computed(() => {
  let result = todoCards.value.filter((card) => matchesSearch([
    card.title,
    card.journal,
    card.doi,
    ...(card.authors || []),
    card.one_line_summary,
    card.search_text,
  ]))

  if (normalizedAuthorFilter.value) {
    result = result.filter((card) => {
      const authorText = (card.authors || []).join(' ').toLowerCase()
      return authorText.includes(normalizedAuthorFilter.value)
    })
  }

  if (yearFrom.value !== null && yearFrom.value !== '' && Number.isFinite(Number(yearFrom.value))) {
    const minYear = Number(yearFrom.value)
    result = result.filter((card) => Number(card.year || 0) >= minYear)
  }

  if (yearTo.value !== null && yearTo.value !== '' && Number.isFinite(Number(yearTo.value))) {
    const maxYear = Number(yearTo.value)
    result = result.filter((card) => Number(card.year || 0) <= maxYear)
  }

  if (doiFilter.value === 'has') {
    result = result.filter((card) => String(card.doi || '').trim() !== '')
  } else if (doiFilter.value === 'missing') {
    result = result.filter((card) => String(card.doi || '').trim() === '')
  }

  if (sortBy.value === 'year') {
    result = [...result].sort((a, b) => (b.year || 0) - (a.year || 0))
  } else if (sortBy.value === 'title') {
    result = [...result].sort((a, b) => String(a.title || '').localeCompare(String(b.title || ''), 'zh-Hans-CN'))
  } else {
    result = [...result].sort((a, b) => (a.collection_index || 0) - (b.collection_index || 0))
  }

  return result
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredTodoCards.value.length / pageSize)))

const pagedTodoCards = computed(() => {
  const page = Math.min(Math.max(1, currentPage.value), totalPages.value)
  const start = (page - 1) * pageSize
  return filteredTodoCards.value.slice(start, start + pageSize)
})

watch(filteredTodoCards, () => {
  currentPage.value = 1
})

const statusClass = (status) => {
  const classes = {
    unread: 'is-unread',
    read: 'is-read',
  }
  return classes[status] || classes.unread
}

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

const escapeHtml = (value) => String(value || '')
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#39;')

const highlightText = (value) => {
  const raw = String(value || '')
  const safe = escapeHtml(raw)
  const query = normalizedQuery.value
  if (!query) return safe
  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp('(' + escapedQuery + ')', 'ig')
  return safe.replace(regex, '<mark class="aio-mark">$1</mark>')
}

const previewText = (card) => {
  const raw = String(card.core_innovation || '').trim()
  if (!raw) return ''
  return raw.length > 180 ? raw.slice(0, 180) + '...' : raw
}

const todoDetailLink = (routeId) => routeId ? '/todo/' + routeId : '#'

const updateCardStatus = (routeId, status) => {
  todoCards.value = todoCards.value.map((item) => {
    if (item.route_id !== routeId) return item
    return {
      ...item,
      read_status: status,
    }
  })
}

const toggleCardReadStatus = async (card) => {
  if (!card || savingRouteId.value) return
  if (!githubWritebackReady.value) {
    readStatusError.value = '当前页面没有 GitHub 写回配置。'
    return
  }

  const previousStatus = card.read_status || 'unread'
  const nextStatus = previousStatus === 'read' ? 'unread' : 'read'
  const token = githubToken.value.trim()

  if (!token) {
    showGithubTokenInput.value = true
    readStatusError.value = '首次写回需要 GitHub token。'
    return
  }

  savingRouteId.value = card.route_id
  pendingRouteId.value = ''
  readStatusError.value = ''
  readStatusMessage.value = ''
  updateCardStatus(card.route_id, nextStatus)
  setReadStatusOverride([card.route_id, card], nextStatus)

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
          paper_ref: card.route_id,
          status: nextStatus,
          title: card.title || '',
        },
      }),
    })

    if (!response.ok) {
      throw new Error(await githubApiErrorText(response))
    }

    pendingRouteId.value = card.route_id
    readStatusMessage.value = '已提交 GitHub Actions 写回；当前浏览器已先显示新状态，部署完成后静态快照会同步。'
  } catch (error) {
    updateCardStatus(card.route_id, previousStatus)
    setReadStatusOverride([card.route_id, card], previousStatus)
    readStatusError.value = errorText(error, 'Failed to update read status.')
  } finally {
    savingRouteId.value = ''
  }
}

const loadTodoCards = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const todoData = await fetchJson('todo-cards.json')
    const cards = Array.isArray(todoData?.cards) ? todoData.cards : []
    todoCards.value = cards.map((card) => applyReadStatusOverride({
      ...card,
      read_status: card.read_status || 'unread',
    }))
  } catch (error) {
    console.error('Failed to load todo cards:', error)
    errorMessage.value = 'Failed to load Todo snapshot.'
  } finally {
    loading.value = false
  }
}

const clearFilters = () => {
  searchQuery.value = ''
  authorFilter.value = ''
  yearFrom.value = null
  yearTo.value = null
  doiFilter.value = ''
  sortBy.value = ''
}

onMounted(() => {
  inferGithubRepository()
  loadGithubToken()
  loadTodoCards()
})
</script>
