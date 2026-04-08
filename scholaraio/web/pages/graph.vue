<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
    <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Research Graph</h1>
        <p class="mt-1 text-sm text-gray-500">
          Static citation, structure, and topic graph snapshots exported from the local library.
        </p>
      </div>
      <div class="text-xs text-gray-500">GitHub Pages read-only mode</div>
    </div>

    <div class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      图谱页面只读取全库（all papers）预计算快照，不再支持在线构建 topic model 或后端实时查询。
    </div>

    <div v-if="errorMessage" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorMessage }}
    </div>

    <div v-if="infoMessage" class="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      {{ infoMessage }}
    </div>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1fr),340px]">
      <ClientOnly>
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div v-if="loading" class="flex h-[800px] items-center justify-center">
            <div class="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
          </div>
          <div v-else-if="nodeCount === 0" class="flex h-[800px] items-center justify-center text-center text-sm text-gray-500">
            No graph data available for this snapshot.
          </div>
          <div v-else ref="graphContainer" class="h-[800px] w-full"></div>
        </div>
        <template #fallback>
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <div class="flex h-[800px] items-center justify-center">
              <div class="h-12 w-12 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600"></div>
            </div>
          </div>
        </template>
      </ClientOnly>

      <div class="space-y-4">
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 class="mb-4 text-sm font-semibold text-gray-900">Graph Controls</h2>

          <div class="space-y-4">
            <label class="block text-sm font-medium text-gray-700">
              <span class="mb-1 block">Mode</span>
              <select v-model="filters.mode" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50">
                <option value="citation">Citation Graph</option>
                <option value="structure">Structure Graph</option>
                <option value="topic">Topic Graph</option>
              </select>
            </label>

            <label class="block text-sm font-medium text-gray-700">
              <span class="mb-1 block">Visible Nodes</span>
              <select v-model.number="nodeLimit" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50">
                <option :value="200">Top 200</option>
                <option :value="500">Top 500</option>
                <option :value="1000">Top 1000</option>
                <option :value="0">All</option>
              </select>
            </label>

            <label class="block text-sm font-medium text-gray-700">
              <span class="mb-1 block">Find Node</span>
              <input
                v-model="nodeQuery"
                type="text"
                placeholder="title / keyword / doi"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50"
              />
            </label>

            <div>
              <span class="mb-2 block text-sm font-medium text-gray-700">Edge Types</span>
              <div class="grid grid-cols-2 gap-2 text-xs text-gray-700">
                <label class="inline-flex items-center gap-2 rounded-md border border-gray-200 px-2 py-1.5">
                  <input v-model="edgeTypeFilters.cites" type="checkbox" /> cites
                </label>
                <label class="inline-flex items-center gap-2 rounded-md border border-gray-200 px-2 py-1.5">
                  <input v-model="edgeTypeFilters.cited_by" type="checkbox" /> cited_by
                </label>
                <label class="inline-flex items-center gap-2 rounded-md border border-gray-200 px-2 py-1.5">
                  <input v-model="edgeTypeFilters.structure" type="checkbox" /> structure
                </label>
                <label class="inline-flex items-center gap-2 rounded-md border border-gray-200 px-2 py-1.5">
                  <input v-model="edgeTypeFilters.shared" type="checkbox" /> shared
                </label>
                <label class="inline-flex items-center gap-2 rounded-md border border-gray-200 px-2 py-1.5">
                  <input v-model="edgeTypeFilters.topic_similarity" type="checkbox" /> topic_similarity
                </label>
                <label class="inline-flex items-center gap-2 rounded-md border border-gray-200 px-2 py-1.5">
                  <input v-model="edgeTypeFilters.unknown" type="checkbox" /> unknown
                </label>
              </div>
            </div>

            <button
              class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              :disabled="!selectedNode"
              @click="focusNeighborsOnly = !focusNeighborsOnly"
            >
              {{ focusNeighborsOnly ? '取消聚焦邻居' : '聚焦当前节点邻居' }}
            </button>

            <p class="text-xs text-gray-500">当前模式始终基于全库文献图谱；节点数限制仅用于前端加速渲染。</p>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <div class="text-2xl font-semibold text-gray-900">{{ nodeCount }}</div>
            <div class="mt-1 text-xs uppercase tracking-wide text-gray-500">Nodes</div>
          </div>
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <div class="text-2xl font-semibold text-gray-900">{{ edgeCount }}</div>
            <div class="mt-1 text-xs uppercase tracking-wide text-gray-500">Edges</div>
          </div>
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <div class="text-2xl font-semibold text-gray-900">{{ paperCount }}</div>
            <div class="mt-1 text-xs uppercase tracking-wide text-gray-500">Papers</div>
          </div>
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <div class="text-2xl font-semibold text-gray-900">{{ auxiliaryStatValue }}</div>
            <div class="mt-1 text-xs uppercase tracking-wide text-gray-500">{{ auxiliaryStatLabel }}</div>
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 class="text-sm font-semibold text-gray-900">Legend</h2>
          <div class="mt-3 space-y-2 text-sm text-gray-600">
            <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-sky-600"></span>Paper node</div>
            <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-amber-500"></span>External DOI node</div>
            <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-purple-600"></span>Topic node</div>
          </div>
          <div class="mt-4 border-t border-gray-100 pt-3 text-xs text-gray-500">
            Edge mix: {{ edgeSummary }}
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-sm font-semibold text-gray-900">Selected Node</h2>
            <button
              v-if="selectedNode && selectedNode.route_id"
              class="rounded-md border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 transition hover:bg-gray-50"
              @click="openSelectedPaper"
            >
              Open Paper
            </button>
          </div>

          <div v-if="selectedNode" class="mt-3 space-y-3 text-sm text-gray-700">
            <div>
              <div class="text-xs uppercase tracking-wide text-gray-500">Title</div>
              <div class="mt-1 font-medium text-gray-900">{{ selectedNode.title || selectedNode.label }}</div>
            </div>
            <div v-if="selectedRoles.length">
              <div class="text-xs uppercase tracking-wide text-gray-500">Role</div>
              <div class="mt-1">{{ selectedRoles.join(', ') }}</div>
            </div>
            <div v-if="selectedNode.keywords && selectedNode.keywords.length">
              <div class="text-xs uppercase tracking-wide text-gray-500">Keywords</div>
              <div class="mt-2 flex flex-wrap gap-2">
                <span
                  v-for="keyword in selectedNode.keywords"
                  :key="keyword"
                  class="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700"
                >
                  {{ keyword }}
                </span>
              </div>
            </div>
            <div v-if="selectedNode.first_author || selectedNode.year">
              <div class="text-xs uppercase tracking-wide text-gray-500">Authors / Year</div>
              <div class="mt-1">
                {{ selectedNode.first_author || 'Unknown' }}
                <span v-if="selectedNode.year"> · {{ selectedNode.year }}</span>
              </div>
            </div>
            <div v-if="selectedNode.doi">
              <div class="text-xs uppercase tracking-wide text-gray-500">DOI</div>
              <div class="mt-1 break-all">{{ selectedNode.doi }}</div>
            </div>
            <div>
              <div class="text-xs uppercase tracking-wide text-gray-500">Degree</div>
              <div class="mt-1">{{ selectedNode.degree || 0 }}</div>
            </div>
            <div v-if="selectedNode.citation_count">
              <div class="text-xs uppercase tracking-wide text-gray-500">Citation Count</div>
              <div class="mt-1">{{ selectedNode.citation_count }}</div>
            </div>
            <div v-if="selectedNode.tags && selectedNode.tags.length">
              <div class="text-xs uppercase tracking-wide text-gray-500">Tags</div>
              <div class="mt-2 flex flex-wrap gap-2">
                <span
                  v-for="tag in selectedNode.tags"
                  :key="tag"
                  class="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
            <div v-if="selectedNode.representative_papers && selectedNode.representative_papers.length">
              <div class="text-xs uppercase tracking-wide text-gray-500">Representative Papers</div>
              <div class="mt-2 space-y-2">
                <button
                  v-for="paper in selectedNode.representative_papers.slice(0, 5)"
                  :key="paper.route_id || paper.paper_id || paper.title"
                  class="block w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-left text-xs text-gray-700 transition hover:bg-gray-100"
                  @click="openRepresentativePaper(paper.route_id || paper.paper_ref)"
                >
                  {{ paper.year || '?' }} · {{ paper.title }}
                </button>
              </div>
            </div>

            <div v-if="selectedEdgeBreakdown.length">
              <div class="text-xs uppercase tracking-wide text-gray-500">Connected Edges</div>
              <div class="mt-2 space-y-1.5">
                <div
                  v-for="item in selectedEdgeBreakdown"
                  :key="item.type"
                  class="rounded-md border border-gray-200 bg-gray-50 px-2.5 py-2 text-xs text-gray-700"
                >
                  <div class="font-medium">{{ item.type }} · {{ item.count }}</div>
                  <div class="mt-1 text-gray-500">{{ edgeTypeExplanation(item.type) }}</div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="mt-3 text-sm text-gray-500">
            Click a node to inspect its metadata.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import * as d3 from 'd3'

