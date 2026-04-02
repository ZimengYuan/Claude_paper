<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Library</h1>
      <p class="mt-1 text-sm text-gray-500">Read-only GitHub Pages snapshot of papers with summary materials.</p>
    </div>

    <div class="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      这个页面现在部署在 GitHub Pages 上，只保留浏览、筛选和阅读功能。已读状态、标签编辑和后台生成任务已移除。
    </div>

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
  await loadLibrarySnapshot()
})
</script>
