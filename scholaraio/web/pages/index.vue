<template>
  <div class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
    <div class="rounded-3xl border border-blue-200 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 px-6 py-8 text-white shadow-xl">
      <p class="text-xs font-semibold uppercase tracking-[0.3em] text-blue-200">Todo Snapshot</p>
      <h1 class="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Todo Reading Cards</h1>
      <p class="mt-3 max-w-3xl text-sm leading-7 text-slate-200 sm:text-base">
        这里只保留 Zotero <code class="rounded bg-white/10 px-1.5 py-0.5 text-blue-100">Todo</code> collection 的阅读卡片。
        首页展示预览，点进二级卡片页再看完整总结；原来那 306 个旧 Library 卡片和 summary / method 展示已经移除。
      </p>
      <div class="mt-5 flex flex-wrap gap-3 text-sm text-blue-100">
        <span class="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">
          当前卡片 {{ filteredTodoCards.length }} / {{ todoCards.length }}
        </span>
        <span class="rounded-full border border-white/15 bg-white/10 px-3 py-1.5">
          已读本地保存，不回写后台
        </span>
      </div>
    </div>

    <div class="mt-6 grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:grid-cols-[minmax(0,1fr)_180px_180px]">
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
        <span class="mb-2 block text-sm font-medium text-slate-700">状态</span>
        <select
          v-model="statusFilter"
          class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        >
          <option value="">全部</option>
          <option value="unread">未读</option>
          <option value="read">已读</option>
        </select>
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

    <div v-if="loading" class="py-16 text-center">
      <div class="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
      <p class="mt-4 text-sm text-slate-500">Loading Todo snapshot...</p>
    </div>

    <div v-else-if="errorMessage" class="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorMessage }}
    </div>

    <div v-else-if="filteredTodoCards.length" class="mt-6 grid gap-5 xl:grid-cols-2">
      <article
        v-for="card in filteredTodoCards"
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
            <h2 class="mt-4 text-xl font-semibold leading-8 text-slate-900">{{ card.title }}</h2>
            <p class="mt-2 text-sm text-slate-600">{{ card.authors?.join(', ') || '作者信息缺失' }}</p>
            <p class="mt-1 text-xs text-slate-500">
              {{ card.year || '年份未知' }}<span v-if="card.journal"> · {{ card.journal }}</span>
            </p>
          </div>
        </div>

        <div class="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p class="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">预览</p>
          <p class="mt-3 text-sm leading-7 text-slate-700">{{ card.one_line_summary }}</p>
          <p v-if="previewText(card)" class="mt-3 text-sm leading-7 text-slate-600">
            {{ previewText(card) }}
          </p>
        </div>

        <div class="mt-5 flex flex-wrap gap-3">
          <button
            class="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
            @click="toggleTodoReadStatus(card.route_id)"
          >
            {{ card.read_status === 'read' ? '标记未读' : '标记已读' }}
          </button>

          <NuxtLink
            class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
            :to="todoDetailLink(card.route_id)"
          >
            查看总结
          </NuxtLink>

          <NuxtLink
            class="rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-sm font-medium text-blue-700 transition hover:bg-blue-100"
            :to="paperLink(card.route_id)"
          >
            查看论文
          </NuxtLink>
        </div>
      </article>
    </div>

    <div v-else class="mt-6 rounded-2xl border border-slate-200 bg-white px-4 py-12 text-center text-sm text-slate-500 shadow-sm">
      当前筛选条件下没有匹配到 Todo 卡片。
    </div>
  </div>
</template>

<script setup>
const TODO_READ_STATUS_STORAGE_KEY = 'scholaraio:todo-read-statuses'

const { fetchJson } = useStaticSiteData()

const searchQuery = ref('')
const statusFilter = ref('')
const sortBy = ref('')
const todoCards = ref([])
const loading = ref(true)
const errorMessage = ref('')
const todoReadStatuses = ref({})

const normalizedQuery = computed(() => searchQuery.value.trim().toLowerCase())

const matchesSearch = (values) => {
  const query = normalizedQuery.value
  if (!query) return true
  return values.some((value) => String(value || '').toLowerCase().includes(query))
}

const applyTodoReadStatuses = () => {
  todoCards.value = todoCards.value.map((card) => {
    const localStatus = todoReadStatuses.value[card.route_id]
    const readStatus = localStatus === 'read' || localStatus === 'unread'
      ? localStatus
      : (card.read_status || 'unread')
    return { ...card, read_status: readStatus }
  })
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

  if (statusFilter.value) {
    result = result.filter((card) => (card.read_status || 'unread') === statusFilter.value)
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

const restoreTodoReadStatuses = () => {
  if (!import.meta.client) return

  try {
    const raw = window.localStorage.getItem(TODO_READ_STATUS_STORAGE_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object') {
      todoReadStatuses.value = parsed
    }
  } catch (error) {
    console.error('Failed to restore todo read statuses:', error)
  }
}

const persistTodoReadStatuses = () => {
  if (!import.meta.client) return

  try {
    window.localStorage.setItem(TODO_READ_STATUS_STORAGE_KEY, JSON.stringify(todoReadStatuses.value))
  } catch (error) {
    console.error('Failed to persist todo read statuses:', error)
  }
}

const toggleTodoReadStatus = (routeId) => {
  const card = todoCards.value.find(item => item.route_id === routeId)
  if (!card) return

  const nextStatus = card.read_status === 'read' ? 'unread' : 'read'
  card.read_status = nextStatus
  todoReadStatuses.value = {
    ...todoReadStatuses.value,
    [routeId]: nextStatus,
  }
  persistTodoReadStatuses()
}

const statusClass = (status) => {
  const classes = {
    unread: 'bg-slate-100 text-slate-600',
    read: 'bg-emerald-100 text-emerald-700',
  }
  return classes[status] || classes.unread
}

const previewText = (card) => {
  const raw = String(card.core_innovation || '').trim()
  if (!raw) return ''
  return raw.length > 180 ? `${raw.slice(0, 180)}...` : raw
}

const todoDetailLink = (routeId) => routeId ? `/todo/${routeId}` : '#'
const paperLink = (routeId) => routeId ? `/paper/${routeId}` : '#'

const loadTodoCards = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const todoData = await fetchJson('todo-cards.json')
    todoCards.value = Array.isArray(todoData?.cards) ? todoData.cards : []
    applyTodoReadStatuses()
  } catch (error) {
    console.error('Failed to load todo cards:', error)
    errorMessage.value = 'Failed to load Todo snapshot.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  restoreTodoReadStatuses()
  await loadTodoCards()
})
</script>
