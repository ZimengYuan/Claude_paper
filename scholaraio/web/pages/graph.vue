<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
    <div class="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Research Graph</h1>
        <p class="mt-1 text-sm text-gray-500">
          Switch between citation paths, paper structure maps, and topic clusters.
        </p>
      </div>
      <div class="flex flex-wrap gap-3">
        <button
          v-if="filters.mode === 'topic'"
          class="inline-flex items-center justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
          :disabled="buildingTopicGraph"
          @click="buildTopicGraph"
        >
          {{ buildingTopicGraph ? 'Building...' : 'Build Topic Model' }}
        </button>
        <button
          class="inline-flex items-center justify-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
          :disabled="loading"
          @click="loadGraph"
        >
          {{ loading ? 'Loading...' : 'Update Graph' }}
        </button>
      </div>
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
            No graph data available for this scope.
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
        <!-- Control Panel -->
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <h2 class="text-sm font-semibold text-gray-900 mb-4">Graph Controls</h2>
          
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
              <span class="mb-1 block">Scope</span>
              <select v-model="filters.scope" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50">
                <option value="library">Library</option>
                <option value="project">Project</option>
                <option value="paper">Paper</option>
              </select>
            </label>

            <label v-if="filters.scope === 'project'" class="block text-sm font-medium text-gray-700">
              <span class="mb-1 block">Project</span>
              <select
                v-model="filters.project"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50"
              >
                <option value="">{{ projects.length ? 'Select a project' : 'No projects' }}</option>
                <option v-for="project in projects" :key="project.name" :value="project.name">
                  {{ project.name }} ({{ project.paper_count }})
                </option>
              </select>
            </label>

            <label v-if="filters.scope === 'paper'" class="block text-sm font-medium text-gray-700">
              <span class="mb-1 block">Paper Ref</span>
              <input
                v-model.trim="filters.paperRef"
                type="text"
                class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50"
                placeholder="dir_name / UUID / DOI"
              >
            </label>

            <div class="grid grid-cols-2 gap-3">
              <label class="block text-sm font-medium text-gray-700" :class="{ 'opacity-50': filters.mode !== 'structure' }">
                <span class="mb-1 block">Min Shared</span>
                <input
                  v-model.number="filters.minShared"
                  type="number"
                  min="1"
                  max="20"
                  class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50"
                  :disabled="filters.mode !== 'structure'"
                >
              </label>

              <label class="block text-sm font-medium text-gray-700">
                <span class="mb-1 block">Max Nodes</span>
                <input
                  v-model.number="filters.maxNodes"
                  type="number"
                  min="5"
                  max="300"
                  class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50"
                >
              </label>
            </div>
            
            <div v-if="filters.mode === 'structure'" class="rounded-lg border border-slate-200 bg-slate-50 p-3 mt-2 text-xs">
              <div class="flex items-center justify-between mb-2">
                <span class="font-medium text-slate-700">Edge Threshold</span>
                <span class="font-bold text-slate-900">{{ thresholdDisplay }}</span>
              </div>
              <input
                v-model.number="structureThreshold"
                type="range"
                class="w-full accent-slate-700 mb-2"
                :min="thresholdBounds.min"
                :max="thresholdBounds.max"
                :step="thresholdBounds.step"
                :disabled="thresholdBounds.max <= 0"
              >
              <button
                class="w-full rounded border border-slate-300 bg-white py-1 px-2 text-center text-slate-600 hover:bg-slate-100 disabled:opacity-50"
                :disabled="thresholdBounds.max <= 0"
                @click="resetThreshold"
              >
                Reset to Show All
              </button>
            </div>
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
            <template v-if="filters.mode === 'citation'">
              <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-red-700"></span>Center paper</div>
              <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-blue-600"></span>Referenced paper</div>
              <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-emerald-600"></span>Citing paper</div>
              <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-amber-500"></span>External DOI node</div>
            </template>
            <template v-else-if="filters.mode === 'structure'">
              <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full border-2 border-red-800" :style="{ backgroundColor: '#cbd5e1' }"></span>Center paper</div>
              <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-slate-400"></span>Singleton / weakly connected paper</div>
              <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full" :style="{ backgroundColor: communitySwatch(1, 4) }"></span>Community-colored paper</div>
              <div class="flex items-center gap-2"><span class="inline-block h-[2px] w-5 bg-blue-600"></span>Direct citation relation</div>
              <div class="flex items-center gap-2"><span class="inline-block h-[2px] w-5 border-t-2 border-dashed border-green-600"></span>Shared-reference relation</div>
            </template>
            <template v-else>
              <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-amber-600"></span>Center topic</div>
              <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full" :style="{ backgroundColor: topicSwatch(1) }"></span>Topic cluster</div>
              <div class="flex items-center gap-2"><span class="inline-block h-[2px] w-5 bg-amber-600"></span>Topic similarity</div>
            </template>
          </div>
          <div class="mt-4 border-t border-gray-100 pt-3 text-xs text-gray-500">
            Edge mix: {{ edgeSummary }}
          </div>
          <div v-if="filters.mode === 'structure'" class="mt-4 border-t border-gray-100 pt-3">
            <div class="text-xs font-medium uppercase tracking-wide text-gray-500">Communities</div>
            <div v-if="communitySummary.length" class="mt-2 flex flex-wrap gap-2">
              <span
                v-for="community in communitySummary.slice(0, 8)"
                :key="community.label"
                class="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs text-gray-700"
              >
                <span class="h-2.5 w-2.5 rounded-full" :style="{ backgroundColor: community.color }"></span>
                {{ community.label }} ({{ community.size }})
              </span>
            </div>
            <div v-else class="mt-2 text-xs text-gray-500">
              Communities appear once the visible structure graph contains connected papers.
            </div>
          </div>
        </div>

        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-sm font-semibold text-gray-900">Selected Node</h2>
            <button
              v-if="selectedNode && selectedNode.paper_ref"
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
            <div v-if="selectedNode.role || selectedRoles.length">
              <div class="text-xs uppercase tracking-wide text-gray-500">Role</div>
              <div class="mt-1">{{ selectedRoles.join(', ') || selectedNode.role }}</div>
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
            <div v-if="selectedNode.community_label">
              <div class="text-xs uppercase tracking-wide text-gray-500">Community</div>
              <div class="mt-1">{{ selectedNode.community_label }}<span v-if="selectedNode.community_size"> · {{ selectedNode.community_size }} papers</span></div>
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
                  :key="paper.paper_ref || paper.paper_id"
                  class="block w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-left text-xs text-gray-700 transition hover:bg-gray-100"
                  @click="openRepresentativePaper(paper.paper_ref)"
                >
                  {{ paper.year || '?' }} · {{ paper.title }}
                </button>
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
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'

