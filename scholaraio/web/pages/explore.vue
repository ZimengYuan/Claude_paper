<template>
  <div class="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
    <section class="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-blue-900 px-6 py-8 text-white sm:px-8">
        <p class="text-xs font-semibold uppercase tracking-[0.28em] text-slate-300">Explore</p>
        <div class="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div class="max-w-3xl">
            <h1 class="text-3xl font-semibold tracking-tight">Library Trend Desk</h1>
            <p class="mt-3 text-sm leading-6 text-slate-200">
              直接基于你当前本地文献库 `data/papers` 和主 `topic_model` 做趋势分析，帮助你看清这批论文覆盖了哪些年份、哪些代表作最值得先读，以及当前是否已经具备 roadmap 生成条件。
            </p>
          </div>
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur">
              <div class="text-xs uppercase tracking-wide text-slate-300">Scopes</div>
              <div class="mt-2 text-2xl font-semibold">{{ filteredLibraries.length }}</div>
            </div>
            <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur">
              <div class="text-xs uppercase tracking-wide text-slate-300">Selected</div>
              <div class="mt-2 truncate text-sm font-medium">{{ selectedLibrary?.title || selectedLibrary?.name || 'None' }}</div>
            </div>
            <div class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur">
              <div class="text-xs uppercase tracking-wide text-slate-300">Roadmap</div>
              <div class="mt-2 text-sm font-medium">{{ roadmapStatusLabel }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="errorMessage" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorMessage }}
    </div>

    <div v-if="notice" class="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
      {{ notice }}
    </div>

    <div class="grid gap-6 xl:grid-cols-[340px,minmax(0,1fr)]">
      <aside class="space-y-4">
        <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div class="flex items-center justify-between gap-3">
            <div>
              <h2 class="text-sm font-semibold text-slate-900">Analysis Scope</h2>
              <p class="mt-1 text-xs text-slate-500">当前仅分析本地主库，不再读取外部数据库</p>
            </div>
            <button class="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 hover:bg-slate-50" @click="loadLibraries(selectedName)">
              Refresh
            </button>
          </div>

          <div class="mt-4 space-y-3">
            <input
              v-model="libraryQuery"
              type="text"
              placeholder="Search scope..."
              class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
            />
            <div class="flex items-center justify-between text-xs text-slate-500">
              <span>{{ filteredLibraries.length }} scope{{ filteredLibraries.length === 1 ? '' : 's' }}</span>
              <span>{{ loadingLibraries ? 'Syncing...' : 'Ready' }}</span>
            </div>
          </div>

          <div v-if="loadingLibraries" class="py-10 text-center text-sm text-slate-500">Loading current library analysis...</div>
          <div v-else-if="filteredLibraries.length === 0" class="py-10 text-center text-sm text-slate-500">Current library analysis is unavailable.</div>
          <div v-else class="mt-4 space-y-3">
            <button
              v-for="library in filteredLibraries"
              :key="library.name"
              class="w-full rounded-2xl border p-4 text-left transition"
              :class="selectedName === library.name ? 'border-blue-300 bg-blue-50 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'"
              @click="selectLibrary(library.name)"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="truncate font-medium text-slate-900">{{ library.title || library.name }}</div>
                  <div class="mt-1 text-xs text-slate-500">{{ formatCount(library.count) }} papers</div>
                </div>
                <span class="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-slate-600">
                  {{ relativeTime(library.fetched_at) }}
                </span>
              </div>
              <p class="mt-2 line-clamp-2 text-xs leading-5 text-slate-600">{{ describeQuery(library.query) }}</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span class="rounded-full px-2 py-1 text-[10px] font-medium" :class="library.has_topics ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'">
                  {{ library.has_topics ? 'Topics ready' : 'No topics' }}
                </span>
                <span class="rounded-full px-2 py-1 text-[10px] font-medium" :class="library.roadmap_exists ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'">
                  {{ library.roadmap_exists ? 'Roadmap cached' : 'Roadmap empty' }}
                </span>
                <span v-if="library.has_semantic_index" class="rounded-full bg-violet-100 px-2 py-1 text-[10px] font-medium text-violet-700">Semantic index</span>
              </div>
            </button>
          </div>
        </section>
      </aside>

      <div class="space-y-4">
        <div v-if="detailLoading" class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">
          Loading {{ selectedName }}...
        </div>

        <template v-if="selectedLibrary">
          <!-- Overview header -->
          <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div class="max-w-3xl">
                <div class="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                  <span class="rounded-full bg-slate-100 px-2.5 py-1">{{ selectedLibrary.source || 'local-library' }}</span>
                  <span>Fetched {{ formatDateTime(selectedLibrary.fetched_at) }}</span>
                </div>
                <h2 class="mt-3 text-2xl font-semibold tracking-tight text-slate-900">{{ selectedLibrary.title || selectedLibrary.name }}</h2>
                <p class="mt-2 text-sm leading-6 text-slate-600">
                  这个页面当前直接分析 {{ describeQuery(selectedLibrary.query) }} 对应的主库范围。下面的统计、主题和代表论文都来自本地 `data/papers/` 与主 `data/topic_model/`，不再依赖外部 explore 数据。
                </p>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                <div class="text-xs uppercase tracking-wide text-slate-500">Current Scope</div>
                <div class="mt-2 font-medium">{{ formatCount(selectedLibrary.count) }} papers</div>
              </div>
            </div>

            <div v-if="queryEntries.length" class="mt-4 flex flex-wrap gap-2 border-t border-slate-200 pt-4">
              <span v-for="entry in queryEntries" :key="entry.key" class="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700">
                {{ entry.key }}: {{ entry.value }}
              </span>
            </div>

            <div class="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <article v-for="card in overviewCards" :key="card.label" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div class="text-xs uppercase tracking-wide text-slate-500">{{ card.label }}</div>
                <div class="mt-2 text-2xl font-semibold text-slate-900">{{ card.value }}</div>
                <p class="mt-2 text-xs leading-5 text-slate-500">{{ card.help }}</p>
              </article>
            </div>
          </section>

          <!-- Main tabbed content -->
          <section class="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div class="flex border-b border-slate-200">
              <button
                v-for="tab in exploreTabs"
                :key="tab.key"
                class="relative px-5 py-3 text-sm font-medium transition-colors"
                :class="exploreTab === tab.key
                  ? 'text-blue-600 after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-blue-600'
                  : 'text-slate-500 hover:text-slate-700'"
                @click="exploreTab = tab.key"
              >
                {{ tab.label }}
              </button>
            </div>

            <div class="p-5 sm:p-6">
              <!-- Tab: Trends -->
              <div v-if="exploreTab === 'trends'">
                <div class="grid gap-4 xl:grid-cols-[minmax(0,1.3fr),minmax(0,0.7fr)]">
                  <div>
                    <h3 class="text-base font-semibold text-slate-900">Trend Highlights</h3>
                    <p class="mt-1 text-xs text-slate-500">先用统计视角判断这个方向更偏前沿快照，还是已经形成相对稳定的文献结构</p>

                    <div v-if="trendHighlights.length" class="mt-4 space-y-3">
                      <div v-for="highlight in trendHighlights" :key="highlight" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-700">
                        {{ highlight }}
                      </div>
                    </div>
                    <div v-else class="mt-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-500">
                      当前主库还没有足够的统计信息可供总结。
                    </div>

                    <div class="mt-6 grid gap-5 lg:grid-cols-2">
                      <div class="rounded-2xl border border-slate-200 p-4">
                        <div class="flex items-center justify-between gap-2">
                          <h4 class="text-sm font-semibold text-slate-900">Year Distribution</h4>
                          <span class="text-xs text-slate-500">last {{ yearDistribution.length }} buckets</span>
                        </div>
                        <div v-if="yearDistribution.length" class="mt-4 space-y-3">
                          <div v-for="item in yearDistribution" :key="item.year" class="space-y-1.5">
                            <div class="flex items-center justify-between text-xs text-slate-500">
                              <span>{{ item.year }}</span>
                              <span>{{ formatCount(item.count) }}</span>
                            </div>
                            <div class="h-2 overflow-hidden rounded-full bg-slate-100">
                              <div class="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400" :style="{ width: item.width }"></div>
                            </div>
                          </div>
                        </div>
                        <div v-else class="mt-4 text-sm text-slate-500">No year distribution available.</div>
                      </div>

                      <div class="space-y-5">
                        <div class="rounded-2xl border border-slate-200 p-4">
                          <h4 class="text-sm font-semibold text-slate-900">Top Authors</h4>
                          <div v-if="topAuthors.length" class="mt-3 space-y-2">
                            <div v-for="author in topAuthors" :key="author.name" class="flex items-center justify-between gap-3 text-sm">
                              <span class="min-w-0 truncate text-slate-700">{{ author.name }}</span>
                              <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{{ author.count }}</span>
                            </div>
                          </div>
                          <div v-else class="mt-3 text-sm text-slate-500">No author aggregate available.</div>
                        </div>

                        <div class="rounded-2xl border border-slate-200 p-4">
                          <h4 class="text-sm font-semibold text-slate-900">Top Journals & Venues</h4>
                          <div v-if="topJournals.length" class="mt-3 space-y-3">
                            <div v-for="item in topJournals" :key="item.name" class="space-y-1.5">
                              <div class="flex items-center justify-between text-xs text-slate-500">
                                <span>{{ item.name }}</span>
                                <span>{{ formatPercent(item.share) }}</span>
                              </div>
                              <div class="h-2 overflow-hidden rounded-full bg-slate-100">
                                <div class="h-full rounded-full bg-slate-700" :style="{ width: percentWidth(item.share) }"></div>
                              </div>
                            </div>
                          </div>
                          <div v-else class="mt-3 text-sm text-slate-500">No venue distribution available.</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <div class="flex items-center justify-between gap-3">
                      <h3 class="text-base font-semibold text-slate-900">Topic Readiness</h3>
                      <span class="rounded-full px-3 py-1 text-xs font-medium" :class="selectedLibrary.has_topics ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'">
                        {{ selectedLibrary.has_topics ? 'Topics available' : 'Topics missing' }}
                      </span>
                    </div>
                    <p class="mt-1 text-xs text-slate-500">roadmap 依赖 topic model，因此这里先判断“主题结构是否就绪”</p>

                    <div v-if="topicOverview.length" class="mt-4">
                      <!-- Per-topic tabs -->
                      <div class="flex flex-wrap gap-1 border-b border-slate-200 pb-1">
                        <button
                          v-for="topic in topicOverview"
                          :key="topic.topic_id"
                          class="rounded-t-lg px-3 py-1.5 text-xs font-medium transition-colors"
                          :class="activeTopicId === topic.topic_id
                            ? 'bg-slate-100 text-slate-900'
                            : 'text-slate-500 hover:text-slate-700'"
                          @click="activeTopicId = topic.topic_id"
                        >
                          {{ topic.name || ('Topic ' + topic.topic_id) }}
                        </button>
                      </div>
                      <!-- Active topic detail -->
                      <div v-if="activeTopic" class="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <div class="flex items-start justify-between gap-3">
                          <div>
                            <h4 class="text-sm font-semibold text-slate-900">{{ activeTopic.name || ('Topic ' + activeTopic.topic_id) }}</h4>
                            <p class="mt-1 text-xs text-slate-500">{{ formatCount(activeTopic.count) }} papers</p>
                          </div>
                          <span class="rounded-full bg-white px-2 py-1 text-[10px] font-medium text-slate-600">Topic {{ activeTopic.topic_id }}</span>
                        </div>
                        <div v-if="activeTopic.keywords?.length" class="mt-3 flex flex-wrap gap-2">
                          <span v-for="keyword in activeTopic.keywords.slice(0, 8)" :key="keyword" class="rounded-full bg-white px-2.5 py-1 text-[11px] text-slate-700">
                            {{ keyword }}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div v-else class="mt-4 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm leading-6 text-slate-600">
                      当前主库还没有 topic model。
                    </div>
                  </div>
                </div>
              </div>

              <!-- Tab: Papers -->
              <div v-if="exploreTab === 'papers'">
                <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                  <div>
                    <h3 class="text-base font-semibold text-slate-900">Representative Papers</h3>
                    <p class="mt-1 text-xs text-slate-500">从“高引用代表作”和“近年论文”两个视角观察当前主库的技术重心</p>
                  </div>
                  <div class="inline-flex rounded-full border border-slate-200 bg-slate-50 p-1 text-sm">
                    <button class="rounded-full px-4 py-2 transition" :class="paperView === 'top' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'" @click="paperView = 'top'">
                      Top Cited
                    </button>
                    <button class="rounded-full px-4 py-2 transition" :class="paperView === 'recent' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'" @click="paperView = 'recent'">
                      Recent Papers
                    </button>
                  </div>
                </div>

                <div v-if="displayedResults.length === 0" class="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500">
                  No representative papers to show.
                </div>
                <div v-else class="mt-6 grid gap-4 md:grid-cols-2">
                  <article v-for="(paper, index) in displayedResults" :key="paper.paper_ref || paper.title || index" class="flex h-full flex-col rounded-2xl border border-slate-200 bg-slate-50 p-4 transition hover:-translate-y-0.5 hover:shadow-md">
                    <div class="flex items-start justify-between gap-3">
                      <div class="min-w-0">
                        <div class="text-[11px] font-semibold uppercase tracking-wide text-slate-400">#{{ index + 1 }} · {{ paperView === 'top' ? 'citation leader' : 'recent sample' }}</div>
                        <h4 class="mt-2 line-clamp-2 text-base font-semibold text-slate-900">{{ paper.title }}</h4>
                      </div>
                      <span class="shrink-0 rounded-full bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700">
                        {{ formatCount(paper.cited_by_count || 0) }} cites
                      </span>
                    </div>

                    <p class="mt-3 line-clamp-2 text-sm text-slate-600">{{ paper.authors?.join(', ') || 'Unknown author' }}</p>
                    <div class="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                      <span class="rounded-full bg-white px-2.5 py-1">{{ paper.year || '?' }}</span>
                      <span class="rounded-full bg-white px-2.5 py-1">{{ paper.type || 'article' }}</span>
                    </div>
                    <p v-if="paper.abstract" class="mt-4 line-clamp-4 text-sm leading-6 text-slate-600">{{ paper.abstract }}</p>
                    <div class="mt-4 flex items-center justify-between gap-3 pt-4">
                      <div class="min-w-0 text-[11px] text-slate-400">
                        <div v-if="paper.doi" class="truncate">{{ paper.doi }}</div>
                        <div v-else class="truncate">{{ paper.paper_id || paper.dir_name || 'No local ref' }}</div>
                      </div>
                      <div class="flex flex-wrap gap-2">
                        <button class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-white" @click.stop="openPaperRef(paper.paper_ref)">
                          Open Paper
                        </button>
                        <a v-if="paper.doi" :href="`https://doi.org/${paper.doi}`" target="_blank" rel="noreferrer" class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-white">
                          DOI
                        </a>
                      </div>
                    </div>
                  </article>
                </div>
              </div>

              <!-- Tab: Roadmap -->
              <div v-if="exploreTab === 'roadmap'">
                <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <h3 class="text-lg font-semibold text-slate-900">Library Evolution & Future Trends</h3>
                    <p class="mt-1 text-xs leading-5 text-slate-500">roadmap 会基于当前主库的 topic model，把整批本地论文聚成几个宏观方向，再生成技术演进和未来预测。</p>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <button
                      class="rounded-full px-4 py-2 text-sm font-medium transition"
                      :class="canGenerateRoadmap ? 'bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-400' : 'bg-slate-100 text-slate-400 cursor-not-allowed'"
                      :disabled="roadmapLoading || !canGenerateRoadmap"
                      @click="generateRoadmap()"
                    >
                      {{ roadmapLoading ? 'Generating...' : (roadmap ? 'Refresh Roadmap' : 'Generate Roadmap') }}
                    </button>
                    <button v-if="roadmap && !roadmapLoading" class="rounded-full border border-slate-200 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50" @click="generateRoadmap(true)">
                      Force Regenerate
                    </button>
                  </div>
                </div>

                <div v-if="!canGenerateRoadmap" class="mt-5 rounded-2xl border border-dashed border-amber-300 bg-amber-50 px-4 py-5 text-sm leading-6 text-amber-800">
                  当前主库还没有 topic model，roadmap 暂时不可生成。等主 topic model 建好以后，这里会输出“阶段划分、关键方法、关键论文和未来趋势”。
                </div>
                <div v-else-if="roadmapLoading" class="mt-6 flex flex-col items-center rounded-2xl border border-slate-200 bg-slate-50 px-4 py-12 text-center">
                  <div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600"></div>
                  <p class="mt-4 text-sm leading-6 text-slate-500">
                    Analyzing {{ formatCount(selectedLibrary.count) }} local papers across main-library topics.<br>
                    This may take 1-2 minutes depending on topic size and model latency.
                  </p>
                </div>
                <div v-else-if="roadmap" class="mt-6">
                  <!-- Per-direction tabs -->
                  <div v-if="roadmapSections.length > 1" class="flex flex-wrap gap-1 border-b border-slate-200 pb-1">
                    <button
                      v-for="(section, idx) in roadmapSections"
                      :key="idx"
                      class="rounded-t-lg px-3 py-1.5 text-xs font-medium transition-colors"
                      :class="activeRoadmapSection === idx
                        ? 'bg-slate-100 text-slate-900'
                        : 'text-slate-500 hover:text-slate-700'"
                      @click="activeRoadmapSection = idx"
                    >
                      {{ section.title }}
                    </button>
                  </div>
                  <div class="roadmap-content prose prose-slate mt-4 max-w-none" @click="handleRoadmapClick" v-html="activeRoadmapHtml"></div>
                </div>
                <div v-else class="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-sm leading-6 text-slate-600">
                  roadmap 还没有生成。你现在可以先通过趋势摘要、主题结构和代表论文判断当前主库的技术重心。
                </div>
              </div>
            </div>
          </section>
        </template>

        <section v-if="selectedLibrary === null && loadingLibraries === false" class="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500 shadow-sm">
          Current library analysis will appear here once the local snapshot is loaded.
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'