const { fetchJson } = useStaticSiteData()

const graphContainer = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const selectedNode = ref(null)
const graphManifest = ref(null)
const libraryPapers = ref([])
const nodeLimit = ref(200)
const nodeQuery = ref('')
const focusNeighborsOnly = ref(false)
const edgeTypeFilters = reactive({
  cites: true,
  cited_by: true,
  structure: true,
  shared: true,
  topic_similarity: true,
  unknown: true,
})
const graphData = ref({
  mode: 'citation',
  nodes: [],
  edges: [],
  stats: {
    nodes: 0,
    edges: 0,
    papers: 0,
    external: 0,
    topics: 0,
    edge_types: {},
  },
  message: '',
})

const filters = reactive({
  mode: 'citation',
})

const normalizedNodeQuery = computed(() => nodeQuery.value.trim().toLowerCase())

function edgeEndpointId(value) {
  if (value == null) return ''
  if (typeof value === 'object') return String(value.id || '')
  return String(value)
}

const allowedEdgeTypes = computed(() => {
  const allowed = new Set()
  for (const [type, enabled] of Object.entries(edgeTypeFilters)) {
    if (enabled) allowed.add(type)
  }
  return allowed
})

function nodeRank(node) {
  const degree = Number(node.degree || 0)
  const cites = Number(node.citation_count || 0)
  const roleBonus = (Array.isArray(node.roles) && node.roles.includes('center')) || node.role === 'center' ? 10000 : 0
  return roleBonus + degree * 10 + cites
}

