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
        <div v-else class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div v-if="searchResults.length > 0">
            <h3 class="font-semibold text-gray-900 mb-4">Search Results</h3>
            <div v-for="(result, i) in searchResults" :key="i" class="mb-4 pb-4 border-b border-gray-100 last:border-0">
              <p class="text-sm text-gray-500 mb-1">{{ result.section }}</p>
              <p class="text-gray-700">{{ result.content }}</p>
            </div>
          </div>
          <div v-else-if="content" v-html="renderMarkdown(content)"></div>
          <div v-else class="text-center py-12 text-gray-500">
            <p>Knowledge base is empty</p>
            <p class="text-sm mt-2">Add notes using the form on the right</p>
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
  return text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    .replace(/\n/gim, '<br>')
}

onMounted(() => {
  loadKnowledge()
  loadTags()
})
</script>