const router = useRouter()

const libraries = ref([])
const selectedName = ref('')
const selectedLibrary = ref(null)
const libraryQuery = ref('')
const loadingLibraries = ref(true)
const detailLoading = ref(false)
const roadmapLoading = ref(false)
const roadmap = ref('')
const notice = ref('')
const errorMessage = ref('')
const paperView = ref('top')
const exploreTab = ref('trends')
const activeTopicId = ref(null)

const exploreTabs = [
  { key: 'trends', label: 'Trends & Topics' },
  { key: 'papers', label: 'Papers' },
  { key: 'roadmap', label: 'Roadmap' },
]

const activeTopic = computed(() => {
  if (activeTopicId.value == null && topicOverview.value.length > 0) {
    return topicOverview.value[0]
  }
  return topicOverview.value.find(t => t.topic_id === activeTopicId.value) || null
})

const filteredLibraries = computed(() => {
  const query = libraryQuery.value.trim().toLowerCase()
  return libraries.value.filter((library) => {
    if (query === '') return true
    const haystack = [library.title || '', library.name, describeQuery(library.query)].join(' ').toLowerCase()
    return haystack.includes(query)
  })
})

const queryEntries = computed(() => {
  return Object.entries(selectedLibrary.value?.query || {})
    .filter(([, value]) => value != null && String(value).trim() !== '')
    .map(([key, value]) => ({ key, value }))
})

