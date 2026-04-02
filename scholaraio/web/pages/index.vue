<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Library</h1>
      <p class="mt-1 text-sm text-gray-500">Read-only GitHub Pages snapshot of papers with summary materials.</p>
    </div>

    <div class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      这个页面现在部署在 GitHub Pages 上，只保留浏览、筛选和阅读功能。已读状态、标签编辑和后台生成任务已移除。
    </div>

    <section class="mb-8 overflow-hidden rounded-2xl border border-blue-200 bg-white shadow-sm">
      <div class="border-b border-blue-100 bg-gradient-to-r from-blue-50 via-sky-50 to-cyan-50 px-5 py-4">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="text-xs font-semibold uppercase tracking-[0.24em] text-blue-700">Todo Summary Card</p>
            <h2 class="mt-2 text-2xl font-semibold text-slate-900">{{ featuredTodoCard.title }}</h2>
            <p class="mt-2 text-sm text-slate-600">
              {{ featuredTodoCard.authors.join(', ') }} · {{ featuredTodoCard.year }} · {{ featuredTodoCard.venue }}
            </p>
            <p class="mt-2 text-sm text-slate-500">来自 Zotero `Todo` collection 的示例总结卡片</p>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <span class="rounded-full border border-blue-200 bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
              Todo
            </span>
            <span
              class="rounded-full px-3 py-1 text-xs font-medium"
              :class="statusClass(featuredTodoReadStatus)"
            >
              {{ featuredTodoReadStatus === 'read' ? '已读' : '未读' }}
            </span>
            <button
              class="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              @click="toggleFeaturedTodoReadStatus"
            >
              {{ featuredTodoReadStatus === 'read' ? '标记未读' : '标记已读' }}
            </button>
            <button
              class="rounded-md bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
              @click="goToPaper(featuredTodoCard.routeId)"
            >
              查看论文
            </button>
          </div>
        </div>
      </div>

      <div class="grid gap-4 px-5 py-5 lg:grid-cols-2">
        <article class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <h3 class="text-sm font-semibold text-slate-900">1. 核心创新点</h3>
          <p class="mt-3 text-sm leading-7 text-slate-700">{{ featuredTodoCard.coreInnovation }}</p>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <h3 class="text-sm font-semibold text-slate-900">2. 技术创新拆解</h3>
          <div class="mt-3 space-y-3">
            <div v-for="item in featuredTodoCard.technicalContributions" :key="item.title" class="rounded-xl border border-slate-200 bg-white px-3 py-3">
              <p class="text-sm font-medium text-slate-900">{{ item.title }}</p>
              <p class="mt-1 text-sm leading-6 text-slate-700">{{ item.body }}</p>
            </div>
          </div>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <h3 class="text-sm font-semibold text-slate-900">3. 方法论突破</h3>
          <div class="mt-3 space-y-3 text-sm leading-6 text-slate-700">
            <p><span class="font-medium text-slate-900">新颖性：</span>{{ featuredTodoCard.methodologicalBreakthrough.novelty }}</p>
            <p><span class="font-medium text-slate-900">关键技术：</span>{{ featuredTodoCard.methodologicalBreakthrough.keyTechnique }}</p>
            <p><span class="font-medium text-slate-900">理论支撑：</span>{{ featuredTodoCard.methodologicalBreakthrough.theory }}</p>
          </div>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
          <h3 class="text-sm font-semibold text-slate-900">4. 实验验证</h3>
          <div class="mt-3 space-y-3 text-sm leading-6 text-slate-700">
            <p><span class="font-medium text-slate-900">主要 benchmark：</span>{{ featuredTodoCard.keyResults.benchmarks }}</p>
            <p><span class="font-medium text-slate-900">性能提升：</span>{{ featuredTodoCard.keyResults.improvements }}</p>
            <p><span class="font-medium text-slate-900">关键贡献组件：</span>{{ featuredTodoCard.keyResults.ablation }}</p>
          </div>
        </article>

        <article class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 lg:col-span-2">
          <h3 class="text-sm font-semibold text-slate-900">5. 局限与启发</h3>
          <div class="mt-3 grid gap-3 md:grid-cols-3">
            <div class="rounded-xl border border-slate-200 bg-white px-3 py-3">
              <p class="text-sm font-medium text-slate-900">当前局限</p>
              <p class="mt-1 text-sm leading-6 text-slate-700">{{ featuredTodoCard.limitations.current }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-white px-3 py-3">
              <p class="text-sm font-medium text-slate-900">未来方向</p>
              <p class="mt-1 text-sm leading-6 text-slate-700">{{ featuredTodoCard.limitations.future }}</p>
            </div>
            <div class="rounded-xl border border-slate-200 bg-white px-3 py-3">
              <p class="text-sm font-medium text-slate-900">可迁移性</p>
              <p class="mt-1 text-sm leading-6 text-slate-700">{{ featuredTodoCard.limitations.transferability }}</p>
            </div>
          </div>
        </article>

        <article class="rounded-2xl border border-slate-900 bg-slate-900 px-4 py-4 text-white lg:col-span-2">
          <h3 class="text-sm font-semibold text-slate-100">6. 一句话总结</h3>
          <p class="mt-3 text-base leading-7 text-slate-100">{{ featuredTodoCard.oneLineSummary }}</p>
        </article>
      </div>
    </section>

    <div class="mb-4 flex flex-col lg:flex-row gap-4">
      <div class="flex-1">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search papers..."
          class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>
      <select v-model="projectFilter" class="px-4 py-2 border border-gray-300 rounded-md">
        <option value="">全库范围</option>
        <option v-for="project in availableProjects" :key="project.name" :value="project.name">
          {{ project.name }} ({{ project.paper_count }})
        </option>
      </select>
      <select v-model="statusFilter" class="px-4 py-2 border border-gray-300 rounded-md">
        <option value="">全部</option>
        <option value="unread">未读</option>
        <option value="read">已读</option>
      </select>
      <select v-model="tagFilter" class="px-4 py-2 border border-gray-300 rounded-md">
        <option value="">All Tags</option>
        <option v-for="tag in availableTags" :key="tag" :value="tag">{{ tag }}</option>
      </select>
      <select v-model="sortBy" class="px-4 py-2 border border-gray-300 rounded-md">
        <option value="">默认排序</option>
        <option value="rating">按评分</option>
        <option value="citation">按引用量</option>
        <option value="year">按年份</option>
      </select>
    </div>

    <div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3">
      <div>
        <p class="text-sm font-medium text-gray-900">{{ scopeLabel }}</p>
        <p class="text-xs text-gray-500">当前范围返回 {{ scopedPapers.length }} 篇论文，检索在静态快照中本地完成。</p>
      </div>
      <button
        v-if="projectFilter"
        class="px-3 py-2 text-sm rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50"
        @click="clearProjectFilter"
      >
        返回全库
      </button>
    </div>

    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-4 text-gray-500">Loading snapshot...</p>
    </div>

    <div v-else-if="errorMessage" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorMessage }}
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="paper in filteredPapers"
        :key="paper.route_id || paper.paper_id || paper.dir_name"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
        @click="goToPaper(paper.route_id)"
      >
        <div class="flex items-start justify-between gap-3">
          <h3 class="text-lg font-semibold text-gray-900 line-clamp-2">{{ paper.title }}</h3>
          <span
            class="shrink-0 px-2 py-1 text-xs font-medium rounded-full"
            :class="statusClass(paper.read_status)"
          >
            {{ paper.read_status === 'read' ? '已读' : '未读' }}
          </span>
        </div>
        <p class="mt-2 text-sm text-gray-600">{{ paper.authors?.join(', ') }}</p>
        <p class="mt-1 text-xs text-gray-500">{{ paper.year }} · {{ paper.journal }}</p>

        <div v-if="paper.rating" class="mt-2 flex items-center gap-2">
          <span class="text-sm font-medium" :class="ratingClass(paper.rating.overall_score)">
            ⭐ {{ paper.rating.overall_score?.toFixed(1) }}
          </span>
          <span class="text-xs text-gray-400">
            创新:{{ paper.rating.innovation }} | 技术:{{ paper.rating.technical_quality }}
          </span>
        </div>

        <div class="mt-3 flex flex-wrap gap-2">
          <span class="px-2 py-0.5 text-xs rounded-full border" :class="materialClass(paper.materials?.summary)">Summary</span>
          <span class="px-2 py-0.5 text-xs rounded-full border" :class="materialClass(paper.materials?.method)">Method</span>
          <span class="px-2 py-0.5 text-xs rounded-full border" :class="materialClass(paper.materials?.rating)">Rating</span>
        </div>

        <div v-if="paper.tags?.length" class="mt-3 flex flex-wrap gap-1">
          <span
            v-for="tag in paper.tags"
            :key="tag"
            class="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
          >
            {{ tag }}
          </span>
        </div>
      </div>
    </div>

    <div v-if="!loading && !errorMessage && filteredPapers.length === 0" class="text-center py-12">
      <p class="text-gray-500">No papers found in the current snapshot scope</p>
    </div>
  </div>
