<template>
  <div class="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
    <section class="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div class="bg-gradient-to-r from-slate-900 via-slate-800 to-blue-900 px-6 py-8 text-white sm:px-8">
        <p class="text-xs font-semibold uppercase tracking-[0.28em] text-slate-300">Explore</p>
        <div class="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div class="max-w-3xl">
            <h1 class="text-3xl font-semibold tracking-tight">Library Trend Desk</h1>
            <p class="mt-3 text-sm leading-6 text-slate-200">用于快速查看论文库结构、趋势与优先阅读建议。</p>
          </div>
          <div class="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:min-w-[520px]">
            <div v-for="card in heroMetricCards" :key="card.label" class="rounded-2xl border border-white/10 bg-white/10 px-4 py-3 backdrop-blur">
              <div class="text-xs uppercase tracking-wide text-slate-300">{{ card.label }}</div>
              <div class="mt-2 text-2xl font-semibold">{{ card.value }}</div>
              <p class="mt-1 text-[11px] text-slate-300">{{ card.help }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      GitHub Pages 版本只展示已导出的分析结果，不再支持实时刷新、重新聚类或在线生成 roadmap。
    </div>

    <div v-if="loading" class="rounded-2xl border border-slate-200 bg-white px-4 py-10 text-center text-sm text-slate-500 shadow-sm">
      Loading library analysis snapshot...
    </div>

    <div v-else-if="errorMessage" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorMessage }}
    </div>

    <template v-else-if="selectedLibrary">
      <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div class="max-w-3xl">
            <div class="flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <span class="rounded-full bg-slate-100 px-2.5 py-1">{{ selectedLibrary.source || 'local-library' }}</span>
              <span>Fetched {{ formatDateTime(selectedLibrary.fetched_at) }}</span>
            </div>
            <h2 class="mt-3 text-2xl font-semibold tracking-tight text-slate-900">{{ selectedLibrary.title || selectedLibrary.name }}</h2>
            <p class="mt-2 text-sm leading-6 text-slate-600">可在本页直接查看统计、趋势与代表论文。</p>
          </div>
          <div class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
            <div class="text-xs uppercase tracking-wide text-slate-500">Current Scope</div>
            <div class="mt-2 font-medium">{{ formatCount(libraryPapers.length || selectedLibrary.count) }} full-library papers</div>
            <p class="mt-1 text-xs text-slate-500">{{ formatCount(materialStats.ready) }} material-ready cards</p>
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
          <div v-if="exploreTab === 'trends'">
            <div class="mb-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <article class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div class="text-xs uppercase tracking-wide text-slate-500">Read Progress</div>
                <div class="mt-2 text-2xl font-semibold text-slate-900">{{ formatPercent(readStats.readRate) }}</div>
                <p class="mt-1 text-xs text-slate-500">{{ formatCount(readStats.read) }} read / {{ formatCount(readStats.total) }} full library</p>
              </article>
              <article class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div class="text-xs uppercase tracking-wide text-slate-500">Backlog</div>
                <div class="mt-2 text-2xl font-semibold text-slate-900">{{ formatCount(readStats.unread) }}</div>
                <p class="mt-1 text-xs text-slate-500">unread papers</p>
              </article>
              <article class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div class="text-xs uppercase tracking-wide text-slate-500">Missing DOI</div>
                <div class="mt-2 text-2xl font-semibold text-slate-900">{{ formatCount(dataQualityStats.missingDoi) }}</div>
                <p class="mt-1 text-xs text-slate-500">{{ formatPercent(dataQualityStats.missingDoiRate) }} of library</p>
              </article>
              <article class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                <div class="text-xs uppercase tracking-wide text-slate-500">Missing Abstract</div>
                <div class="mt-2 text-2xl font-semibold text-slate-900">{{ formatCount(dataQualityStats.missingAbstract) }}</div>
                <p class="mt-1 text-xs text-slate-500">quality watch</p>
              </article>
            </div>

            <div class="mb-6 grid gap-4 xl:grid-cols-[minmax(0,1.1fr),minmax(0,0.9fr)]">
              <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h3 class="text-base font-semibold text-slate-900">Library Coverage Matrix</h3>
                    <p class="mt-1 text-xs text-slate-500">全库层面的材料、评分和阅读覆盖率，不再只看有材料的子集。</p>
                  </div>
                  <span class="rounded-full bg-white px-3 py-1 text-xs text-slate-600">{{ formatCount(libraryPapers.length) }} papers indexed</span>
                </div>
                <div class="mt-4 grid gap-3 md:grid-cols-2">
                  <article v-for="row in materialCoverageRows" :key="row.key" class="rounded-xl border border-slate-200 bg-white px-3 py-3">
                    <div class="flex items-center justify-between gap-3 text-xs">
                      <span class="font-medium text-slate-700">{{ row.label }}</span>
                      <span class="text-slate-500">{{ formatCount(row.count) }} · {{ formatPercent(row.share) }}</span>
                    </div>
                    <div class="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                      <div class="h-full rounded-full" :style="{ width: percentWidth(row.share), backgroundColor: row.color }"></div>
                    </div>
                  </article>
                </div>
              </section>

              <section class="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
                <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <h3 class="text-base font-semibold text-slate-900">Read Status</h3>
                  <div class="mt-3 space-y-3">
                    <div v-for="row in readStatusRows" :key="row.status" class="space-y-1.5">
                      <div class="flex items-center justify-between text-xs text-slate-500">
                        <span>{{ row.label }}</span>
                        <span>{{ formatCount(row.count) }} · {{ formatPercent(row.share) }}</span>
                      </div>
                      <div class="h-2 overflow-hidden rounded-full bg-white">
                        <div class="h-full rounded-full bg-slate-800" :style="{ width: percentWidth(row.share) }"></div>
                      </div>
                    </div>
                  </div>
                </div>
                <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <h3 class="text-base font-semibold text-slate-900">Paper Types</h3>
                  <div v-if="typeBreakdown.length" class="mt-3 space-y-3">
                    <div v-for="item in typeBreakdown" :key="item.name" class="space-y-1.5">
                      <div class="flex items-center justify-between text-xs text-slate-500">
                        <span class="truncate">{{ item.name }}</span>
                        <span>{{ formatCount(item.count) }}</span>
                      </div>
                      <div class="h-2 overflow-hidden rounded-full bg-white">
                        <div class="h-full rounded-full bg-blue-500" :style="{ width: percentWidth(item.share) }"></div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="mt-3 text-sm text-slate-500">No type breakdown available.</div>
                </div>
              </section>
            </div>

            <div class="mb-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <h3 class="text-base font-semibold text-slate-900">Topic Filter & Trend Window</h3>
                  <p class="mt-1 text-xs text-slate-500">点击主题即可联动到 Papers 和建议阅读队列。</p>
                </div>
                <div class="inline-flex rounded-full border border-slate-200 bg-white p-1 text-xs">
                  <button class="rounded-full px-3 py-1.5" :class="trendWindowYears === 1 ? 'bg-slate-900 text-white' : 'text-slate-600'" @click="trendWindowYears = 1">1y</button>
                  <button class="rounded-full px-3 py-1.5" :class="trendWindowYears === 3 ? 'bg-slate-900 text-white' : 'text-slate-600'" @click="trendWindowYears = 3">3y</button>
                  <button class="rounded-full px-3 py-1.5" :class="trendWindowYears === 5 ? 'bg-slate-900 text-white' : 'text-slate-600'" @click="trendWindowYears = 5">5y</button>
                </div>
              </div>
              <div class="mt-3 flex flex-wrap gap-2">
                <button
                  class="rounded-full border px-3 py-1 text-xs transition"
                  :class="selectedTopic ? 'border-slate-200 bg-white text-slate-700' : 'border-blue-500 bg-blue-50 text-blue-700'"
                  @click="selectedTopic = ''"
                >
                  All topics
                </button>
                <button
                  v-for="topic in topTopicChips"
                  :key="topic"
                  class="rounded-full border px-3 py-1 text-xs transition"
                  :class="selectedTopic === topic ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'"
                  @click="selectedTopic = topic"
                >
                  {{ topic }}
                </button>
              </div>
            </div>

            <div class="grid gap-4 xl:grid-cols-[minmax(0,1.3fr),minmax(0,0.7fr)]">
              <div>
                <h3 class="text-base font-semibold text-slate-900">Trend Highlights</h3>
                <p class="mt-1 text-xs text-slate-500">先从统计视角判断这批论文更偏前沿跟踪，还是已经形成相对稳定的主题结构。</p>

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

                <div class="mt-6 rounded-2xl border border-slate-200 p-4">
                  <div class="flex items-center justify-between gap-3">
                    <h4 class="text-sm font-semibold text-slate-900">Topic Heat Timeline</h4>
                    <span class="text-xs text-slate-500">{{ fullYearRange.length ? (fullYearRange[0] + ' - ' + fullYearRange[fullYearRange.length - 1]) : 'n/a' }}</span>
                  </div>
                  <div v-if="keywordYearRows.length" class="mt-4 space-y-3">
                    <div v-for="row in keywordYearRows" :key="row.topic" class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
                      <div class="mb-2 flex items-center justify-between gap-3">
                        <button class="truncate text-left text-xs font-medium text-slate-700 hover:text-blue-700" @click="selectedTopic = row.topic">{{ row.topic }}</button>
                        <span class="text-[11px] text-slate-500">{{ row.total }}</span>
                      </div>
                      <div class="flex h-10 items-end gap-1">
                        <div
                          v-for="bar in row.bars"
                          :key="bar.year"
                          class="group relative w-full rounded-t bg-blue-300"
                          :style="{ height: bar.height }"
                        >
                          <span class="pointer-events-none absolute -top-7 left-1/2 hidden -translate-x-1/2 whitespace-nowrap rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-white group-hover:block">
                            {{ bar.year }} · {{ bar.count }}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="mt-4 text-sm text-slate-500">Not enough paper metadata to build topic timeline.</div>
                </div>
              </div>

              <div>
                <div class="flex items-center justify-between gap-3">
                  <h3 class="text-base font-semibold text-slate-900">Topic Readiness</h3>
                  <span class="rounded-full px-3 py-1 text-xs font-medium" :class="selectedLibrary.has_topics ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'">
                    {{ selectedLibrary.has_topics ? 'Topics available' : 'Topics missing' }}
                  </span>
                </div>
                <p class="mt-1 text-xs text-slate-500">这里展示的是构建时刻已保存的 topic model 结果。</p>

                <div v-if="topicOverview.length" class="mt-4">
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

                <div class="mt-5 rounded-2xl border border-slate-200 p-4">
                  <h4 class="text-sm font-semibold text-slate-900">Rising Topics</h4>
                  <div v-if="risingTopics.length" class="mt-3 space-y-2">
                    <button
                      v-for="item in risingTopics"
                      :key="item.topic"
                      class="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-xs hover:bg-white"
                      @click="selectedTopic = item.topic"
                    >
                      <span class="truncate text-slate-700">{{ item.topic }}</span>
                      <span class="shrink-0 font-medium text-emerald-700">+{{ item.momentum.toFixed(1) }}</span>
                    </button>
                  </div>
                  <div v-else class="mt-3 text-sm text-slate-500">No rising signal yet.</div>
                </div>

                <div class="mt-4 rounded-2xl border border-slate-200 p-4">
                  <h4 class="text-sm font-semibold text-slate-900">Cooling Topics</h4>
                  <div v-if="fadingTopics.length" class="mt-3 space-y-2">
                    <button
                      v-for="item in fadingTopics"
                      :key="item.topic"
                      class="flex w-full items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-left text-xs hover:bg-white"
                      @click="selectedTopic = item.topic"
                    >
                      <span class="truncate text-slate-700">{{ item.topic }}</span>
                      <span class="shrink-0 font-medium text-amber-700">{{ item.momentum.toFixed(1) }}</span>
                    </button>
                  </div>
                  <div v-else class="mt-3 text-sm text-slate-500">No cooling signal yet.</div>
                </div>
              </div>
            </div>

            <div class="mt-6 grid gap-4 lg:grid-cols-2">
              <div class="rounded-2xl border border-slate-200 p-4">
                <h4 class="text-sm font-semibold text-slate-900">Representative Milestones (by year)</h4>
                <p class="mt-1 text-xs text-slate-500">每年选引用最高代表作，可快速复盘技术演化路径。</p>
                <div v-if="representativeTimeline.length" class="mt-4 space-y-2">
                  <button
                    v-for="item in representativeTimeline"
                    :key="item.year + '-' + (item.paper.route_id || item.paper.paper_id || item.paper.title)"
                    class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-left hover:bg-white"
                    @click="openPaperRef(item.paper.route_id || item.paper.paper_ref)"
                  >
                    <div class="text-[11px] text-slate-500">{{ item.year }} · {{ formatCount(item.citation) }} cites</div>
                    <div class="mt-1 line-clamp-2 text-sm font-medium text-slate-800">{{ item.paper.title }}</div>
                  </button>
                </div>
                <div v-else class="mt-3 text-sm text-slate-500">No yearly milestones available.</div>
              </div>

              <div class="rounded-2xl border border-slate-200 p-4">
                <h4 class="text-sm font-semibold text-slate-900">Action Queue · Priority 10</h4>
                <p class="mt-1 text-xs text-slate-500">未读论文按“趋势动量 + 引用影响 + 近年性”综合排序。</p>
                <div v-if="priorityReadingQueue.length" class="mt-4 space-y-2">
                  <button
                    v-for="(paper, idx) in priorityReadingQueue"
                    :key="paper.route_id || paper.paper_id || idx"
                    class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-left hover:bg-white"
                    @click="openPaperRef(paper.route_id || paper.paper_id)"
                  >
                    <div class="text-[11px] text-slate-500">#{{ idx + 1 }} · {{ paper.year || '?' }} · {{ (paper._priorityScore || 0).toFixed(1) }}</div>
                    <div class="mt-1 line-clamp-2 text-sm font-medium text-slate-800">{{ paper.title }}</div>
                  </button>
                </div>
                <div v-else class="mt-3 text-sm text-slate-500">All papers are read or queue unavailable.</div>
              </div>
            </div>

            <div class="mt-6 grid gap-4 xl:grid-cols-4">
              <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <h4 class="text-sm font-semibold text-slate-900">High-impact Unread</h4>
                <p class="mt-1 text-xs text-slate-500">高引用但未读，适合补全基础脉络。</p>
                <div v-if="highImpactUnread.length" class="mt-4 space-y-2">
                  <button v-for="paper in highImpactUnread" :key="paper.route_id || paper.paper_id" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-left hover:bg-slate-50" @click="openPaperRef(paper.route_id || paper.paper_id)">
                    <div class="text-[11px] text-slate-500">{{ paper.year || '?' }} · {{ formatCount(paper.citation_count || paper.cited_by_count || 0) }} cites</div>
                    <div class="mt-1 line-clamp-2 text-sm font-medium text-slate-800">{{ paper.title }}</div>
                  </button>
                </div>
                <div v-else class="mt-3 text-sm text-slate-500">No high-impact unread papers.</div>
              </section>

              <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <h4 class="text-sm font-semibold text-slate-900">Recent Strong Scores</h4>
                <p class="mt-1 text-xs text-slate-500">近年高评分论文，适合判断当前方向。</p>
                <div v-if="recentStrongScores.length" class="mt-4 space-y-2">
                  <button v-for="paper in recentStrongScores" :key="paper.route_id || paper.paper_id" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-left hover:bg-slate-50" @click="openPaperRef(paper.route_id || paper.paper_id)">
                    <div class="text-[11px] text-slate-500">{{ paper.year || '?' }} · score {{ formatScore(overallScore(paper)) }}</div>
                    <div class="mt-1 line-clamp-2 text-sm font-medium text-slate-800">{{ paper.title }}</div>
                  </button>
                </div>
                <div v-else class="mt-3 text-sm text-slate-500">No scored recent papers yet.</div>
              </section>

              <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <h4 class="text-sm font-semibold text-slate-900">Important Missing Materials</h4>
                <p class="mt-1 text-xs text-slate-500">高引用但 summary/method 不完整。</p>
                <div v-if="importantMissingMaterials.length" class="mt-4 space-y-2">
                  <button v-for="paper in importantMissingMaterials" :key="paper.route_id || paper.paper_id" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-left hover:bg-slate-50" @click="openPaperRef(paper.route_id || paper.paper_id)">
                    <div class="text-[11px] text-slate-500">{{ formatCount(paper.citation_count || paper.cited_by_count || 0) }} cites · material gap</div>
                    <div class="mt-1 line-clamp-2 text-sm font-medium text-slate-800">{{ paper.title }}</div>
                  </button>
                </div>
                <div v-else class="mt-3 text-sm text-slate-500">No important material gaps.</div>
              </section>

              <section class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <h4 class="text-sm font-semibold text-slate-900">Todo Card Refresh</h4>
                <p class="mt-1 text-xs text-slate-500">弱来源或仍含不确定表述的卡片。</p>
                <div v-if="todoRefreshQueue.length" class="mt-4 space-y-2">
                  <button v-for="card in todoRefreshQueue" :key="card.route_id" class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-left hover:bg-slate-50" @click="openTodoRef(card.route_id || card.paper_route_id)">
                    <div class="text-[11px] text-slate-500">{{ card.analysis_source || 'unknown source' }}</div>
                    <div class="mt-1 line-clamp-2 text-sm font-medium text-slate-800">{{ card.title }}</div>
                  </button>
                </div>
                <div v-else class="mt-3 text-sm text-slate-500">No Todo refresh queue.</div>
              </section>
            </div>

            <section class="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 class="text-base font-semibold text-slate-900">Data Quality Watchlist</h3>
                  <p class="mt-1 text-xs text-slate-500">这些不是论文质量判断，而是当前库数据是否足以支持搜索、评分和趋势分析。</p>
                </div>
                <span class="rounded-full bg-white px-3 py-1 text-xs text-slate-600">{{ qualityIssueRows.length }} checks</span>
              </div>
              <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <article v-for="row in qualityIssueRows" :key="row.key" class="rounded-xl border border-slate-200 bg-white px-3 py-3">
                  <div class="flex items-center justify-between gap-3">
                    <h4 class="text-sm font-medium text-slate-800">{{ row.label }}</h4>
                    <span class="rounded-full px-2 py-0.5 text-[11px] font-medium" :class="row.count ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'">
                      {{ row.count ? 'watch' : 'ok' }}
                    </span>
                  </div>
                  <div class="mt-2 text-2xl font-semibold text-slate-900">{{ formatCount(row.count) }}</div>
                  <p class="mt-1 text-xs leading-5 text-slate-500">{{ row.help }}</p>
                </article>
              </div>
            </section>
          </div>

          <div v-if="exploreTab === 'papers'">
            <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h3 class="text-base font-semibold text-slate-900">Full-library Paper Browser</h3>
                <p class="mt-1 text-xs text-slate-500">基于全库轻量索引浏览论文，不再只展示代表样本。</p>
                <p class="mt-1 text-xs text-slate-400">显示 {{ displayedResults.length }} / {{ paperResultTotal }}</p>
                <p v-if="selectedTopic" class="mt-1 text-xs text-blue-600">Topic filter: {{ selectedTopic }}</p>
              </div>
              <div class="flex flex-wrap gap-1 rounded-2xl border border-slate-200 bg-slate-50 p-1 text-sm">
                <button class="rounded-full px-4 py-2 transition" :class="paperView === 'all' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'" @click="paperView = 'all'">
                  All
                </button>
                <button class="rounded-full px-4 py-2 transition" :class="paperView === 'top' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'" @click="paperView = 'top'">
                  Top Cited
                </button>
                <button class="rounded-full px-4 py-2 transition" :class="paperView === 'recent' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'" @click="paperView = 'recent'">
                  Recent Papers
                </button>
                <button class="rounded-full px-4 py-2 transition" :class="paperView === 'scored' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'" @click="paperView = 'scored'">
                  Scored
                </button>
                <button class="rounded-full px-4 py-2 transition" :class="paperView === 'gaps' ? 'bg-slate-900 text-white shadow-sm' : 'text-slate-600 hover:text-slate-900'" @click="paperView = 'gaps'">
                  Material Gaps
                </button>
              </div>
            </div>

            <div v-if="displayedResults.length === 0" class="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-center text-sm text-slate-500">
              No representative papers to show.
            </div>
            <div v-else class="mt-6 grid gap-4 md:grid-cols-2">
              <article v-for="(paper, index) in displayedResults" :key="paper.route_id || paper.paper_id || paper.title || index" class="flex h-full flex-col rounded-2xl border border-slate-200 bg-slate-50 p-4 transition hover:-translate-y-0.5 hover:shadow-md">
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="text-[11px] font-semibold uppercase tracking-wide text-slate-400">#{{ index + 1 }} · {{ paperViewLabel }}</div>
                    <h4 class="mt-2 line-clamp-2 text-base font-semibold text-slate-900">{{ paper.title }}</h4>
                  </div>
                  <span class="shrink-0 rounded-full bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700">
                    {{ formatCount(paper.citation_count || paper.cited_by_count || 0) }} cites
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
                    <div v-else class="truncate">{{ paper.route_id || paper.paper_id || paper.dir_name || 'No local ref' }}</div>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <button class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-white" @click.stop="openPaperRef(paper.route_id || paper.paper_ref)">
                      Open Paper
                    </button>
                    <a v-if="paper.doi" :href="`https://doi.org/${paper.doi}`" target="_blank" rel="noreferrer" class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-white">
                      DOI
                    </a>
                  </div>
                </div>
              </article>
            </div>

            <div v-if="paperResultTotal > 12" class="mt-4 flex flex-wrap gap-2">
              <button
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                :disabled="displayedResults.length >= paperResultTotal"
                @click="visiblePaperCount = Math.min(visiblePaperCount + 12, paperResultTotal)"
              >
                加载更多
              </button>
              <button
                class="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                :disabled="visiblePaperCount <= 12"
                @click="visiblePaperCount = 12"
              >
                收起
              </button>
            </div>
          </div>

        </div>
      </section>
    </template>
  </div>