const trendOverview = computed(() => selectedLibrary.value?.trend_overview || {})
const topicOverview = computed(() => selectedLibrary.value?.topic_overview || [])
const topAuthors = computed(() => trendOverview.value.top_authors || [])
const topJournals = computed(() => trendOverview.value.top_journals || [])
const trendHighlights = computed(() => trendOverview.value.trend_highlights || [])
const topPapers = computed(() => selectedLibrary.value?.papers_sample || [])
const recentPapers = computed(() => trendOverview.value.recent_papers_sample || [])
const displayedResults = computed(() => paperView.value === 'recent' ? recentPapers.value : topPapers.value)
const canGenerateRoadmap = computed(() => Boolean(selectedLibrary.value?.has_topics))

const yearDistribution = computed(() => {
  const rows = trendOverview.value.year_distribution || []
  const maxCount = Math.max(1, ...rows.map((item) => Number(item.count || 0)))
  return rows.map((item) => ({
    ...item,
    width: `${Math.max(6, Math.round((Number(item.count || 0) / maxCount) * 100))}%`
  }))
})

const overviewCards = computed(() => {
  const yearSummary = trendOverview.value.year_summary || {}
  const citationSummary = trendOverview.value.citation_summary || {}
  const yearLabel = yearSummary.earliest && yearSummary.latest
    ? (yearSummary.earliest === yearSummary.latest ? String(yearSummary.latest) : `${yearSummary.earliest}-${yearSummary.latest}`)
    : 'n/a'
  const recentLabel = yearSummary.recent_window_start
    ? `${formatPercent(yearSummary.recent_share || 0)} since ${yearSummary.recent_window_start}`
    : 'n/a'
  const citationLabel = citationSummary.average != null ? `${citationSummary.average.toFixed(1)} avg` : 'n/a'
  const citedCoverage = citationSummary.with_citations_share != null ? formatPercent(citationSummary.with_citations_share) : 'n/a'

  return [
    { label: 'Total Papers', value: formatCount(selectedLibrary.value?.count || 0), help: '当前本地主库已收录的全部论文数量。' },
    { label: 'Year Span', value: yearLabel, help: '观察当前主库更偏长期积累，还是最近集中收录。' },
    { label: 'Recent Density', value: recentLabel, help: '最近 3 年的论文占比，越高说明主库更偏当前前沿动态。' },
    { label: 'Citation Coverage', value: `${citationLabel} · ${citedCoverage}`, help: '同时看主库的平均引用和有引用记录的覆盖率。' }
  ]
})

