<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900">Knowledge Base</h1>
      <p class="mt-1 text-sm text-gray-500">Cross-paper notes and insights</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Knowledge Content -->
      <div class="lg:col-span-2">
        <!-- Search -->
        <div class="mb-4">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search knowledge base..."
            class="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            @input="debouncedSearch"
          />
        </div>

        <!-- Loading -->
        <div v-if="loading" class="text-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        </div>

        <!-- Knowledge Content -->
        <div v-else class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <!-- Tabs -->
          <div class="flex border-b border-gray-200 bg-slate-50">
            <button
              v-for="cat in ['All', 'General', 'Research', 'Method', 'Review']"
              :key="cat"
              class="px-5 py-3 text-sm font-medium transition-colors"
              :class="activeCategory === cat ? 'bg-white text-blue-600 border-b-2 border-blue-600' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
              @click="activeCategory = cat"
            >
              {{ cat }}
            </button>
          </div>

          <div class="p-6">
            <div v-if="searchResults.length > 0">
              <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <span class="text-blue-600">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                </span>
                Search Results
              </h3>
              <div class="space-y-4">
                <div v-for="(result, i) in searchResults" :key="i" class="bg-gray-50 border border-gray-100 rounded-lg p-4 transition hover:shadow-md">
                  <p class="text-xs font-semibold uppercase tracking-wider text-blue-600 mb-2">{{ result.section }}</p>
                  <p class="text-sm text-gray-700 leading-relaxed">{{ result.content }}</p>
                </div>
              </div>
            </div>
            <div v-else-if="filteredNotes.length > 0">
              <div class="space-y-4">
                <div v-for="(note, i) in filteredNotes" :key="i" class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition">
                  <div class="flex items-center justify-between mb-3 border-b border-slate-100 pb-3">
                    <span class="text-xs font-bold uppercase tracking-wider" :class="getCategoryColor(note.category)">{{ note.category }}</span>
                  </div>
                  <div class="prose prose-sm max-w-none prose-slate text-sm" v-html="renderMarkdown(note.content)"></div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-16">
              <div class="mx-auto w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
                <svg class="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
              </div>
              <p class="text-gray-900 font-medium">No knowledge notes found here.</p>
              <p class="text-sm text-gray-500 mt-1">Add a new note using the form on the right.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Add Note Form -->
      <div class="lg:col-span-1">
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h3 class="font-semibold text-gray-900 mb-3">Add Note</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select v-model="newNote.category" class="w-full border border-gray-300 rounded-md py-2 px-3">
                <option value="general">General</option>
                <option value="research">Research</option>
                <option value="method">Method</option>
                <option value="review">Review</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Note</label>
              <textarea
                v-model="newNote.content"
                rows="6"
                class="w-full border border-gray-300 rounded-md py-2 px-3"
                placeholder="Write your note..."
              ></textarea>
            </div>
            <button
              @click="addNote"
              :disabled="!newNote.content.trim()"
              class="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Add Note
            </button>
          </div>
        </div>

        <!-- Tags -->
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mt-4">
          <h3 class="font-semibold text-gray-900 mb-3">Registered Tags</h3>
          <div v-if="tags.length > 0" class="flex flex-wrap gap-2">
            <span
              v-for="tag in tags"
              :key="tag.tag"
              class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-sm"
              :style="tag.color ? { backgroundColor: tag.color + '20', color: tag.color } : {}"
            >
              {{ tag.tag }} ({{ tag.paper_count }})
            </span>
          </div>
          <p v-else class="text-sm text-gray-500">No tags registered</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const searchQuery = ref('')
const content = ref('')
const loading = ref(true)
const searchResults = ref([])
const tags = ref([])
const activeCategory = ref('All')

const parsedNotes = computed(() => {
  if (!content.value) return []
  const sections = content.value.split(/(?=^## (?:General|Research|Method|Review))/m)
  const notes = []

  let currentCategory = 'General'
  for (const section of sections) {
    if (!section.trim()) continue
    
    let sectionContent = section
    const match = section.match(/^## (General|Research|Method|Review)\s*\n/i)
    if (match) {
      currentCategory = match[1]
      sectionContent = section.substring(match[0].length)
    }

    const items = sectionContent.split(/^\s*[-*]\s+/m).filter(i => i.trim() !== '')
    for (const item of items) {
      if (item.trim()) {
        notes.push({
          category: currentCategory,
          content: item.trim()
        })
      }
    }
  }
  return notes
})

const filteredNotes = computed(() => {
  if (activeCategory.value === 'All') return parsedNotes.value
  return parsedNotes.value.filter(n => n.category.toLowerCase() === activeCategory.value.toLowerCase())
})

const getCategoryColor = (cat) => {
  const map = {
    'general': 'text-gray-600',
    'research': 'text-emerald-600',
    'method': 'text-blue-600',
    'review': 'text-purple-600'
  }
  return map[cat.toLowerCase()] || 'text-gray-600'
}

const newNote = ref({
  category: 'general',
  content: ''
})

let searchTimeout = null
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    searchKnowledge()
  }, 300)
}

const loadKnowledge = async () => {
  try {
    const res = await fetch('/api/knowledge')
    content.value = await res.text()
  } catch (e) {
    console.error('Failed to load knowledge:', e)
  } finally {
    loading.value = false
  }
}

const searchKnowledge = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  try {
    const res = await fetch(`/api/knowledge/search?q=${encodeURIComponent(searchQuery.value)}`)
    const data = await res.json()
    searchResults.value = data.results || []
  } catch (e) {
    console.error('Failed to search knowledge:', e)
  }
}

const addNote = async () => {
  try {
    await fetch('/api/knowledge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        note: newNote.value.content,
        category: newNote.value.category
      })
    })
    newNote.value.content = ''
    await loadKnowledge()
  } catch (e) {
    console.error('Failed to add note:', e)
  }
}

const loadTags = async () => {
  try {
    const res = await fetch('/api/tags')
    tags.value = await res.json()
  } catch (e) {
    console.error('Failed to load tags:', e)
  }
}

const renderMarkdown = (text) => {
  if (!text) return ''
  return text
    .replace(/^### (.*$)/gim, '<h3 class="text-sm font-semibold mt-2 mb-1 text-slate-800">$1</h3>')
    .replace(/^## (.*$)/gim, '<h2 class="text-base font-semibold mt-3 mb-2 text-slate-800">$1</h2>')
    .replace(/^# (.*$)/gim, '<h1 class="text-lg font-bold mt-4 mb-2 text-slate-900">$1</h1>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-semibold text-slate-900">$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em class="text-slate-700">$1</em>')
    .replace(/\[(.*?)\]\((.*?)\)/gim, '<a href="$2" class="text-blue-600 hover:underline" target="_blank">$1</a>')
    .replace(/`([^`]+)`/gim, '<code class="px-1.5 py-0.5 bg-slate-100 rounded text-pink-600 font-mono text-[13px]">$1</code>')
    .replace(/\n/gim, '<br>')
}

onMounted(() => {
  loadKnowledge()
  loadTags()
})
</script>
