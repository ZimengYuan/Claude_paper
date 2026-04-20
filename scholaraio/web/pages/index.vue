<template>
  <div class="aio-content">
    <section class="aio-hero">
      <div>
        <p class="aio-kicker">// Todo Snapshot · ScholarAIO</p>
        <h1 class="aio-title">Todo Reading Cards</h1>
        <p class="aio-subtitle">
          这里汇总 Zotero Todo collection 的阅读卡片，按静态快照展示，已读状态可以直接从详情页写回仓库。
        </p>
      </div>
      <div class="aio-hero-stats">
        <div class="aio-stat">
          <div class="aio-stat-value">{{ filteredTodoCards.length }}</div>
          <div class="aio-stat-label">visible cards</div>
        </div>
        <div class="aio-stat">
          <div class="aio-stat-value">{{ todoCards.length }}</div>
          <div class="aio-stat-label">total todo</div>
        </div>
        <div class="aio-stat">
          <div class="aio-stat-value">{{ unreadCount }}</div>
          <div class="aio-stat-label">unread</div>
        </div>
      </div>
    </section>

    <section class="aio-panel aio-filter-panel">
      <div class="aio-field-grid primary">
        <label class="aio-field">
          <span>Search</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索标题、作者、术语、结论..."
            class="aio-input"
          >
        </label>

        <label class="aio-field">
          <span>Sort</span>
          <select v-model="sortBy" class="aio-select">
            <option value="">Todo 顺序</option>
            <option value="year">按年份</option>
            <option value="title">按标题</option>
          </select>
        </label>
      </div>

      <div class="aio-field-grid secondary">
        <label class="aio-field">
          <span>Author</span>
          <input
            v-model="authorFilter"
            type="text"
            placeholder="例如 Hutter"
            class="aio-input"
          >
        </label>

        <label class="aio-field">
          <span>Year From</span>
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
          <span>Year To</span>
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
        <span class="aio-muted">matched {{ filteredTodoCards.length }} / {{ todoCards.length }}</span>
      </div>
    </section>

    <div v-if="loading" class="aio-state">
      <div class="aio-spinner"></div>
      <p>Loading Todo snapshot...</p>
    </div>

    <div v-else-if="errorMessage" class="aio-state error">
      {{ errorMessage }}
    </div>

    <template v-else>
      <section class="aio-section-header">
        <h2>// Reading Queue · Todo</h2>
        <span class="aio-muted">page {{ currentPage }} / {{ totalPages }}</span>
      </section>

      <div v-if="filteredTodoCards.length" class="aio-card-grid">
        <NuxtLink
          v-for="card in pagedTodoCards"
          :key="card.route_id"
          class="aio-card aio-todo-card"
          :to="todoDetailLink(card.route_id)"
        >
          <div class="aio-card-top">
            <div class="aio-pill-row">
              <span class="aio-pill is-ready">Todo</span>
              <span class="aio-pill" :class="statusClass(card.read_status)">
                {{ card.read_status === 'read' ? '已读' : '未读' }}
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

          <div class="aio-card-action">查看总结 →</div>
        </NuxtLink>
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
const { fetchJson, applyReadStatusOverride } = useStaticSiteData()
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
const currentPage = ref(1)
const pageSize = 24

const appBaseUrl = computed(() => {
  const value = String(runtimeConfig.app.baseURL || '/')
  return value.endsWith('/') ? value : value + '/'
})
const normalizedQuery = computed(() => searchQuery.value.trim().toLowerCase())
const normalizedAuthorFilter = computed(() => authorFilter.value.trim().toLowerCase())
const unreadCount = computed(() => todoCards.value.filter((card) => (card.read_status || 'unread') !== 'read').length)

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

onMounted(loadTodoCards)
</script>