const roadmapStatusLabel = computed(() => {
  if (roadmapLoading.value) return 'Generating'
  if (roadmap.value) return 'Loaded'
  if (selectedLibrary.value?.has_topics) return 'Ready to generate'
  return 'Needs topics'
})

const normalizedRoadmap = computed(() => normalizeRoadmapMarkdown(roadmap.value))
const activeRoadmapSection = ref(0)

const roadmapSections = computed(() => {
  const source = normalizedRoadmap.value
  if (!source) return []
  const parts = source.split(/^## /m)
  const intro = parts[0].trim()
  const sections = []
  if (intro && !parts[1]) {
    sections.push({ title: 'Overview', body: intro })
    return sections
  }
  for (let i = 1; i < parts.length; i++) {
    const chunk = parts[i]
    const newlineIdx = chunk.indexOf('\n')
    const title = newlineIdx >= 0 ? chunk.slice(0, newlineIdx).replace(/---\s*$/, '').trim() : chunk.trim()
    const body = newlineIdx >= 0 ? chunk.slice(newlineIdx + 1).replace(/\n---\s*$/, '').trim() : ''
    if (title) sections.push({ title, body: body || '' })
  }
  if (intro && sections.length) {
    sections.unshift({ title: 'Overview', body: intro })
  }
  return sections
})

function renderRoadmapHtml(md) {
  if (!md) return ''
  const html = marked.parse(md, { gfm: true, breaks: true })
  return html.replace(/<a href="paper_id:([^"]+)">([^<]+)<\/a>/g, (match, id, text) => {
    return `<span class="paper-link cursor-pointer text-blue-600 hover:underline font-medium" data-paper-id="${id}">${text}</span>`
  })
}