const displayGraph = computed(() => {
  const baseNodes = Array.isArray(graphData.value.nodes) ? graphData.value.nodes : []
  const baseEdges = Array.isArray(graphData.value.edges) ? graphData.value.edges : []

  let visibleNodes = [...baseNodes]
  const query = normalizedNodeQuery.value
  if (query) {
    visibleNodes = visibleNodes.filter((node) => {
      const haystack = [
        node.title,
        node.label,
        node.doi,
        node.first_author,
        ...(Array.isArray(node.keywords) ? node.keywords : []),
        ...(Array.isArray(node.tags) ? node.tags : []),
      ].join(' ').toLowerCase()
      return haystack.includes(query)
    })
  }

  const limit = Number(nodeLimit.value || 0)
  if (limit > 0 && visibleNodes.length > limit) {
    visibleNodes = visibleNodes
      .sort((a, b) => nodeRank(b) - nodeRank(a))
      .slice(0, limit)
  }

  const visibleIds = new Set(visibleNodes.map((node) => node.id))
  let visibleEdges = baseEdges.filter((edge) => {
    const edgeType = String(edge.type || 'unknown')
    const sourceId = edgeEndpointId(edge.source)
    const targetId = edgeEndpointId(edge.target)
    return allowedEdgeTypes.value.has(edgeType) && visibleIds.has(sourceId) && visibleIds.has(targetId)
  })

  if (focusNeighborsOnly.value && selectedNode.value?.id) {
    const centerId = String(selectedNode.value.id)
    const neighborIds = new Set([centerId])
    for (const edge of visibleEdges) {
      const sourceId = edgeEndpointId(edge.source)
      const targetId = edgeEndpointId(edge.target)
      if (sourceId === centerId || targetId === centerId) {
        neighborIds.add(sourceId)
        neighborIds.add(targetId)
      }
    }
    visibleNodes = visibleNodes.filter((node) => neighborIds.has(String(node.id)))
    const neighborSet = new Set(visibleNodes.map((node) => String(node.id)))
    visibleEdges = visibleEdges.filter((edge) => {
      const sourceId = edgeEndpointId(edge.source)
      const targetId = edgeEndpointId(edge.target)
      return neighborSet.has(sourceId) && neighborSet.has(targetId)
    })
  }

  return {
    ...graphData.value,
    nodes: visibleNodes,
    edges: visibleEdges,
  }
})

