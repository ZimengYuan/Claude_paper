<template>
  <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
    <div class="rounded-3xl border border-blue-200 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 px-6 py-8 text-white shadow-xl">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-blue-200">Todo Snapshot</p>
      <h1 class="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Todo Reading Cards</h1>
      <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-200 sm:text-base">
        这里只保留 Zotero <code class="rounded bg-white/10 px-1.5 py-0.5 text-blue-100">Todo</code> collection 的阅读卡片。
      </p>
      <div class="mt-5 flex flex-wrap gap-3 text-sm text-blue-100">
        <span class="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">
          当前卡片 {{ filteredTodoCards.length }} / {{ todoCards.length }}
        </span>
        <span class="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">
          Todo 默认全部按未读展示
        </span>
      </div>
    </div>

    <div class="mt-6 space-y-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_180px]">
        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">搜索</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索标题、作者、术语、结论..."
            class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">排序</span>
          <select
            v-model="sortBy"
            class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          >
            <option value="">Todo 顺序</option>
            <option value="year">按年份</option>
            <option value="title">按标题</option>
          </select>
        </label>
      </div>

      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">作者包含</span>
          <input
            v-model="authorFilter"
            type="text"
            placeholder="例如 Hutter"
            class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">年份起</span>
          <input
            v-model.number="yearFrom"
            type="number"
            min="1900"
            max="2100"
            placeholder="例如 2020"
            class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">年份止</span>
          <input
            v-model.number="yearTo"
            type="number"
            min="1900"
            max="2100"
            placeholder="例如 2026"
            class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </label>

        <label class="block">
          <span class="mb-2 block text-sm font-medium text-slate-700">DOI</span>
          <select
            v-model="doiFilter"
            class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          >
            <option value="">全部</option>
            <option value="has">仅有 DOI</option>
            <option value="missing">仅无 DOI</option>
          </select>
        </label>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <button
          class="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          @click="clearFilters"
        >
          清空筛选
        </button>
        <span class="text-sm text-slate-500">命中 {{ filteredTodoCards.length }} 条</span>
      </div>
    </div>

    <div v-if="loading" class="py-16 text-center">
      <div class="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
      <p class="mt-4 text-sm text-slate-500">Loading Todo snapshot...</p>
    </div>

    <div v-else-if="errorMessage" class="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorMessage }}
    </div>

    <div v-else-if="filteredTodoCards.length" class="mt-6 grid gap-5 xl:grid-cols-2">
      <article
        v-for="card in pagedTodoCards"
        :key="card.route_id"
        class="flex h-full flex-col rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:shadow-lg"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              <span class="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-blue-700">
                Todo
              </span>
              <span class="rounded-full px-3 py-1 text-xs font-medium" :class="statusClass(card.read_status)">
                {{ card.read_status === 'read' ? '已读' : '未读' }}
              </span>
            </div>
            <h2 class="mt-4 text-xl font-semibold leading-8 text-slate-900" v-html="highlightText(card.title)"></h2>
            <p class="mt-2 text-sm text-slate-600" v-html="highlightText(card.authors?.join(', ') || '作者信息缺失')"></p>
            <p class="mt-1 text-xs text-slate-500">
              {{ card.year || '年份未知' }}<span v-if="card.journal"> · {{ card.journal }}</span>
            </p>
          </div>
        </div>

        <div class="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">预览</p>
          <p class="mt-3 text-sm leading-7 text-slate-700" v-html="highlightText(card.one_line_summary)"></p>
          <p v-if="previewText(card)" class="mt-3 text-sm leading-7 text-slate-600">
            {{ previewText(card) }}
          </p>
        </div>

        <div class="mt-5 flex flex-wrap gap-3">
          <NuxtLink
            class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
            :to="todoDetailLink(card.route_id)"
          >
            查看总结
          </NuxtLink>

          <a
            class="rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 transition hover:bg-blue-100"
            :href="paperLink(card)"
            :target="paperLink(card).startsWith('http') ? '_blank' : null"
            :rel="paperLink(card).startsWith('http') ? 'noopener noreferrer' : null"
          >
            查看论文
          </a>
        </div>
      </article>
    </div>

    <div v-if="filteredTodoCards.length" class="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 shadow-sm">
      <span>第 {{ currentPage }} / {{ totalPages }} 页（每页 {{ pageSize }} 条）</span>
      <div class="flex items-center gap-2">
        <button
          class="rounded-lg border border-slate-300 px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="currentPage <= 1"
          @click="currentPage = Math.max(1, currentPage - 1)"
        >上一页</button>
        <button
          class="rounded-lg border border-slate-300 px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="currentPage >= totalPages"
          @click="currentPage = Math.min(totalPages, currentPage + 1)"
        >下一页</button>
      </div>
    </div>

    <div v-else class="mt-6 rounded-2xl border border-slate-200 bg-white px-4 py-12 text-center text-sm text-slate-500 shadow-sm">
      当前筛选条件下没有匹配到 Todo 卡片。
    </div>
  </div>
</template>

<script setup>
const { fetchJson } = useStaticSiteData()
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
    unread: 'bg-slate-100 text-slate-600',
    read: 'bg-emerald-100 text-emerald-700',
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
  return safe.replace(regex, '<mark class="rounded bg-yellow-200/80 px-0.5">$1</mark>')
}

const previewText = (card) => {
  const raw = String(card.core_innovation || '').trim()
  if (!raw) return ''
  return raw.length > 180 ? raw.slice(0, 180) + '...' : raw
}

const todoDetailLink = (routeId) => routeId ? '/todo/' + routeId : '#'
const paperLink = (card) => {
  const paperRouteId = String(card?.paper_route_id || '').trim()
  if (paperRouteId) return appBaseUrl.value + 'paper/' + paperRouteId
  const doi = String(card?.doi || '').trim()
  if (doi) return 'https://doi.org/' + doi
  return '#'
}

const loadTodoCards = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const todoData = await fetchJson('todo-cards.json')
    const cards = Array.isArray(todoData?.cards) ? todoData.cards : []
    todoCards.value = cards.map((card) => ({
      ...card,
      read_status: 'unread',
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