const COMMUNITY_COLORS = [
  '#0f766e',
  '#0369a1',
  '#4338ca',
  '#b45309',
  '#be123c',
  '#166534',
  '#7c3aed',
  '#1d4ed8',
  '#9a3412',
  '#047857'
]

const graphContainer = ref(null)
const loading = ref(false)
const buildingTopicGraph = ref(false)
const errorMessage = ref('')
const selectedNode = ref(null)
const projects = ref([])
const structureThreshold = ref(0)
const graphData = ref({
  mode: 'citation',
  scope: 'library',
  nodes: [],
  edges: [],
  stats: {
    nodes: 0,
    edges: 0,
    papers: 0,
    external: 0,
    edge_types: {}
  },
  truncated: false,
  hidden_nodes: 0,
  message: ''
})

const filters = reactive({
  mode: 'citation',
  scope: 'library',
  project: '',
  paperRef: '',
  minShared: 2,
  maxNodes: 80
})

function nodeRoles(node) {
  if (!node) {
    return []
  }
  if (Array.isArray(node.roles) && node.roles.length) {
    return node.roles
  }
  if (node.role) {
    return [node.role]
  }
  if (node.type === 'external') {
    return ['external']
  }
  if (node.type === 'topic') {
    return ['topic']
  }
  return ['paper']
}

