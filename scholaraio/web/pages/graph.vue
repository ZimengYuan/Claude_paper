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
      图谱页面现在只读取预计算快照，不再支持在线构建 topic model、paper scope 临时查询或重新拉取后端数据。
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
            No graph data available for this snapshot scope.
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
              <span class="mb-1 block">Scope</span>
              <select v-model="filters.scope" class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50">
                <option value="library">Library</option>
                <option value="project">Project</option>
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
const projects = ref([])
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
    topics: 0,
    edge_types: {},
  },
  message: '',
})

const filters = reactive({
  mode: 'citation',
  scope: 'library',
  project: '',
})

const displayGraph = computed(() => graphData.value)
const nodeCount = computed(() => displayGraph.value.stats.nodes || displayGraph.value.nodes.length || 0)
const edgeCount = computed(() => displayGraph.value.stats.edges || displayGraph.value.edges.length || 0)
const paperCount = computed(() => displayGraph.value.stats.papers || 0)
const selectedRoles = computed(() => {
  if (!selectedNode.value) return []
  if (Array.isArray(selectedNode.value.roles) && selectedNode.value.roles.length) return selectedNode.value.roles
  if (selectedNode.value.role) return [selectedNode.value.role]
  return []
})
const infoMessage = computed(() => displayGraph.value.message || '')
const edgeSummary = computed(() => {
  const edgeTypes = displayGraph.value.stats.edge_types || {}
  const entries = Object.entries(edgeTypes)
  if (entries.length === 0) return 'No visible edges'
  return entries.map(([type, count]) => `${type}: ${count}`).join(' · ')
})
const auxiliaryStatLabel = computed(() => displayGraph.value.mode === 'topic' ? 'Topics' : 'External')
const auxiliaryStatValue = computed(() => {
  if (displayGraph.value.mode === 'topic') return displayGraph.value.stats.topics || 0
  return displayGraph.value.stats.external || 0
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

async function loadGraphManifest() {
  const data = await fetchJson('graphs/index.json')
  graphManifest.value = data
  projects.value = Array.isArray(data?.projects)
    ? data.projects.map((project) => ({
        name: project.name,
        slug: project.slug,
        paper_count: project.paper_count,
      }))
    : []

  if (!filters.project && projects.value.length) {
    filters.project = projects.value[0].name
  }
}

function resolveGraphPath() {
  if (!graphManifest.value) return ''
  if (filters.scope === 'library') {
    return graphManifest.value.library?.[filters.mode] || ''
  }

  const match = (graphManifest.value.projects || []).find((project) => project.name === filters.project)
  return match?.files?.[filters.mode] || ''
}

async function loadGraph() {
  const relativePath = resolveGraphPath()
  if (!relativePath) {
    graphData.value = {
      mode: filters.mode,
      scope: filters.scope,
      nodes: [],
      edges: [],
      stats: { nodes: 0, edges: 0, papers: 0, external: 0, topics: 0, edge_types: {} },
      message: filters.scope === 'project' ? 'Select a project to view its graph snapshot.' : 'Graph snapshot not available.',
    }
    return
  }

  loading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchJson(relativePath)
    graphData.value = data
    syncSelectedNode()
    await nextTick()
    renderGraph()
  } catch (error) {
    console.error('Failed to load graph snapshot:', error)
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

watch(() => filters.scope, (scope) => {
  if (scope === 'project' && !filters.project && projects.value.length) {
    filters.project = projects.value[0].name
  }
})

watch(() => [filters.mode, filters.scope, filters.project], async () => {
  if (filters.scope === 'project' && !filters.project) return
  await loadGraph()
}, { deep: true })

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