</template>

<script setup>
const LIBRARY_FILTERS_STORAGE_KEY = 'scholaraio:library-filters'
const FEATURED_TODO_STATUS_STORAGE_KEY = 'scholaraio:featured-todo-status'
const FEATURED_TODO_ROUTE_ID = 'bd480aa8-bbbd-491f-9bf7-b24918266b76'

const featuredTodoCard = {
  routeId: FEATURED_TODO_ROUTE_ID,
  title: 'DTC: Deep Tracking Control',
  year: 2024,
  venue: 'Science Robotics',
  authors: ['Fabian Jenelten', 'Junzhe He', 'Farbod Farshidian', 'Marco Hutter'],
  coreInnovation: 'DTC 的核心创新，是把轨迹优化生成的参考落脚点直接变成强化学习策略的训练目标，让策略不再自己摸索哪里落脚，而是专注于如何鲁棒地把脚落到规划器想要的位置上。它真正统一了模型控制的精度与学习控制的恢复能力，解决了稀疏落脚点地形上既要足点精确、又要抗扰鲁棒的矛盾。',
  technicalContributions: [
    {
      title: '创新点 1：混合式跟踪控制架构',
      body: '用轨迹优化器在线生成参考运动，用深度策略去跟踪优化后的 foothold，而不是直接让策略从稀疏奖励里学整套 locomotion。这样把高层规划难题和低层鲁棒执行明确解耦，显著降低了学习难度。'
    },
    {
      title: '创新点 2：只暴露对泛化最关键的参考信息',
      body: '策略不直接吃完整优化轨迹，而是只看平面落脚点、touchdown 目标关节位形、接触时序和局部高度扫描，减少对特定 planner 细节的依赖，提升跨 planner 泛化。'
    },
    {
      title: '创新点 3：硬跟踪奖励 + consistency 奖励',
      body: '作者把 foothold tracking 作为核心训练目标，并额外引入相邻规划解一致性的奖励，既避免拖脚式伪最优，又抑制困难地形前的犹豫行为。'
    }
  ],
  methodologicalBreakthrough: {
    novelty: '它不是简单在模型控制前面加一个学习模块，而是把轨迹优化当作在线 reference generator，把 RL 变成对 reference 的鲁棒跟踪器。',
    keyTechnique: '核心技术是 TAMOLS 轨迹优化、低层 MLP 策略、asymmetric actor-critic、足间局部高度扫描、foothold hard-tracking reward 和 consistency reward 的组合。',
    theory: '没有新的强理论证明，但方法论上非常清晰：让 TO 负责可规划性和结构先验，让 RL 负责闭环鲁棒性和恢复行为。'
  },
  keyResults: {
    benchmarks: '真实世界和仿真中的 gaps、stepping stones、narrow beams、stairs、slippery ground、soft/deformable ground、tall boxes 等复杂地形。',
    improvements: '平地足点跟踪误差平均约 2.3 cm，标准差约 0.48 cm；配合更强 planner 时可爬升 0.48 m 高台，比 baseline-rl-1 高 50%，比 baseline-rl-2 报告结果高 380%；对 0.6 m gap 序列和 1.8 m beam 保持 100% 成功率。',
    ablation: '最关键的不是某个单独网络模块，而是优化器在线给参考、策略只学鲁棒跟踪这个训练范式本身，尤其是 foothold tracking reward 和 reference 观察设计。'
  },
  limitations: {
    current: '整体能力仍依赖上层 planner 质量；如果 planner 给出的 foothold pattern 超出训练分布，tracking 性能会下降，且固定 trot gait 仍限制了动作多样性。',
    future: '下一步很自然是让策略反过来影响 planner，例如调整接触时序或直接修改 cost function，形成真正双向耦合的 hybrid control。',
    transferability: '这个思路很适合迁移到 humanoid foothold control、loco-manipulation、dynamic stepping，甚至部分机械臂接触控制任务。'
  },
  oneLineSummary: 'DTC 把稀疏地形 locomotion 从直接学任务改写成学习鲁棒跟踪优化足点，从而同时拿到了厘米级足点精度、跨 planner 泛化能力和真实环境恢复鲁棒性。'
}