function edgeTypeSummary(edges) {
  const summary = {}
  edges.forEach((edge) => {
    if (edge.type === 'structure' && Array.isArray(edge.relations) && edge.relations.length) {
      edge.relations.forEach((relation) => {
        summary[relation] = (summary[relation] || 0) + 1
      })
      return
    }
    const key = edge.type || 'edge'
    summary[key] = (summary[key] || 0) + 1
  })
  return summary
}

function communitySwatch(index, size) {
  if (!index || size <= 1) {
    return '#94a3b8'
  }
  return COMMUNITY_COLORS[(index - 1) % COMMUNITY_COLORS.length]
}

function detectStructureCommunities(nodes, edges) {
  const nodeIds = nodes.map((node) => node.id)
  if (!nodeIds.length) {
    return { nodes: [], communities: [] }
  }

  const adjacency = new Map(nodeIds.map((id) => [id, []]))
  edges.forEach((edge) => {
    const source = typeof edge.source === 'object' ? edge.source.id : edge.source
    const target = typeof edge.target === 'object' ? edge.target.id : edge.target
    if (!adjacency.has(source) || !adjacency.has(target)) {
      return
    }
    const weight = Number(edge.weight || 1)
    adjacency.get(source).push({ id: target, weight })
    adjacency.get(target).push({ id: source, weight })
  })

  const labels = {}
  nodeIds.forEach((id) => {
    labels[id] = id
  })

  const orderedIds = [...nodeIds].sort((a, b) => {
    const degreeDelta = adjacency.get(b).length - adjacency.get(a).length
    if (degreeDelta !== 0) {
      return degreeDelta
    }
    return String(a).localeCompare(String(b))
  })

  for (let step = 0; step < 12; step += 1) {
    let changed = false
    orderedIds.forEach((id) => {
      const neighbors = adjacency.get(id) || []
      if (!neighbors.length) {
        return
      }
      const scores = {}
      neighbors.forEach((neighbor) => {
        const label = labels[neighbor.id]
        scores[label] = (scores[label] || 0) + neighbor.weight
      })
      const winner = Object.entries(scores).sort((a, b) => {
        const scoreDelta = b[1] - a[1]
        if (scoreDelta !== 0) {
          return scoreDelta
        }
        return String(a[0]).localeCompare(String(b[0]))
      })[0]
      if (winner && winner[0] !== labels[id]) {
        labels[id] = winner[0]
        changed = true
      }
    })
    if (!changed) {
      break
    }
  }

  const groups = new Map()
  nodeIds.forEach((id) => {
    const label = labels[id]
    if (!groups.has(label)) {
      groups.set(label, [])
    }
    groups.get(label).push(id)
  })

  const orderedGroups = [...groups.values()].sort((a, b) => {
    const sizeDelta = b.length - a.length
    if (sizeDelta !== 0) {
      return sizeDelta
    }
    return String(a[0]).localeCompare(String(b[0]))
  })

  const idToCommunity = {}
  const communities = orderedGroups.map((members, index) => {
    const communityId = index + 1
    const label = `C${communityId}`
    members.forEach((member) => {
      idToCommunity[member] = {
        id: communityId,
        label,
        size: members.length,
        color: communitySwatch(communityId, members.length)
      }
    })
    return {
      id: communityId,
      label,
      size: members.length,
      color: communitySwatch(communityId, members.length)
    }
  })

  const communityNodes = nodes.map((node) => {
    const community = idToCommunity[node.id]
    return {
      ...node,
      community_id: community ? community.id : null,
      community_label: community ? community.label : '',
      community_size: community ? community.size : 0,
      community_color: community ? community.color : '#94a3b8'
    }
  })

  return { nodes: communityNodes, communities }
}