const nodeCount = computed(() => displayGraph.value.nodes.length || 0)
const edgeCount = computed(() => displayGraph.value.edges.length || 0)
const paperCount = computed(() => displayGraph.value.nodes.filter((node) => node.type !== 'external' && node.type !== 'topic').length)
const selectedRoles = computed(() => {
  if (!selectedNode.value) return []
  if (Array.isArray(selectedNode.value.roles) && selectedNode.value.roles.length) return selectedNode.value.roles
  if (selectedNode.value.role) return [selectedNode.value.role]
  return []
})
const infoMessage = computed(() => displayGraph.value.message || '')
const edgeSummary = computed(() => {
  const counter = new Map()
  for (const edge of displayGraph.value.edges || []) {
    const key = edge.type || 'unknown'
    counter.set(key, (counter.get(key) || 0) + 1)
  }
  const entries = Array.from(counter.entries())
  if (entries.length === 0) return 'No visible edges'
  return entries.map(([type, count]) => `${type}: ${count}`).join(' · ')
})
const auxiliaryStatLabel = computed(() => displayGraph.value.mode === 'topic' ? 'Topics' : 'External')
const auxiliaryStatValue = computed(() => {
  if (displayGraph.value.mode === 'topic') {
    return displayGraph.value.nodes.filter((node) => node.type === 'topic').length
  }
  return displayGraph.value.nodes.filter((node) => node.type === 'external').length
})

const selectedEdgeBreakdown = computed(() => {
  if (!selectedNode.value?.id) return []
  const centerId = String(selectedNode.value.id)
  const counter = new Map()
  for (const edge of displayGraph.value.edges || []) {
    const sourceId = edgeEndpointId(edge.source)
    const targetId = edgeEndpointId(edge.target)
    if (sourceId !== centerId && targetId !== centerId) continue
    const key = String(edge.type || 'unknown')
    counter.set(key, (counter.get(key) || 0) + 1)
  }
  return Array.from(counter.entries())
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count)
})

function nodeColor(node) {
  if (node.type === 'topic') return '#7c3aed'
  if (node.type === 'external') return '#f59e0b'
  if ((node.roles || []).includes('center') || node.role === 'center') return '#dc2626'
  return '#0284c7'
}

function nodeRadius(node) {
  if (node.type === 'topic') return 16
  if (node.type === 'external') return 9
  return 11
}