const { fetchJson } = useStaticSiteData()

const searchQuery = ref('')
const projectFilter = ref('')
const statusFilter = ref('')
const tagFilter = ref('')
const sortBy = ref('')
const allPapers = ref([])
const loading = ref(true)
const errorMessage = ref('')
const availableProjects = ref([])
const projectMemberships = ref({})
const featuredTodoReadStatus = ref('unread')

const currentProject = computed(() => {
  return availableProjects.value.find(project => project.name === projectFilter.value) || null
})

const scopeLabel = computed(() => {
  if (!projectFilter.value) {
    return '全库范围'
  }
  return `项目范围: ${currentProject.value?.name || projectFilter.value}`
})

const scopedPapers = computed(() => {
  let result = allPapers.value

  if (projectFilter.value) {
    const allowed = new Set(projectMemberships.value[projectFilter.value] || [])
    result = result.filter((paper) => allowed.has(paper.paper_id))
  }

  const query = searchQuery.value.trim().toLowerCase()
  if (query) {
    result = result.filter((paper) => {
      return [
        paper.title,
        paper.abstract,
        paper.journal,
        paper.doi,
        ...(paper.authors || []),
        ...(paper.tags || []),
      ].some((value) => String(value || '').toLowerCase().includes(query))
    })
  }

  return result
})