const activeRoadmapHtml = computed(() => {
  const section = roadmapSections.value[activeRoadmapSection.value]
  if (!section) return ''
  return renderRoadmapHtml(section.body)
})

function formatCount(value) {
  return new Intl.NumberFormat('en-US').format(Number(value || 0))
}

function formatPercent(value) {
  const ratio = Number(value || 0)
  if (!Number.isFinite(ratio)) return '0%'
  return `${(ratio * 100).toFixed(ratio > 0 && ratio < 0.1 ? 1 : 0)}%`
}

function percentWidth(value) {
  const ratio = Number(value || 0)
  return `${Math.max(6, Math.round(ratio * 100))}%`
}

function formatDateTime(value) {
  if (!value) return 'unknown time'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString()
}

function relativeTime(value) {
  if (!value) return 'unknown'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  const diffHours = Math.round((Date.now() - date.getTime()) / (1000 * 60 * 60))
  if (Math.abs(diffHours) < 24) return `${Math.abs(diffHours)}h ago`
  const diffDays = Math.round(diffHours / 24)
  if (Math.abs(diffDays) < 30) return `${Math.abs(diffDays)}d ago`
  return date.toLocaleDateString()
}

function describeQuery(query) {
  const entries = Object.entries(query || {}).filter(([, value]) => value != null && String(value).trim() !== '')
  if (entries.length === 0) return 'no query metadata saved'
  return entries.map(([key, value]) => `${key}: ${value}`).join(' · ')
}