function edgeColor(edge) {
  if (edge.type === 'topic_similarity') return '#8b5cf6'
  if (edge.type === 'shared' || edge.type === 'structure') return '#10b981'
  if (edge.type === 'cites' || edge.type === 'cited_by') return '#2563eb'
  return '#94a3b8'
}

function edgeWidth(edge) {
  const weight = Number(edge.weight || edge.shared_refs || edge.similarity || 1)
  return Math.max(1.5, Math.min(4, weight))
}

function edgeDash(edge) {
  if (edge.type === 'shared' || edge.type === 'structure') return '6 4'
  return null
}

function edgeTypeExplanation(type) {
  const map = {
    cites: '论文之间的引用或同年近邻关系。',
    cited_by: '被引用方向关系（若快照中存在）。',
    structure: '论文与结构节点（如 venue）之间的关联。',
    shared: '共享参考文献或结构相似连接。',
    topic_similarity: '论文与主题标签之间的关联。',
    unknown: '快照中未标注明确类型的边。',
  }
  return map[type] || map.unknown
}

async function loadLibrarySnapshot() {
  if (libraryPapers.value.length) return
  try {
    const payload = await fetchJson('library.json')
    const papers = Array.isArray(payload?.papers) ? payload.papers : []
    libraryPapers.value = papers
  } catch (error) {
    console.error('Failed to load library snapshot for fallback graph:', error)
    libraryPapers.value = []
  }
}

function normalizePaperNode(paper, index) {
  const id = String(paper.route_id || paper.paper_id || paper.doi || `paper-${index}`)
  return {
    id,
    type: 'paper',
    label: paper.title || id,
    title: paper.title || id,
    route_id: paper.route_id || paper.paper_id || '',
    doi: paper.doi || '',
    first_author: Array.isArray(paper.authors) && paper.authors.length ? paper.authors[0] : '',
    year: paper.year || null,
    citation_count: Number(paper.citation_count || 0),
    degree: 0,
    tags: Array.isArray(paper.tags) ? paper.tags : [],
    keywords: Array.isArray(paper.tags) ? paper.tags : [],
    roles: [],
  }
}

function addDegree(nodesById, edge) {
  const source = nodesById.get(edge.source)
  const target = nodesById.get(edge.target)
  if (source) source.degree = Number(source.degree || 0) + 1
  if (target) target.degree = Number(target.degree || 0) + 1
}

function buildFallbackGraph(mode) {
  const papers = libraryPapers.value.slice(0, 1500)
  const nodes = papers.map((paper, index) => normalizePaperNode(paper, index))
  const edges = []
  const nodesById = new Map(nodes.map((node) => [node.id, node]))

  if (mode === 'topic') {
    const topicMap = new Map()
    for (const node of nodes) {
      const tags = Array.isArray(node.tags) ? node.tags.slice(0, 4) : []
      for (const tag of tags) {
        const topicId = `topic:${String(tag).trim().toLowerCase()}`
        if (!topicMap.has(topicId)) {
          topicMap.set(topicId, {
            id: topicId,
            type: 'topic',
            label: String(tag),
            title: String(tag),
            degree: 0,
            keywords: [],
            tags: [],
          })
        }
        const edge = { source: node.id, target: topicId, type: 'topic_similarity', directed: false, weight: 1 }
        edges.push(edge)
      }
    }
    nodes.push(...topicMap.values())
  } else if (mode === 'structure') {
    const venueMap = new Map()
    for (const node of nodes) {
      const venue = String(node.title && papers.find((p) => (p.route_id || p.paper_id || p.doi) === node.id)?.journal || '').trim()
      if (!venue) continue
      const venueId = `venue:${venue.toLowerCase()}`
      if (!venueMap.has(venueId)) {
        venueMap.set(venueId, {
          id: venueId,
          type: 'topic',
          label: venue,
          title: venue,
          degree: 0,
          keywords: [],
          tags: [],
        })
      }
      edges.push({ source: node.id, target: venueId, type: 'structure', directed: false, weight: 1 })
    }
    nodes.push(...venueMap.values())
  } else {
    const byYear = new Map()
    for (const node of nodes) {
      const key = String(node.year || 'unknown')
      if (!byYear.has(key)) byYear.set(key, [])
      byYear.get(key).push(node)
    }
    for (const bucket of byYear.values()) {
      bucket.sort((a, b) => Number(b.citation_count || 0) - Number(a.citation_count || 0))
      const top = bucket.slice(0, 20)
      for (let i = 1; i < top.length; i++) {
        edges.push({ source: top[i - 1].id, target: top[i].id, type: 'cites', directed: false, weight: 1 })
      }
    }
  }

  for (const edge of edges) {
    addDegree(nodesById, edge)
  }

  const paperCount = nodes.filter((node) => node.type === 'paper').length
  const topicCount = nodes.filter((node) => node.type === 'topic').length

  const edgeTypes = {}
  for (const edge of edges) {
    const key = edge.type || 'unknown'
    edgeTypes[key] = (edgeTypes[key] || 0) + 1
  }

  return {
    mode,
    scope: 'library',
    nodes,
    edges,
    stats: {
      nodes: nodes.length,
      edges: edges.length,
      papers: paperCount,
      external: 0,
      topics: topicCount,
      edge_types: edgeTypes,
    },
    message: 'Using fallback graph generated from library snapshot.',
  }
}