function buildDisplayPayload(nodes, edges, extra = {}) {
  const paperNodes = nodes.filter((node) => node.type === 'paper').length
  const topicPaperCount = nodes
    .filter((node) => node.type === 'topic')
    .reduce((sum, node) => sum + Number(node.paper_count || 0), 0)

  return {
    nodes,
    edges,
    stats: {
      nodes: nodes.length,
      edges: edges.length,
      papers: topicPaperCount > 0 ? topicPaperCount : paperNodes,
      external: nodes.filter((node) => node.type === 'external').length,
      topics: nodes.filter((node) => node.type === 'topic').length,
      edge_types: edgeTypeSummary(edges)
    },
    communities: extra.communities || [],
    hidden_edges: extra.hiddenEdges || 0
  }
}

const thresholdBounds = computed(() => {
  if (graphData.value.mode !== 'structure') {
    return { min: 0, max: 0, step: 0.5 }
  }
  const rawEdges = Array.isArray(graphData.value.edges) ? graphData.value.edges : []
  let maxWeight = 0
  rawEdges.forEach((edge) => {
    maxWeight = Math.max(maxWeight, Number(edge.weight || 0))
  })
  return {
    min: 0,
    max: Math.max(0, Math.ceil(maxWeight * 2) / 2),
    step: 0.5
  }
})

const thresholdDisplay = computed(() => {
  if (filters.mode !== 'structure') {
    return 'n/a'
  }
  return structureThreshold.value <= 0 ? 'All' : structureThreshold.value.toFixed(1)
})

const displayGraph = computed(() => {
  const rawNodes = Array.isArray(graphData.value.nodes)
    ? graphData.value.nodes.map((node) => ({ ...node }))
    : []
  const rawEdges = Array.isArray(graphData.value.edges)
    ? graphData.value.edges.map((edge) => ({ ...edge }))
    : []

  if (graphData.value.mode !== 'structure') {
    return buildDisplayPayload(rawNodes, rawEdges)
  }

  const threshold = Number(structureThreshold.value || 0)
  const keptEdges = rawEdges.filter((edge) => Number(edge.weight || 0) >= threshold)
  const keepIds = new Set()
  keptEdges.forEach((edge) => {
    keepIds.add(edge.source)
    keepIds.add(edge.target)
  })
  rawNodes.forEach((node) => {
    if (nodeRoles(node).includes('center')) {
      keepIds.add(node.id)
    }
  })

  const keptNodes = rawNodes.filter((node) => keepIds.has(node.id))
  const communityResult = detectStructureCommunities(keptNodes, keptEdges)
  return buildDisplayPayload(communityResult.nodes, keptEdges, {
    communities: communityResult.communities,
    hiddenEdges: Math.max(0, rawEdges.length - keptEdges.length)
  })
})

const nodeCount = computed(() => displayGraph.value.stats.nodes || 0)
const edgeCount = computed(() => displayGraph.value.stats.edges || 0)
const paperCount = computed(() => displayGraph.value.stats.papers || 0)
const externalCount = computed(() => displayGraph.value.stats.external || 0)
const topicCount = computed(() => displayGraph.value.stats.topics || 0)
const communitySummary = computed(() => displayGraph.value.communities || [])
const communityCount = computed(() => communitySummary.value.filter((community) => community.size > 1).length || communitySummary.value.length)
const auxiliaryStatLabel = computed(() => {
  if (filters.mode === 'structure') return 'Communities'
  if (filters.mode === 'topic') return 'Topics'
  return 'External'
})
const auxiliaryStatValue = computed(() => {
  if (filters.mode === 'structure') return communityCount.value
  if (filters.mode === 'topic') return topicCount.value
  return externalCount.value
})

const infoMessage = computed(() => {
  const parts = []
  if (graphData.value.message) {
    parts.push(graphData.value.message)
  }
  if (graphData.value.truncated && graphData.value.hidden_nodes) {
    parts.push(`Hidden ${graphData.value.hidden_nodes} nodes to keep the graph readable.`)
  }
  if (graphData.value.mode === 'structure' && displayGraph.value.hidden_edges) {
    parts.push(`Threshold hides ${displayGraph.value.hidden_edges} weaker edges.`)
  }
  return parts.join(' ')
})