const availableTags = computed(() => {
  const tags = new Set()
  for (const paper of scopedPapers.value) {
    for (const tag of paper.tags || []) {
      tags.add(tag)
    }
  }
  return [...tags].sort((a, b) => a.localeCompare(b))
})

const filteredPapers = computed(() => {
  let result = scopedPapers.value

  if (statusFilter.value) {
    result = result.filter(p => (p.read_status || 'unread') === statusFilter.value)
  }

  if (tagFilter.value) {
    result = result.filter(p => p.tags?.includes(tagFilter.value))
  }

  if (sortBy.value === 'rating') {
    result = [...result].sort((a, b) => (b.rating?.overall_score || 0) - (a.rating?.overall_score || 0))
  } else if (sortBy.value === 'citation') {
    result = [...result].sort((a, b) => (b.citation_count || 0) - (a.citation_count || 0))
  } else if (sortBy.value === 'year') {
    result = [...result].sort((a, b) => (b.year || 0) - (a.year || 0))
  }

  return result
})

watch(availableTags, (tags) => {
  if (tagFilter.value && !tags.includes(tagFilter.value)) {
    tagFilter.value = ''
  }
})

watch(availableProjects, (projects) => {
  if (!projectFilter.value) return
  const exists = projects.some(project => project.name === projectFilter.value)
  if (!exists) {
    projectFilter.value = ''
  }
})

const restoreSavedFilters = () => {
  if (!import.meta.client) return

  try {
    const raw = window.localStorage.getItem(LIBRARY_FILTERS_STORAGE_KEY)
    if (!raw) return

    const saved = JSON.parse(raw)
    searchQuery.value = typeof saved.searchQuery === 'string' ? saved.searchQuery : ''
    projectFilter.value = typeof saved.projectFilter === 'string' ? saved.projectFilter : ''
    statusFilter.value = typeof saved.statusFilter === 'string' ? saved.statusFilter : ''
    tagFilter.value = typeof saved.tagFilter === 'string' ? saved.tagFilter : ''
    sortBy.value = typeof saved.sortBy === 'string' ? saved.sortBy : ''
  } catch (error) {
    console.error('Failed to restore library filters:', error)
  }
}