async function loadGraphManifest() {
  const data = await fetchJson('graphs/index.json')
  graphManifest.value = data
}

function resolveGraphPath() {
  if (!graphManifest.value) return ''
  return graphManifest.value.library?.[filters.mode] || ''
}

async function loadGraph() {
  const relativePath = resolveGraphPath()
  if (!relativePath) {
    await loadLibrarySnapshot()
    if (libraryPapers.value.length) {
      graphData.value = buildFallbackGraph(filters.mode)
      syncSelectedNode()
      await nextTick()
      renderGraph()
      return
    }

    graphData.value = {
      mode: filters.mode,
      nodes: [],
      edges: [],
      stats: { nodes: 0, edges: 0, papers: 0, external: 0, topics: 0, edge_types: {} },
      message: 'Graph snapshot not available.',
    }
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchJson(relativePath)
    if (Array.isArray(data?.nodes) && data.nodes.length > 0) {
      graphData.value = data
    } else {
      await loadLibrarySnapshot()
      graphData.value = libraryPapers.value.length
        ? buildFallbackGraph(filters.mode)
        : {
            ...data,
            message: data?.message || 'Graph snapshot is empty.',
          }
    }
    syncSelectedNode()
    await nextTick()
    renderGraph()
  } catch (error) {
    console.error('Failed to load graph snapshot:', error)
    await loadLibrarySnapshot()
    if (libraryPapers.value.length) {
      graphData.value = buildFallbackGraph(filters.mode)
      syncSelectedNode()
      await nextTick()
      renderGraph()
      return
    }
    errorMessage.value = 'Failed to load static graph snapshot.'
  } finally {
    loading.value = false
  }
}

function syncSelectedNode() {
  const nodes = displayGraph.value.nodes || []
  if (!nodes.length) {
    selectedNode.value = null
    return
  }
  if (selectedNode.value) {
    const match = nodes.find((node) => node.id === selectedNode.value.id)
    if (match) {
      selectedNode.value = match
      return
    }
  }
  selectedNode.value = nodes.find((node) => (node.roles || []).includes('center') || node.role === 'center') || nodes[0]
}