const edgeSummary = computed(() => {
  const edgeTypes = displayGraph.value.stats.edge_types || {}
  const parts = []
  Object.keys(edgeTypes).sort().forEach((key) => {
    parts.push(`${key}: ${edgeTypes[key]}`)
  })
  return parts.length ? parts.join(' · ') : 'No edges'
})

const selectedRoles = computed(() => {
  if (!selectedNode.value) {
    return []
  }
  const roles = selectedNode.value.roles
  if (Array.isArray(roles) && roles.length) {
    return roles
  }
  return selectedNode.value.role ? [selectedNode.value.role] : []
})

function topicSwatch(topicId) {
  if (!Number.isFinite(Number(topicId))) {
    return '#9ca3af'
  }
  return COMMUNITY_COLORS[Math.abs(Number(topicId)) % COMMUNITY_COLORS.length]
}

function nodeColor(node) {
  if (graphData.value.mode === 'structure') {
    return node.community_color || communitySwatch(node.community_id, node.community_size)
  }
  if (graphData.value.mode === 'topic') {
    if (nodeRoles(node).includes('center')) return '#b45309'
    return topicSwatch(node.topic_id)
  }
  const roles = nodeRoles(node)
  if (roles.includes('center')) return '#b91c1c'
  if (node.type === 'external') return '#d97706'
  if (roles.includes('reference')) return '#2563eb'
  if (roles.includes('citer') || roles.includes('shared')) return '#059669'
  return '#475569'
}

function nodeStroke(node) {
  if (nodeRoles(node).includes('center')) {
    return '#7f1d1d'
  }
  return '#ffffff'
}

function nodeStrokeWidth(node) {
  return nodeRoles(node).includes('center') ? 3 : 2
}

function nodeRadius(node) {
  if (graphData.value.mode === 'topic') {
    const count = Number(node.paper_count || 0)
    return Math.max(12, Math.min(26, 12 + Math.sqrt(count || 0) * 2))
  }
  if (nodeRoles(node).includes('center')) return 16
  if (node.type === 'external') return 9
  const cite = Number(node.citation_count || 0)
  return Math.max(8, Math.min(18, 8 + Math.sqrt(cite || 0)))
}

function edgeColor(edge) {
  if (edge.type === 'cites') return '#64748b'
  if (edge.type === 'topic_similarity') return '#b45309'
  const relations = Array.isArray(edge.relations) ? edge.relations : []
  if (relations.includes('direct_citation') && relations.includes('shared_refs')) return '#c2410c'
  if (relations.includes('direct_citation')) return '#2563eb'
  if (relations.includes('shared_refs')) return '#16a34a'
  return '#64748b'
}

function edgeWidth(edge) {
  const weight = Number(edge.weight || 1)
  if (edge.type === 'topic_similarity') {
    return Math.max(1.5, Math.min(5, 1 + weight * 4))
  }
  return Math.max(1.5, Math.min(5, 1 + weight * 0.6))
}

function edgeDash(edge) {
  const relations = Array.isArray(edge.relations) ? edge.relations : []
  if (edge.type === 'structure' && relations.includes('shared_refs') && !relations.includes('direct_citation')) {
    return '5 4'
  }
  return null
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
  selectedNode.value = nodes.find((node) => nodeRoles(node).includes('center')) || nodes[0] || null
}

function resetThreshold() {
  structureThreshold.value = 0
}

async function loadProjects() {
  try {
    const response = await fetch('/api/projects')
    if (!response.ok) {
      throw new Error(`Failed to load projects: ${response.status}`)
    }
    const data = await response.json()
    projects.value = Array.isArray(data) ? data : []
    if (!filters.project && projects.value.length) {
      filters.project = projects.value[0].name
    }
  } catch (error) {
    console.error(error)
  }
}