const persistFilters = () => {
  if (!import.meta.client) return

  try {
    window.localStorage.setItem(LIBRARY_FILTERS_STORAGE_KEY, JSON.stringify({
      searchQuery: searchQuery.value,
      projectFilter: projectFilter.value,
      statusFilter: statusFilter.value,
      tagFilter: tagFilter.value,
      sortBy: sortBy.value,
    }))
  } catch (error) {
    console.error('Failed to persist library filters:', error)
  }
}

watch([searchQuery, projectFilter, statusFilter, tagFilter, sortBy], persistFilters)

const persistFeaturedTodoStatus = () => {
  if (!import.meta.client) return

  try {
    window.localStorage.setItem(FEATURED_TODO_STATUS_STORAGE_KEY, featuredTodoReadStatus.value)
  } catch (error) {
    console.error('Failed to persist featured todo status:', error)
  }
}

const syncFeaturedTodoStatusToLibrary = () => {
  const featuredPaper = allPapers.value.find((paper) => (
    paper.route_id === FEATURED_TODO_ROUTE_ID ||
    paper.paper_id === FEATURED_TODO_ROUTE_ID ||
    paper.title === featuredTodoCard.title
  ))

  if (featuredPaper) {
    featuredPaper.read_status = featuredTodoReadStatus.value
  }
}

const restoreFeaturedTodoStatus = () => {
  if (!import.meta.client) return false

  try {
    const raw = window.localStorage.getItem(FEATURED_TODO_STATUS_STORAGE_KEY)
    if (raw === 'read' || raw === 'unread') {
      featuredTodoReadStatus.value = raw
      return true
    }
  } catch (error) {
    console.error('Failed to restore featured todo status:', error)
  }

  return false
}

const initializeFeaturedTodoStatus = (restoredFromStorage) => {
  if (!restoredFromStorage) {
    const featuredPaper = allPapers.value.find((paper) => (
      paper.route_id === FEATURED_TODO_ROUTE_ID ||
      paper.paper_id === FEATURED_TODO_ROUTE_ID ||
      paper.title === featuredTodoCard.title
    ))
    featuredTodoReadStatus.value = featuredPaper?.read_status || 'unread'
  }

  syncFeaturedTodoStatusToLibrary()
}

const toggleFeaturedTodoReadStatus = () => {
  featuredTodoReadStatus.value = featuredTodoReadStatus.value === 'read' ? 'unread' : 'read'
  syncFeaturedTodoStatusToLibrary()
  persistFeaturedTodoStatus()
}

const statusClass = (status) => {
  const classes = {
    unread: 'bg-gray-100 text-gray-600',
    read: 'bg-green-100 text-green-600',
  }
  return classes[status] || classes.unread
}

const ratingClass = (score) => {
  if (!score) return 'text-gray-400'
  if (score >= 8) return 'text-green-600'
  if (score >= 6) return 'text-yellow-600'
  return 'text-red-600'
}

const materialClass = (enabled) => {
  return enabled
    ? 'border-blue-200 bg-blue-50 text-blue-700'
    : 'border-gray-200 bg-gray-50 text-gray-400'
}

const clearProjectFilter = () => {
  projectFilter.value = ''
}

const goToPaper = (routeId) => {
  if (!routeId) return
  navigateTo(`/paper/${routeId}`)
}

const loadLibrarySnapshot = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchJson('library.json')
    allPapers.value = Array.isArray(data?.papers) ? data.papers : []
    availableProjects.value = Array.isArray(data?.projects) ? data.projects : []
    projectMemberships.value = data?.project_memberships || {}
  } catch (error) {
    console.error('Failed to load library snapshot:', error)
    errorMessage.value = 'Failed to load static library snapshot.'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  restoreSavedFilters()
  const restoredFeaturedTodoStatus = restoreFeaturedTodoStatus()
  await loadLibrarySnapshot()
  initializeFeaturedTodoStatus(restoredFeaturedTodoStatus)
})
</script>