function renderGraph() {
  if (!graphContainer.value) return

  const nodes = (displayGraph.value.nodes || []).map((node) => ({ ...node }))
  const edges = (displayGraph.value.edges || []).map((edge) => ({ ...edge }))
  const container = graphContainer.value
  container.innerHTML = ''

  if (!nodes.length) return

  const width = container.clientWidth || 900
  const height = container.clientHeight || 680

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    .style('background', '#fcfcfd')

  const defs = svg.append('defs')
  defs.append('marker')
    .attr('id', 'graph-arrow')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 18)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#64748b')

  const root = svg.append('g')
  svg.call(
    d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        root.attr('transform', event.transform)
      })
  )

  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id((d) => d.id).distance((d) => d.type === 'topic_similarity' ? 140 : 110))
    .force('charge', d3.forceManyBody().strength(-280))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius((d) => nodeRadius(d) + 18))

  const link = root.append('g')
    .attr('stroke-linecap', 'round')
    .selectAll('line')
    .data(edges)
    .join('line')
    .attr('stroke', (d) => edgeColor(d))
    .attr('stroke-width', (d) => edgeWidth(d))
    .attr('stroke-opacity', 0.78)
    .attr('stroke-dasharray', (d) => edgeDash(d))
    .attr('marker-end', (d) => d.directed ? 'url(#graph-arrow)' : null)

  const node = root.append('g')
    .selectAll('g')
    .data(nodes)
    .join('g')
    .style('cursor', 'pointer')
    .call(
      d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended)
    )

  node.append('circle')
    .attr('r', (d) => nodeRadius(d))
    .attr('fill', (d) => nodeColor(d))
    .attr('stroke', '#ffffff')
    .attr('stroke-width', 2)

  node.append('text')
    .text((d) => {
      const label = d.label || d.title || d.id
      return label.length > 28 ? `${label.slice(0, 25)}...` : label
    })
    .attr('x', (d) => nodeRadius(d) + 6)
    .attr('y', 4)
    .attr('font-size', '11px')
    .attr('fill', '#1f2937')

  node.append('title')
    .text((d) => d.title || d.label || d.id)

  node.on('click', (event, d) => {
    event.stopPropagation()
    selectedNode.value = d
  })

  svg.on('click', () => {
    selectedNode.value = null
  })

  simulation.on('tick', () => {
    link
      .attr('x1', (d) => d.source.x)
      .attr('y1', (d) => d.source.y)
      .attr('x2', (d) => d.target.x)
      .attr('y2', (d) => d.target.y)

    node.attr('transform', (d) => `translate(${d.x},${d.y})`)
  })

  function dragstarted(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    event.subject.fx = event.subject.x
    event.subject.fy = event.subject.y
  }

  function dragged(event) {
    event.subject.fx = event.x
    event.subject.fy = event.y
  }

  function dragended(event) {
    if (!event.active) simulation.alphaTarget(0)
    event.subject.fx = null
    event.subject.fy = null
  }
}

function openSelectedPaper() {
  if (!selectedNode.value?.route_id) return
  navigateTo(`/paper/${selectedNode.value.route_id}`)
}

function openRepresentativePaper(routeId) {
  if (!routeId) return
  navigateTo(`/paper/${routeId}`)
}

watch(() => filters.mode, async () => {
  await loadGraph()
})

watch(() => [nodeLimit.value, normalizedNodeQuery.value], async () => {
  syncSelectedNode()
  await nextTick()
  renderGraph()
})

watch(() => [
  edgeTypeFilters.cites,
  edgeTypeFilters.cited_by,
  edgeTypeFilters.structure,
  edgeTypeFilters.shared,
  edgeTypeFilters.topic_similarity,
  edgeTypeFilters.unknown,
  focusNeighborsOnly.value,
  selectedNode.value?.id,
], async () => {
  syncSelectedNode()
  await nextTick()
  renderGraph()
})

onMounted(async () => {
  try {
    await loadGraphManifest()
    await loadGraph()
  } catch (error) {
    console.error('Failed to initialize graph snapshot:', error)
    errorMessage.value = 'Failed to initialize graph snapshot.'
  }
})
</script>