</template>

<script setup>

const { fetchJson } = useStaticSiteData()
const router = useRouter()

const selectedLibrary = ref(null)
const libraryPapers = ref([])
const todoCards = ref([])
const loading = ref(true)
const errorMessage = ref('')
const paperView = ref('all')
const visiblePaperCount = ref(12)
const exploreTab = ref('trends')
const activeTopicId = ref(null)
const trendWindowYears = ref(3)
const selectedTopic = ref('')

const exploreTabs = [
  { key: 'trends', label: 'Trends & Topics' },
  { key: 'papers', label: 'Papers' },
]

const activeTopic = computed(() => {
  if (activeTopicId.value == null && topicOverview.value.length > 0) {
    return topicOverview.value[0]
  }
  return topicOverview.value.find((topic) => topic.topic_id === activeTopicId.value) || null
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
const typeBreakdown = computed(() => trendOverview.value.type_breakdown || [])

function citationOf(paper) {
  return Number(paper?.citation_count || paper?.cited_by_count || 0)
}

function overallScore(paper) {
  return Number(paper?.rating?.overall_score || paper?.rating?.overall || 0)
}

function isRead(paper) {
  const status = String(paper?.read_status || '').toLowerCase()
  return status === 'read' || status === 'done'
}

const allPaperResults = computed(() => {
  const papers = [...libraryPapers.value]
  if (paperView.value === 'top') {
    return papers.sort((a, b) => citationOf(b) - citationOf(a) || Number(b.year || 0) - Number(a.year || 0))
  }
  if (paperView.value === 'recent') {
    return papers.sort((a, b) => Number(b.year || 0) - Number(a.year || 0) || citationOf(b) - citationOf(a))
  }
  if (paperView.value === 'scored') {
    return papers.filter((paper) => overallScore(paper) > 0).sort((a, b) => overallScore(b) - overallScore(a) || Number(b.year || 0) - Number(a.year || 0))
  }
  if (paperView.value === 'gaps') {
    return papers.filter((paper) => !paper?.has_materials).sort((a, b) => citationOf(b) - citationOf(a) || Number(b.year || 0) - Number(a.year || 0))
  }
  return papers.sort((a, b) => String(a.title || '').localeCompare(String(b.title || '')))
})

const paperViewLabel = computed(() => ({
  all: 'full library',
  top: 'citation leader',
  recent: 'recent paper',
  scored: 'scored paper',
  gaps: 'material gap',
}[paperView.value] || 'paper'))

const STOPWORDS = new Set([
  'the', 'and', 'for', 'with', 'from', 'into', 'towards', 'toward', 'based', 'using', 'via', 'under', 'over',
  'in', 'on', 'of', 'to', 'a', 'an', 'is', 'are', 'by', 'as', 'be', 'or', 'at', 'we', 'our', 'their', 'this',
  'that', 'these', 'those', 'can', 'may', 'new', 'toward', 'study', 'learning', 'model', 'models', 'robot', 'robots',
])

function normalizeTopicToken(token) {
  const value = String(token || '').toLowerCase().trim()
  if (!value) return ''
  if (value === 'rl') return 'reinforcement learning'
  if (value === 'offline rl') return 'offline reinforcement learning'
  if (value === 'vla') return 'vision-language-action'
  if (value === 'wbc') return 'whole-body control'
  if (value === 'mpc') return 'model predictive control'
  return value
}

function extractPaperTopics(paper) {
  const tags = Array.isArray(paper?.tags) ? paper.tags : []
  const title = String(paper?.title || '').toLowerCase()
  const abstract = String(paper?.abstract || '').toLowerCase().slice(0, 1200)
  const text = `${title} ${abstract}`
  const bucket = new Set(tags.map((tag) => normalizeTopicToken(tag)).filter(Boolean))

  const phraseRules = [
    ['reinforcement learning', /reinforcement learning|\brl\b/],
    ['offline reinforcement learning', /offline reinforcement learning|offline rl/],
    ['diffusion', /diffusion|denoising/],
    ['world model', /world model|world-model/],
    ['humanoid', /humanoid/],
    ['legged locomotion', /legged|quadruped|locomotion/],
    ['loco-manipulation', /loco-?manipulation/],
    ['imitation learning', /imitation learning|behavior cloning/],
    ['model predictive control', /model predictive control|\bmpc\b/],
    ['vision-language-action', /vision-language-action|\bvla\b/],
    ['transformer', /transformer|attention/],
    ['teleoperation', /teleoperation|teleop/],
  ]

  for (const [name, rule] of phraseRules) {
    if (rule.test(text)) bucket.add(name)
  }

  const tokens = (title.match(/[a-z][a-z0-9-]{3,}/g) || [])
    .map((token) => normalizeTopicToken(token))
    .filter((token) => token && !STOPWORDS.has(token) && token.length <= 24)
  for (const token of tokens.slice(0, 12)) {
    bucket.add(token)
  }

  return [...bucket]
}

function paperContainsTopic(paper, topic) {
  const key = normalizeTopicToken(topic)
  if (!key) return true
  const topics = extractPaperTopics(paper)
  return topics.some((topicName) => topicName.includes(key) || key.includes(topicName))
}

const filteredPaperResults = computed(() => {
  if (!selectedTopic.value) return allPaperResults.value
  return allPaperResults.value.filter((paper) => paperContainsTopic(paper, selectedTopic.value))
})

const paperResultTotal = computed(() => filteredPaperResults.value.length)
const displayedResults = computed(() => filteredPaperResults.value.slice(0, visiblePaperCount.value))

const fullYearRange = computed(() => {
  const years = libraryPapers.value
    .map((paper) => Number(paper?.year || 0))
    .filter((year) => Number.isFinite(year) && year > 1900)
    .sort((a, b) => a - b)
  if (!years.length) return []
  return [...new Set(years)]
})

const keywordYearRows = computed(() => {
  const years = fullYearRange.value
  if (!years.length) return []

  const table = new Map()
  for (const paper of libraryPapers.value) {
    const year = Number(paper?.year || 0)
    if (!Number.isFinite(year) || year <= 1900) continue
    const topics = extractPaperTopics(paper)
    for (const topic of topics) {
      if (!topic) continue
      if (!table.has(topic)) {
        table.set(topic, { topic, total: 0, yearly: new Map() })
      }
      const row = table.get(topic)
      row.total += 1
      row.yearly.set(year, (row.yearly.get(year) || 0) + 1)
    }
  }

  const maxCell = Math.max(1, ...[...table.values()].map((row) => Math.max(0, ...years.map((y) => row.yearly.get(y) || 0))))

  return [...table.values()]
    .filter((row) => row.total >= 4)
    .sort((a, b) => b.total - a.total)
    .slice(0, 14)
    .map((row) => ({
      topic: row.topic,
      total: row.total,
      bars: years.map((year) => {
        const count = row.yearly.get(year) || 0
        return {
          year,
          count,
          height: `${Math.max(8, Math.round((count / maxCell) * 100))}%`,
        }
      }),
    }))
})

const topTopicChips = computed(() => keywordYearRows.value.slice(0, 10).map((item) => item.topic))

const topicMomentumRows = computed(() => {
  const years = fullYearRange.value
  if (!years.length) return []
  const maxYear = years[years.length - 1]
  const win = Number(trendWindowYears.value || 3)
  const recentStart = maxYear - win + 1

  return keywordYearRows.value.map((row) => {
    const recent = row.bars.filter((item) => item.year >= recentStart).reduce((sum, item) => sum + item.count, 0)
    const past = row.bars.filter((item) => item.year < recentStart).reduce((sum, item) => sum + item.count, 0)
    const recentAvg = recent / Math.max(1, win)
    const pastAvg = past / Math.max(1, years.length - win)
    return {
      topic: row.topic,
      total: row.total,
      recent,
      past,
      momentum: Number((recentAvg - pastAvg).toFixed(2)),
    }
  })
})

const risingTopics = computed(() => topicMomentumRows.value
  .filter((item) => item.recent >= 2)
  .sort((a, b) => b.momentum - a.momentum)
  .slice(0, 6)
)

const fadingTopics = computed(() => topicMomentumRows.value
  .filter((item) => item.past >= 2)
  .sort((a, b) => a.momentum - b.momentum)
  .slice(0, 6)
)

const readStats = computed(() => {
  const total = libraryPapers.value.length
  const read = libraryPapers.value.filter((paper) => isRead(paper)).length
  const reading = libraryPapers.value.filter((paper) => String(paper?.read_status || '').toLowerCase() === 'reading').length
  const unread = Math.max(0, total - read - reading)
  return {
    total,
    read,
    reading,
    unread,
    readRate: total ? read / total : 0,
  }
})

const readStatusRows = computed(() => {
  const total = libraryPapers.value.length || 1
  const rows = [
    ['read', 'Read'],
    ['reading', 'Reading'],
    ['unread', 'Unread'],
    ['skipped', 'Skipped'],
  ]
  return rows.map(([status, label]) => {
    const count = libraryPapers.value.filter((paper) => String(paper?.read_status || 'unread').toLowerCase() === status).length
    return { status, label, count, share: count / total }
  }).filter((row) => row.count > 0 || row.status !== 'skipped')
})

const materialStats = computed(() => {
  const papers = libraryPapers.value
  return {
    total: papers.length,
    ready: papers.filter((paper) => paper?.has_materials).length,
    summary: papers.filter((paper) => paper?.materials?.summary || paper?.has_summary).length,
    method: papers.filter((paper) => paper?.materials?.method).length,
    score: papers.filter((paper) => paper?.materials?.score_report).length,
    report: papers.filter((paper) => paper?.materials?.report).length,
    rating: papers.filter((paper) => paper?.materials?.rating || overallScore(paper) > 0).length,
    sensemaking: papers.filter((paper) => paper?.materials?.sensemaking).length,
  }
})

const materialCoverageRows = computed(() => {
  const total = materialStats.value.total || 1
  return [
    { key: 'ready', label: 'Summary + Method ready', count: materialStats.value.ready, color: '#10b981' },
    { key: 'summary', label: 'Summary available', count: materialStats.value.summary, color: '#3b82f6' },
    { key: 'method', label: 'Method note available', count: materialStats.value.method, color: '#06b6d4' },
    { key: 'score', label: 'Compass score available', count: materialStats.value.score, color: '#f59e0b' },
    { key: 'report', label: 'Compass report available', count: materialStats.value.report, color: '#f97316' },
    { key: 'sensemaking', label: 'Sensemaking available', count: materialStats.value.sensemaking, color: '#334155' },
  ].map((row) => ({ ...row, share: row.count / total }))
})

const dataQualityStats = computed(() => {
  const papers = libraryPapers.value
  const total = papers.length || 1
  const missingDoi = papers.filter((paper) => !String(paper?.doi || '').trim()).length
  const missingYear = papers.filter((paper) => !Number(paper?.year || 0)).length
  const missingAbstract = papers.filter((paper) => !String(paper?.abstract || '').trim()).length
  const missingCitation = papers.filter((paper) => citationOf(paper) <= 0).length
  const missingMaterials = papers.filter((paper) => !paper?.has_materials).length
  const missingRating = papers.filter((paper) => overallScore(paper) <= 0).length
  return {
    missingDoi,
    missingYear,
    missingAbstract,
    missingCitation,
    missingMaterials,
    missingRating,
    missingDoiRate: missingDoi / total,
  }
})

const heroMetricCards = computed(() => {
  const todoCount = todoCards.value.length
  return [
    { label: 'Full Library', value: formatCount(libraryPapers.value.length || selectedLibrary.value?.count || 0), help: 'all papers' },
    { label: 'Materials', value: formatPercent(materialStats.value.total ? materialStats.value.ready / materialStats.value.total : 0), help: `${formatCount(materialStats.value.ready)} ready` },
    { label: 'Todo', value: formatCount(todoCount), help: 'reading queue' },
    { label: 'Read', value: formatPercent(readStats.value.readRate), help: `${formatCount(readStats.value.read)} done` },
  ]
})

const representativeTimeline = computed(() => {
  const map = new Map()
  for (const paper of libraryPapers.value) {
    if (selectedTopic.value && !paperContainsTopic(paper, selectedTopic.value)) continue
    const year = Number(paper?.year || 0)
    if (!Number.isFinite(year) || year <= 1900) continue
    const citation = Number(paper?.citation_count || paper?.cited_by_count || 0)
    const existing = map.get(year)
    if (!existing || citation > existing.citation) {
      map.set(year, { year, paper, citation })
    }
  }
  return [...map.values()]
    .sort((a, b) => b.year - a.year)
    .slice(0, 12)
})

const priorityReadingQueue = computed(() => {
  const rising = new Set(risingTopics.value.slice(0, 4).map((item) => item.topic))
  const maxYear = fullYearRange.value[fullYearRange.value.length - 1] || new Date().getFullYear()

  const candidates = libraryPapers.value
    .filter((paper) => {
      const status = String(paper?.read_status || '').toLowerCase()
      return status !== 'read' && status !== 'done'
    })
    .map((paper) => {
      const citation = Number(paper?.citation_count || paper?.cited_by_count || 0)
      const year = Number(paper?.year || 0)
      const topics = extractPaperTopics(paper)
      const trendHit = topics.some((topic) => rising.has(topic))
      const score = Math.log10(citation + 1) * 3 + Math.max(0, year - (maxYear - 5)) * 0.7 + (trendHit ? 2 : 0)
      return { ...paper, _priorityScore: score }
    })
    .sort((a, b) => b._priorityScore - a._priorityScore)

  return candidates.slice(0, 10)
})

const highImpactUnread = computed(() => libraryPapers.value
  .filter((paper) => !isRead(paper) && citationOf(paper) > 0)
  .sort((a, b) => citationOf(b) - citationOf(a) || Number(b.year || 0) - Number(a.year || 0))
  .slice(0, 5)
)

const recentStrongScores = computed(() => {
  const maxYear = fullYearRange.value[fullYearRange.value.length - 1] || new Date().getFullYear()
  return libraryPapers.value
    .filter((paper) => Number(paper?.year || 0) >= maxYear - 3 && overallScore(paper) > 0)
    .sort((a, b) => overallScore(b) - overallScore(a) || citationOf(b) - citationOf(a))
    .slice(0, 5)
})

const importantMissingMaterials = computed(() => libraryPapers.value
  .filter((paper) => !paper?.has_materials)
  .sort((a, b) => citationOf(b) - citationOf(a) || Number(b.year || 0) - Number(a.year || 0))
  .slice(0, 5)
)

const UNCERTAINTY_MARKERS = ['摘要未披露', '未披露', '无法确认', '文中未清楚披露', 'not disclosed', 'unclear']

function todoCardNeedsRefresh(card) {
  const source = String(card?.analysis_source || '').toLowerCase()
  if (source === 'metadata' || source === 'metadata+web') return true
  const text = [
    card?.one_line_summary,
    card?.core_innovation,
    card?.key_results?.benchmarks,
    card?.key_results?.improvements,
    card?.key_results?.ablation,
  ].join('\n')
  return UNCERTAINTY_MARKERS.some((marker) => text.includes(marker))
}

const todoRefreshQueue = computed(() => todoCards.value
  .filter((card) => todoCardNeedsRefresh(card))
  .slice(-12)
  .reverse()
)

const qualityIssueRows = computed(() => [
  { key: 'doi', label: 'Missing DOI', count: dataQualityStats.value.missingDoi, help: '影响去重、引用和外部跳转。' },
  { key: 'year', label: 'Missing Year', count: dataQualityStats.value.missingYear, help: '影响时间趋势与近年排序。' },
  { key: 'abstract', label: 'Missing Abstract', count: dataQualityStats.value.missingAbstract, help: '影响主题识别、搜索和卡片质量。' },
  { key: 'citation', label: 'No Citation Count', count: dataQualityStats.value.missingCitation, help: '影响高影响论文排序。' },
  { key: 'materials', label: 'Material Gaps', count: dataQualityStats.value.missingMaterials, help: 'summary/method 不完整，无法形成稳定阅读页。' },
  { key: 'rating', label: 'Missing Rating', count: dataQualityStats.value.missingRating, help: '影响高价值论文筛选。' },
  { key: 'todoWeak', label: 'Todo Weak Sources', count: todoRefreshQueue.value.length, help: '需要重新补充网页上下文或重生成卡片。' },
  { key: 'topic', label: 'Topic Model Missing', count: selectedLibrary.value?.has_topics ? 0 : 1, help: '影响真实 topic readiness 与 roadmap。' },
])

watch(paperView, () => {
  visiblePaperCount.value = 12
})

watch(selectedTopic, () => {
  visiblePaperCount.value = 12
})

const yearDistribution = computed(() => {
  const rows = trendOverview.value.year_distribution || []
  const maxCount = Math.max(1, ...rows.map((item) => Number(item.count || 0)))
  return rows.map((item) => ({
    ...item,
    width: `${Math.max(6, Math.round((Number(item.count || 0) / maxCount) * 100))}%`,
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
    { label: 'Citation Coverage', value: `${citationLabel} · ${citedCoverage}`, help: '同时看主库的平均引用和有引用记录的覆盖率。' },
  ]
})


function formatCount(value) {
  return new Intl.NumberFormat('en-US').format(Number(value || 0))
}

function formatScore(value) {
  const score = Number(value || 0)
  return Number.isFinite(score) ? score.toFixed(score >= 10 ? 0 : 1) : '0'
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

function openPaperRef(paperRef) {
  const value = String(paperRef || '').trim()
  if (!value) return
  if (/^https?:\/\//.test(value)) {
    window.open(value, '_blank', 'noopener,noreferrer')
    return
  }
  router.push(`/paper/${value}`)
}

function openTodoRef(routeId) {
  const value = String(routeId || '').trim()
  if (!value) return
  router.push(`/todo/${value}`)
}

const loadExploreSnapshot = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [data, library, todoSnapshot] = await Promise.all([
      fetchJson('explore/current-library.json'),
      fetchJson('library.json').catch(() => ({ papers: [] })),
      fetchJson('todo-cards.json').catch(() => ({ cards: [] })),
    ])

    selectedLibrary.value = data
    libraryPapers.value = Array.isArray(data?.papers)
      ? data.papers
      : (Array.isArray(library?.papers) ? library.papers : [])
    todoCards.value = Array.isArray(todoSnapshot?.cards) ? todoSnapshot.cards : []
    if (topicOverview.value.length > 0) {
      activeTopicId.value = topicOverview.value[0].topic_id
    }
  } catch (error) {
    console.error('Failed to load explore snapshot:', error)
    errorMessage.value = 'Failed to load static library analysis snapshot.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadExploreSnapshot()
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
  font-size: 1.125rem;
  line-height: 1.75rem;
  font-weight: 700;
  color: #0f172a;
}

.roadmap-content :deep(h4) {
  margin: 1.2rem 0 0.5rem;
  font-size: 1rem;
  line-height: 1.5rem;
  font-weight: 600;
  color: #0f172a;
}

.roadmap-content :deep(p) {
  margin: 0.85rem 0;
}

.roadmap-content :deep(ul),
.roadmap-content :deep(ol) {
  margin: 0.85rem 0;
  padding-left: 1.25rem;
}

.roadmap-content :deep(li) {
  margin: 0.35rem 0;
}

.roadmap-content :deep(hr) {
  margin: 1.75rem 0;
  border: 0;
  border-top: 1px solid #e2e8f0;
}

.roadmap-content :deep(strong) {
  color: #0f172a;
  font-weight: 600;
}

.roadmap-content :deep(blockquote) {
  margin: 1rem 0;
  border-left: 3px solid #94a3b8;
  background: #f8fafc;
  padding: 0.75rem 1rem;
  color: #475569;
}

.roadmap-content :deep(code) {
  border-radius: 0.375rem;
  background: #f8fafc;
  padding: 0.15rem 0.35rem;
  font-size: 0.9em;
  color: #0f172a;
}

.roadmap-content :deep(.paper-link) {
  cursor: pointer;
}

.roadmap-content :deep(pre) {
  overflow-x: auto;
  border-radius: 1rem;
  background: #0f172a;
  padding: 1rem 1.25rem;
  color: #e2e8f0;
}

.roadmap-content :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}

.roadmap-content :deep(table) {
  width: 100%;
  overflow: hidden;
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
  border-collapse: separate;
  border-spacing: 0;
  margin: 1rem 0;
}

.roadmap-content :deep(thead) {
  background: #f8fafc;
}

.roadmap-content :deep(th),
.roadmap-content :deep(td) {
  border-bottom: 1px solid #e2e8f0;
  padding: 0.75rem 0.9rem;
  text-align: left;
  vertical-align: top;
}

.roadmap-content :deep(th) {
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #64748b;
}

.roadmap-content :deep(td) {
  font-size: 0.95rem;
}

.roadmap-content :deep(tbody tr:last-child td) {
  border-bottom: none;
}

.roadmap-content :deep(a) {
  color: #2563eb;
  text-decoration: none;
  font-weight: 500;
}

.roadmap-content :deep(a:hover) {
  text-decoration: underline;
}
</style>
