<template>
  <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <button class="text-sm font-medium text-blue-600 transition hover:text-blue-800" @click="goBack">
        ← 返回 Todo 列表
      </button>

      <div class="flex flex-wrap gap-3">
        <button
          v-if="card"
          class="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
          @click="toggleReadStatus"
        >
          {{ resolvedReadStatus === 'read' ? '标记未读' : '标记已读' }}
        </button>
        <NuxtLink
          v-if="card"
          class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
          :to="paperLink(card.route_id)"
        >
          查看论文
        </NuxtLink>
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
    </div>
  </div>
</template>

<script setup>
const TODO_READ_STATUS_STORAGE_KEY = 'scholaraio:todo-read-statuses'

const { fetchJson } = useStaticSiteData()
const route = useRoute()
const routeId = computed(() => String(route.params.id || '').trim())

const loading = ref(true)
const errorMessage = ref('')
const card = ref(null)
const localReadStatuses = ref({})

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

const persistReadStatuses = () => {
  if (!import.meta.client) return

  try {
    window.localStorage.setItem(TODO_READ_STATUS_STORAGE_KEY, JSON.stringify(localReadStatuses.value))
  } catch (error) {
    console.error('Failed to persist todo read statuses:', error)
  }
}

const statusClass = (status) => {
  const classes = {
    unread: 'bg-slate-100 text-slate-600',
    read: 'bg-emerald-100 text-emerald-700',
  }
  return classes[status] || classes.unread
}

const paperLink = (id) => id ? `/paper/${id}` : '#'

const goBack = () => navigateTo('/')

const toggleReadStatus = () => {
  if (!card.value?.route_id) return

  const nextStatus = resolvedReadStatus.value === 'read' ? 'unread' : 'read'
  card.value = { ...card.value, read_status: nextStatus }
  localReadStatuses.value = {
    ...localReadStatuses.value,
    [card.value.route_id]: nextStatus,
  }
  persistReadStatuses()
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
