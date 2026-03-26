<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Library</h1>
      <p class="mt-1 text-sm text-gray-500">Search inside the papers that already have summary, method, and rating materials.</p>
    </div>

    <div class="mb-4 flex flex-col lg:flex-row gap-4">
      <div class="flex-1">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search papers..."
          class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          @input="debouncedSearch"
        />
      </div>
      <select v-model="projectFilter" class="px-4 py-2 border border-gray-300 rounded-md" @change="handleProjectChange">
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
        <p class="text-xs text-gray-500">当前范围返回 {{ papers.length }} 篇论文，检索只会在这个子集里执行。</p>
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
      <p class="mt-4 text-gray-500">Loading papers...</p>
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="paper in filteredPapers"
        :key="paper.dir_name"
        class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
        @click="goToPaper(paper.dir_name)"
      >
        <div class="flex items-start justify-between gap-3">
          <h3 class="text-lg font-semibold text-gray-900 line-clamp-2">{{ paper.title }}</h3>
          <button
            class="shrink-0 px-2 py-1 text-xs font-medium rounded-full transition-colors"
            :class="statusClass(paper.read_status)"
            @click.stop="toggleReadStatus(paper)"
          >
            {{ paper.read_status === 'read' ? '已读' : '未读' }}
          </button>
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

    <div v-if="!loading && filteredPapers.length === 0" class="text-center py-12">
      <p class="text-gray-500">No papers found in the current scope</p>
    </div>
  </div>
</template>

<script setup>
const searchQuery = ref('')
const projectFilter = ref('')
const statusFilter = ref('')
const tagFilter = ref('')
const sortBy = ref('')
const papers = ref([])
const loading = ref(true)
const availableProjects = ref([])

let searchTimeout = null
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadPapers()
  }, 300)
}

const currentProject = computed(() => {
  return availableProjects.value.find(project => project.name === projectFilter.value) || null
})

const scopeLabel = computed(() => {
  if (!projectFilter.value) {
    return '全库范围'
  }
  return `项目范围: ${currentProject.value?.name || projectFilter.value}`
})

const availableTags = computed(() => {
  const tags = new Set()
  for (const paper of papers.value) {
    for (const tag of paper.tags || []) {
      tags.add(tag)
    }
  }
  return [...tags].sort((a, b) => a.localeCompare(b))
})

watch(availableTags, (tags) => {
  if (tagFilter.value && !tags.includes(tagFilter.value)) {
    tagFilter.value = ''
  }
})

const statusClass = (status) => {
  const classes = {
    unread: 'bg-gray-100 text-gray-600',
    read: 'bg-green-100 text-green-600'
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

const filteredPapers = computed(() => {
  let result = papers.value

  if (statusFilter.value) {
    result = result.filter(p => (p.read_status || 'unread') === statusFilter.value)
  }

  if (tagFilter.value) {
    result = result.filter(p => p.tags?.includes(tagFilter.value))
  }

  if (sortBy.value === 'rating') {
    result = [...result].sort((a, b) => {
      const ratingA = a.rating?.overall_score || 0
      const ratingB = b.rating?.overall_score || 0
      return ratingB - ratingA
    })
  } else if (sortBy.value === 'citation') {
    result = [...result].sort((a, b) => (b.citation_count || 0) - (a.citation_count || 0))
  } else if (sortBy.value === 'year') {
    result = [...result].sort((a, b) => (b.year || 0) - (a.year || 0))
  }

  return result
})

const loadPapers = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchQuery.value.trim()) params.append('q', searchQuery.value.trim())
    if (projectFilter.value) params.append('project', projectFilter.value)

    const res = await fetch(`/api/papers?${params.toString()}`)
    papers.value = await res.json()
  } catch (e) {
    console.error('Failed to load papers:', e)
  } finally {
    loading.value = false
  }
}

const loadProjects = async () => {
  try {
    const res = await fetch('/api/projects')
    availableProjects.value = await res.json()
  } catch (e) {
    console.error('Failed to load projects:', e)
  }
}

const handleProjectChange = async () => {
  await loadPapers()
}

const clearProjectFilter = async () => {
  projectFilter.value = ''
  await loadPapers()
}

const toggleReadStatus = async (paper) => {
  const next = paper.read_status === 'read' ? 'unread' : 'read'
  try {
    const encodedId = encodeURIComponent(paper.dir_name)
    await fetch(`/api/papers/${encodedId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: next })
    })
    paper.read_status = next
  } catch (e) {
    console.error('Failed to toggle read status:', e)
  }
}

const goToPaper = (dirName) => {
  navigateTo(`/paper/${encodeURIComponent(dirName)}`)
}

onMounted(async () => {
  await loadProjects()
  await loadPapers()
})
</script>