function buildGraphQuery() {
  const query = new URLSearchParams()
  query.set('mode', filters.mode)
  query.set('scope', filters.scope)
  query.set('max_nodes', String(filters.maxNodes || 80))
  if (filters.mode === 'structure') {
    query.set('min_shared', String(filters.minShared || 2))
  }
  if (filters.scope === 'project' && filters.project) {
    query.set('project', filters.project)
  }
  if (filters.scope === 'paper' && filters.paperRef) {
    query.set('paper_ref', filters.paperRef)
  }
  return query.toString()
}

function normalizeThreshold() {
  if (graphData.value.mode !== 'structure') {
    structureThreshold.value = 0
    return
  }
  if (structureThreshold.value > thresholdBounds.value.max) {
    structureThreshold.value = thresholdBounds.value.max
  }
  if (structureThreshold.value < thresholdBounds.value.min) {
    structureThreshold.value = thresholdBounds.value.min
  }
}

async function buildTopicGraph() {
  if (filters.mode !== 'topic') {
    return
  }
  if (filters.scope === 'project' && !filters.project) {
    errorMessage.value = 'Select a project first.'
    return
  }
  if (filters.scope === 'paper' && !filters.paperRef) {
    errorMessage.value = 'Enter a paper reference first.'
    return
  }

  buildingTopicGraph.value = true
  errorMessage.value = ''
  try {
    const response = await fetch('/api/graph/build', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mode: filters.mode,
        scope: filters.scope,
        project: filters.project,
        paper_ref: filters.paperRef,
        min_shared: filters.minShared,
        max_nodes: filters.maxNodes
      })
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error((data && data.statusMessage) || `Failed to build topic graph (${response.status})`)
    }
    graphData.value = data.graph || graphData.value
    normalizeThreshold()
    syncSelectedNode()
    await nextTick()
    renderGraph()
  } catch (error) {
    errorMessage.value = (error && error.message) || 'Failed to build topic graph'
  } finally {
    buildingTopicGraph.value = false
  }
}

async function loadGraph() {
  if (filters.scope === 'project' && !filters.project) {
    errorMessage.value = 'Select a project first.'
    return
  }
  if (filters.scope === 'paper' && !filters.paperRef) {
    errorMessage.value = 'Enter a paper reference first.'
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const response = await fetch(`/api/graph?${buildGraphQuery()}`)
    const data = await response.json()
    if (!response.ok) {
      throw new Error((data && data.statusMessage) || `Failed to load graph (${response.status})`)
    }
    graphData.value = data || graphData.value
    normalizeThreshold()
    syncSelectedNode()
    await nextTick()
    renderGraph()
  } catch (error) {
    errorMessage.value = (error && error.message) || 'Failed to load graph'
  } finally {
    loading.value = false
  }
}

function renderGraph() {
  if (!graphContainer.value) {
    return
  }

  const nodes = displayGraph.value.nodes.map((node) => ({ ...node }))
  const edges = displayGraph.value.edges.map((edge) => ({ ...edge }))
  const container = graphContainer.value
  container.innerHTML = ''

  if (!nodes.length) {
    return
  }

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
    .force('link', d3.forceLink(edges).id((d) => d.id).distance((d) => d.type === 'cites' ? 120 : 95))
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
    .attr('stroke', (d) => nodeStroke(d))
    .attr('stroke-width', (d) => nodeStrokeWidth(d))

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
  if (!selectedNode.value || !selectedNode.value.paper_ref) {
    return
  }
  navigateTo(`/paper/${encodeURIComponent(selectedNode.value.paper_ref)}`)
}

function openRepresentativePaper(paperRef) {
  if (!paperRef) {
    return
  }
  navigateTo(`/paper/${encodeURIComponent(paperRef)}`)
}

watch(() => filters.scope, (scope) => {
  if (scope === 'project' && !filters.project && projects.value.length) {
    filters.project = projects.value[0].name
  }
})

watch(() => filters.mode, (mode) => {
  if (mode !== 'structure') {
    structureThreshold.value = 0
  }
})

watch(structureThreshold, async () => {
  syncSelectedNode()
  await nextTick()
  renderGraph()
})

onMounted(async () => {
  await loadProjects()
  await loadGraph()
})
</script>