function normalizeRoadmapMarkdown(value) {
  const source = String(value || '').replace(/\r\n/g, '\n').trim()
  if (source === '') return ''

  return source
    .replace(/^生成失败:\s*(.+)$/gm, '> 当前方向生成失败：$1')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function resolvePaperLink(paperRef) {
  const value = String(paperRef || '').trim()
  if (value === '') return ''
  if (/^10\./.test(value)) return `https://doi.org/${value}`
  if (/^https?:\/\//.test(value)) return value
  return `/paper/${encodeURIComponent(value)}`
}

function openPaperRef(paperRef) {
  const target = resolvePaperLink(paperRef)
  if (!target) return
  if (target.startsWith('/paper/')) {
    router.push(target)
    return
  }
  window.open(target, '_blank', 'noopener,noreferrer')
}

function handleRoadmapClick(event) {
  const target = event.target
  if (target.classList.contains('paper-link')) {
    const paperId = target.getAttribute('data-paper-id')
    openPaperRef(paperId)
  }
}

async function generateRoadmap(force = false) {
  if (!selectedName.value || !canGenerateRoadmap.value) return
  roadmapLoading.value = true
  errorMessage.value = ''
  notice.value = ''
  try {
    const response = await fetch(`/api/explore/${encodeURIComponent(selectedName.value)}/roadmap`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force })
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data?.statusMessage || 'Failed to generate library roadmap')
    roadmap.value = data.roadmap || ''
    notice.value = data.cached ? 'Loaded cached roadmap.' : 'Roadmap generated from the current topic model.'
  } catch (error) {
    errorMessage.value = error?.message || 'Failed to generate library roadmap'
  } finally {
    roadmapLoading.value = false
  }
}

async function loadLibraries(preferredName = '') {
  loadingLibraries.value = true
  errorMessage.value = ''
  try {
    const response = await fetch('/api/explore')
    if (response.ok === false) {
      throw new Error(`Failed to load current library snapshot (${response.status})`)
    }
    const data = await response.json()
    libraries.value = Array.isArray(data) ? data : []
    const target = preferredName || selectedName.value || libraries.value[0]?.name || ''
    if (target === '') {
      selectedName.value = ''
      selectedLibrary.value = null
      roadmap.value = ''
    } else {
      await selectLibrary(target)
    }
  } catch (error) {
    errorMessage.value = error?.message || 'Failed to load current library snapshot'
  } finally {
    loadingLibraries.value = false
  }
}

async function selectLibrary(name) {
  if (name === '') {
    selectedName.value = ''
    selectedLibrary.value = null
    roadmap.value = ''
    return
  }
  selectedName.value = name
  selectedLibrary.value = null
  roadmap.value = ''
  activeRoadmapSection.value = 0
  paperView.value = 'top'
  detailLoading.value = true
  errorMessage.value = ''
  notice.value = ''
  try {
    const response = await fetch(`/api/explore/${encodeURIComponent(name)}`)
    const data = await response.json()
    if (response.ok === false) {
      throw new Error(data?.statusMessage || `Failed to load ${name}`)
    }
    selectedLibrary.value = data

    if (data.roadmap_exists && data.has_topics) {
      const roadmapResp = await fetch(`/api/explore/${encodeURIComponent(name)}/roadmap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force: false })
      })
      if (roadmapResp.ok) {
        const roadmapData = await roadmapResp.json()
        roadmap.value = roadmapData.roadmap || ''
        if (roadmap.value) {
          notice.value = 'Loaded cached roadmap for the current library.'
        }
      }
    }
  } catch (error) {
    errorMessage.value = error?.message || 'Failed to load library analysis'
  } finally {
    detailLoading.value = false
  }
}

onMounted(async () => {
  await loadLibraries()
})
</script>

<style scoped>
.roadmap-content {
  color: #334155;
  line-height: 1.85;
}

.roadmap-content :deep(h1) {
  margin: 0 0 1rem;
  font-size: 1.875rem;
  line-height: 2.25rem;
  font-weight: 700;
  color: #0f172a;
}

.roadmap-content :deep(h2) {
  margin: 2rem 0 0.9rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 1.5rem;
  line-height: 2rem;
  font-weight: 700;
  color: #0f172a;
}

.roadmap-content :deep(h3) {
  margin: 1.5rem 0 0.75rem;
  font-size: 1.2rem;
  line-height: 1.8rem;
  font-weight: 700;
  color: #0f172a;
}

.roadmap-content :deep(h4) {
  margin: 1rem 0 0.5rem;
  font-size: 1rem;
  line-height: 1.6rem;
  font-weight: 700;
  color: #1e293b;
}

.roadmap-content :deep(p) {
  margin: 0.85rem 0;
}

.roadmap-content :deep(ul),
.roadmap-content :deep(ol) {
  margin: 0.85rem 0;
  padding-left: 1.5rem;
}

.roadmap-content :deep(li) {
  margin: 0.35rem 0;
}

.roadmap-content :deep(hr) {
  margin: 2rem 0;
  border: 0;
  border-top: 1px solid #cbd5e1;
}

.roadmap-content :deep(strong) {
  font-weight: 700;
  color: #0f172a;
}

.roadmap-content :deep(blockquote) {
  margin: 1rem 0;
  border-left: 3px solid #cbd5e1;
  padding-left: 1rem;
  color: #475569;
}

.roadmap-content :deep(code) {
  border-radius: 0.35rem;
  background: #e2e8f0;
  padding: 0.1rem 0.35rem;
  font-size: 0.92em;
  color: #0f172a;
}

.roadmap-content :deep(.paper-link) {
  color: #2563eb;
}

.roadmap-content :deep(pre) {
  overflow-x: auto;
  border-radius: 1rem;
  background: #0f172a;
  color: #e2e8f0;
  padding: 1rem;
}

.roadmap-content :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}

.roadmap-content :deep(table) {
  width: 100%;
  margin: 1.25rem 0;
  border-collapse: collapse;
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
}

.roadmap-content :deep(thead) {
  background: #f8fafc;
}

.roadmap-content :deep(th),
.roadmap-content :deep(td) {
  border-bottom: 1px solid #e2e8f0;
  padding: 0.8rem 0.9rem;
  text-align: left;
  vertical-align: top;
}

.roadmap-content :deep(th) {
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #0f172a;
}

.roadmap-content :deep(td) {
  font-size: 0.94rem;
  color: #334155;
}

.roadmap-content :deep(tbody tr:last-child td) {
  border-bottom: 0;
}

.roadmap-content :deep(a) {
  color: #2563eb;
  font-weight: 600;
  text-decoration: none;
}

.roadmap-content :deep(a:hover) {
  text-decoration: underline;
}
</style>
