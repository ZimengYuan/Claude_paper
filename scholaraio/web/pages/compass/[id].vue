<template>
  <div class="min-h-screen bg-[linear-gradient(180deg,_#f8fafc_0%,_#eef2ff_32%,_#f8fafc_100%)]">
    <div class="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
        <button class="text-sm font-medium text-blue-600 transition hover:text-blue-800" @click="goBackToTodo">
          ← 返回 Todo 详情
        </button>

        <a
          v-if="sourceLink"
          class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
          :href="sourceLink"
          :target="sourceLink.startsWith('http') ? '_blank' : null"
          :rel="sourceLink.startsWith('http') ? 'noopener noreferrer' : null"
        >
          查看原论文
        </a>
      </div>

      <div v-if="loading" class="py-20 text-center">
        <div class="mx-auto h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600"></div>
        <p class="mt-4 text-sm text-slate-500">Loading Paper Compass...</p>
      </div>

      <div v-else-if="errorMessage" class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ errorMessage }}
      </div>

      <div v-else-if="card" class="space-y-6">
        <section class="relative overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-sm">
          <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.16),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(15,23,42,0.08),_transparent_32%)]"></div>
          <div class="relative p-8">
            <div class="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_320px]">
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-blue-700">
                    Paper Compass
                  </span>
                  <span
                    class="rounded-full px-3 py-1 text-xs font-medium"
                    :class="heroStatusClass"
                  >
                    {{ heroStatusText }}
                  </span>
                </div>

                <h1 class="mt-5 text-4xl font-semibold leading-tight text-slate-950">{{ card.title }}</h1>
                <p class="mt-4 text-sm text-slate-600">{{ card.authors?.join(', ') || '作者信息缺失' }}</p>
                <p class="mt-1 text-xs text-slate-500">
                  {{ card.year || '年份未知' }}<span v-if="card.journal"> · {{ card.journal }}</span>
                  <span v-if="card.doi"> · DOI: {{ card.doi }}</span>
                </p>

                <div class="mt-8 rounded-[28px] border border-slate-200 bg-slate-50 p-6">
                  <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">核心判断</p>
                  <p class="mt-3 text-base leading-8 text-slate-800">
                    {{ heroSummaryText }}
                  </p>

                  <div v-if="showTodoSummarySnippet" class="mt-5 border-t border-slate-200 pt-5">
                    <p class="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Todo Summary</p>
                    <p class="mt-2 text-sm leading-7 text-slate-600">{{ card.one_line_summary }}</p>
                  </div>
                </div>
              </div>

              <div class="w-full rounded-[28px] border border-slate-900 bg-[linear-gradient(135deg,_#020617,_#111827_54%,_#1d4ed8)] p-6 text-white shadow-lg">
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-300">Overall Score</p>
                <div class="mt-4 flex items-end gap-3">
                  <p class="text-5xl font-semibold leading-none">{{ overallRatingText }}</p>
                  <span class="pb-1 text-sm text-slate-300">/ 10</span>
                </div>

                <div class="mt-5 flex flex-wrap gap-2">
                  <span
                    v-if="overallGradeText"
                    class="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-white"
                  >
                    {{ overallGradeText }}
                  </span>
                  <span
                    v-if="readingPriorityText"
                    class="rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-medium text-white"
                  >
                    {{ readingPriorityText }}
                  </span>
                </div>

                <div class="mt-6 space-y-3">
                  <div
                    v-for="entry in heroMaterialEntries"
                    :key="entry.label"
                    class="flex items-center justify-between rounded-2xl border border-white/10 bg-white/10 px-4 py-3"
                  >
                    <p class="text-sm font-medium text-slate-100">{{ entry.label }}</p>
                    <span
                      class="rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide"
                      :class="entry.ready ? 'bg-emerald-400/15 text-emerald-100' : 'bg-white/10 text-slate-300'"
                    >
                      {{ entry.ready ? '已就绪' : '缺失' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="score" class="rounded-[32px] border border-slate-200 bg-white p-6 shadow-sm scroll-mt-24">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Score Layer</p>
              <h2 class="mt-2 text-2xl font-semibold text-slate-950">Score Report</h2>
              <p class="mt-2 text-sm text-slate-500">先看结构化结论和分项评分，再按需展开原始报告。</p>
            </div>
            <span class="rounded-full border px-3 py-1 text-xs font-medium" :class="materialClass(Boolean(scoreReport))">
              {{ scoreReport ? '已就绪' : '缺失' }}
            </span>
          </div>

          <div v-if="structuredScore.snapshot.length || structuredScore.conclusion.length || structuredScore.oneLine" class="mt-6 grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
            <div v-if="structuredScore.snapshot.length" class="rounded-[28px] border border-slate-200 bg-slate-50 p-5">
              <p class="text-sm font-semibold text-slate-900">论文快照</p>
              <dl class="mt-4 space-y-3 text-sm">
                <div v-for="entry in structuredScore.snapshot" :key="entry.label">
                  <dt class="text-slate-500">{{ entry.label }}</dt>
                  <dd class="mt-1 break-words text-slate-900">{{ entry.value }}</dd>
                </div>
              </dl>
            </div>

            <div class="space-y-4">
              <div v-if="structuredScore.conclusion.length" class="grid gap-3 md:grid-cols-2">
                <div
                  v-for="entry in structuredScore.conclusion"
                  :key="entry.label"
                  class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4"
                >
                  <p class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ entry.label }}</p>
                  <p class="mt-2 text-sm leading-7 text-slate-900">{{ entry.value }}</p>
                </div>
              </div>

              <div v-if="structuredScore.oneLine" class="rounded-[28px] border border-blue-100 bg-[linear-gradient(135deg,_rgba(239,246,255,0.9),_rgba(248,250,252,1))] p-5">
                <p class="text-sm font-semibold text-slate-900">一句话判断</p>
                <p class="mt-3 text-sm leading-8 text-slate-800">{{ structuredScore.oneLine }}</p>
              </div>
            </div>
          </div>

          <div v-if="structuredScore.scoringRows.length" class="mt-6 space-y-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Scoring Breakdown</p>
              <h3 class="mt-2 text-xl font-semibold text-slate-950">分项评分</h3>
            </div>
            <div class="grid gap-4 xl:grid-cols-2">
              <article
                v-for="row in structuredScore.scoringRows"
                :key="row.dimension"
                class="rounded-[28px] border border-slate-200 bg-slate-50 p-5"
              >
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <p class="text-base font-semibold text-slate-950">{{ row.dimension }}</p>
                    <p class="mt-1 text-xs text-slate-400">满分 {{ row.fullMark }}</p>
                  </div>
                  <span class="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-sm font-semibold text-blue-700">
                    {{ row.score }}/{{ row.fullMark }}
                  </span>
                </div>
                <div class="mt-4 h-2 overflow-hidden rounded-full bg-slate-200">
                  <div
                    class="h-full rounded-full bg-[linear-gradient(90deg,_#1d4ed8,_#60a5fa)]"
                    :style="{ width: scoreRatioWidth(row.score, row.fullMark) }"
                  ></div>
                </div>
                <div class="mt-4 space-y-3">
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">评分依据</p>
                    <p class="mt-2 text-sm leading-7 text-slate-700">{{ row.rationale }}</p>
                  </div>
                  <div>
                    <p class="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">关键证据</p>
                    <p class="mt-2 text-sm leading-7 text-slate-700">{{ row.evidence }}</p>
                  </div>
                </div>
              </article>
            </div>
          </div>

          <div v-if="structuredScore.peers.length" class="mt-6 space-y-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Peer Set</p>
              <h3 class="mt-2 text-xl font-semibold text-slate-950">相似论文对比集合</h3>
            </div>
            <div class="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
              <article
                v-for="peer in structuredScore.peers"
                :key="peer.peer + '-' + peer.title"
                class="rounded-[28px] border border-slate-200 bg-white p-5"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <span class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700">{{ peer.peer }}</span>
                  <span v-if="peer.category" class="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">{{ peer.category }}</span>
                  <span v-if="peer.year" class="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-500">{{ peer.year }}</span>
                </div>
                <h4 class="mt-4 text-base font-semibold leading-7 text-slate-950">{{ peer.title }}</h4>
                <p v-if="peer.venue" class="mt-2 text-sm text-slate-500">{{ peer.venue }}</p>
                <p v-if="peer.citations" class="mt-2 text-xs font-medium text-slate-400">引用量 {{ peer.citations }}</p>
                <p class="mt-4 text-sm leading-7 text-slate-700">{{ peer.reason }}</p>
                <a
                  v-if="peer.arxiv"
                  class="mt-4 inline-flex rounded-xl border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition hover:bg-blue-100"
                  :href="peer.arxiv"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  查看来源
                </a>
              </article>
            </div>
          </div>

          <div v-if="structuredScore.observations.length" class="mt-6 space-y-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Comparison Notes</p>
              <h3 class="mt-2 text-xl font-semibold text-slate-950">横向对比观察</h3>
            </div>
            <div class="grid gap-3 md:grid-cols-3">
              <div
                v-for="entry in structuredScore.observations"
                :key="entry.label"
                class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4"
              >
                <p class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ entry.label }}</p>
                <p class="mt-2 text-sm leading-7 text-slate-900">{{ entry.value }}</p>
              </div>
            </div>
          </div>

          <div v-if="structuredScore.reasons.length" class="mt-6 rounded-[28px] border border-slate-200 bg-slate-50 p-5">
            <p class="text-sm font-semibold text-slate-900">分数形成原因</p>
            <div class="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              <div
                v-for="entry in structuredScore.reasons"
                :key="entry.label"
                class="rounded-2xl border border-slate-200 bg-white px-4 py-4"
              >
                <p class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ entry.label }}</p>
                <p class="mt-2 text-sm leading-7 text-slate-700">{{ entry.value }}</p>
              </div>
            </div>
          </div>

          <div v-if="structuredScore.priority.length || structuredScore.sources.length" class="mt-6 grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)]">
            <div v-if="structuredScore.priority.length" class="rounded-[28px] border border-slate-200 bg-white p-5">
              <p class="text-sm font-semibold text-slate-900">是否值得优先读</p>
              <div class="mt-4 grid gap-3 md:grid-cols-3">
                <div
                  v-for="entry in structuredScore.priority"
                  :key="entry.label"
                  class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4"
                >
                  <p class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ entry.label }}</p>
                  <p class="mt-2 text-sm leading-7 text-slate-900">{{ entry.value }}</p>
                </div>
              </div>
            </div>

            <div v-if="structuredScore.sources.length" class="rounded-[28px] border border-slate-200 bg-slate-50 p-5">
              <p class="text-sm font-semibold text-slate-900">Sources</p>
              <div class="mt-4 flex flex-wrap gap-3">
                <a
                  v-for="source in structuredScore.sources"
                  :key="source.url"
                  class="rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700 transition hover:bg-blue-100"
                  :href="source.url"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {{ source.label || source.url }}
                </a>
              </div>
            </div>
          </div>

          <details v-if="scoreReport" class="mt-6 overflow-hidden rounded-[28px] border border-slate-200 bg-slate-50/80">
            <summary class="cursor-pointer list-none px-5 py-4 text-sm font-semibold text-slate-900">查看原始 Score Report 文本</summary>
            <div class="border-t border-slate-200 p-5">
              <div
                class="markdown-body prose prose-slate max-w-none prose-headings:font-semibold prose-h1:text-2xl prose-h2:mt-8 prose-p:leading-8 prose-li:leading-7 prose-table:w-full"
                v-html="renderMarkdown(scoreReport)"
              ></div>
            </div>
          </details>
          <p v-else class="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-500">
            当前静态快照里还没有这篇论文的评分报告。
          </p>
        </section>

        <section id="report" class="rounded-[32px] border border-slate-200 bg-white p-6 shadow-sm scroll-mt-24">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Readable Layer</p>
              <h2 class="mt-2 text-2xl font-semibold text-slate-950">Report / Learnpath</h2>
              <p class="mt-2 text-sm text-slate-500">把学习路径拆成可扫读的信息块，优先看先修、顺序和快速起步。</p>
            </div>
            <span class="rounded-full border px-3 py-1 text-xs font-medium" :class="materialClass(Boolean(readableReport))">
              {{ readableReport ? '已就绪' : '缺失' }}
            </span>
          </div>

          <div v-if="readableReport && structuredReport.hasStructuredContent" class="mt-6 space-y-6">
            <div class="grid gap-4 xl:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)]">
              <div class="rounded-[28px] border border-slate-200 bg-slate-50 p-5">
                <p class="text-sm font-semibold text-slate-900">论文快照</p>
                <dl class="mt-4 space-y-3 text-sm">
                  <div v-for="entry in structuredReport.snapshot" :key="entry.label">
                    <dt class="text-slate-500">{{ entry.label }}</dt>
                    <dd class="mt-1 break-words text-slate-900">{{ entry.value }}</dd>
                  </div>
                </dl>
              </div>

              <div class="rounded-[28px] border border-blue-100 bg-[linear-gradient(135deg,_rgba(239,246,255,0.9),_rgba(248,250,252,1))] p-5">
                <p class="text-sm font-semibold text-slate-900">30 分钟快速起步</p>
                <div
                  class="markdown-body prose prose-slate mt-4 max-w-none prose-p:leading-8 prose-strong:text-slate-900"
                  v-html="renderMarkdown(structuredReport.quickStartMarkdown || '当前报告里还没有快速起步块。')"
                ></div>
              </div>
            </div>

            <div v-if="structuredReport.prerequisites.length" class="space-y-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Prerequisites</p>
                <h3 class="mt-2 text-xl font-semibold text-slate-950">必学先修知识</h3>
              </div>
              <div class="grid gap-4 xl:grid-cols-2">
                <article
                  v-for="item in structuredReport.prerequisites"
                  :key="item.order + '-' + item.title"
                  class="rounded-[28px] border border-slate-200 bg-slate-50 p-5"
                >
                  <div class="flex items-center justify-between gap-3">
                    <span class="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-500">
                      Step {{ item.order || '-' }}
                    </span>
                    <span v-if="item.time" class="text-xs text-slate-400">{{ item.time }}</span>
                  </div>
                  <h4 class="mt-4 text-lg font-semibold text-slate-950">{{ item.title }}</h4>
                  <p class="mt-3 text-sm leading-7 text-slate-700">{{ item.reason }}</p>
                  <div class="mt-4 space-y-2 text-sm text-slate-600">
                    <p v-if="item.goal"><span class="font-medium text-slate-900">最小目标：</span>{{ item.goal }}</p>
                    <p v-if="item.location"><span class="font-medium text-slate-900">论文位置：</span>{{ item.location }}</p>
                    <p v-if="item.evidence"><span class="font-medium text-slate-900">证据锚点：</span>{{ item.evidence }}</p>
                  </div>
                </article>
              </div>
            </div>

            <div v-if="structuredReport.bridges.length" class="space-y-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Bridge Topics</p>
                <h3 class="mt-2 text-xl font-semibold text-slate-950">桥接知识</h3>
              </div>
              <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <article
                  v-for="item in structuredReport.bridges"
                  :key="item.title"
                  class="rounded-3xl border border-slate-200 bg-white p-5"
                >
                  <p class="text-base font-semibold text-slate-950">{{ item.title }}</p>
                  <div class="mt-4 space-y-2 text-sm leading-7 text-slate-700">
                    <p v-if="item.role"><span class="font-medium text-slate-900">角色：</span>{{ item.role }}</p>
                    <p v-if="item.location"><span class="font-medium text-slate-900">论文位置：</span>{{ item.location }}</p>
                    <p v-if="item.evidence"><span class="font-medium text-slate-900">证据：</span>{{ item.evidence }}</p>
                    <p v-if="item.action"><span class="font-medium text-slate-900">建议动作：</span>{{ item.action }}</p>
                  </div>
                </article>
              </div>
            </div>

            <div v-if="structuredReport.personalizedMarkdown" class="rounded-[28px] border border-slate-200 bg-slate-50 p-5">
              <p class="text-sm font-semibold text-slate-900">个性化增量</p>
              <div
                class="markdown-body prose prose-slate mt-4 max-w-none prose-p:leading-8 prose-li:leading-7"
                v-html="renderMarkdown(structuredReport.personalizedMarkdown)"
              ></div>
            </div>

            <div v-if="structuredReport.learningOrder.length" class="space-y-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Learning Order</p>
                <h3 class="mt-2 text-xl font-semibold text-slate-950">建议学习顺序</h3>
              </div>
              <div class="grid gap-3">
                <div
                  v-for="(item, index) in structuredReport.learningOrder"
                  :key="index"
                  class="flex gap-4 rounded-3xl border border-slate-200 bg-white px-5 py-4"
                >
                  <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
                    {{ index + 1 }}
                  </div>
                  <p class="pt-1 text-sm leading-7 text-slate-700">{{ item }}</p>
                </div>
              </div>
            </div>

            <div v-if="structuredReport.resources.length" class="space-y-4">
              <div>
                <p class="text-xs font-semibold uppercase tracking-[0.24em] text-slate-400">Resources</p>
                <h3 class="mt-2 text-xl font-semibold text-slate-950">推荐学习资源</h3>
              </div>
              <div class="grid gap-4 xl:grid-cols-2">
                <article
                  v-for="resource in structuredReport.resources"
                  :key="resource.title"
                  class="rounded-[28px] border border-slate-200 bg-white p-5"
                >
                  <h4 class="text-lg font-semibold text-slate-950">{{ resource.title }}</h4>
                  <div
                    class="markdown-body prose prose-slate mt-4 max-w-none prose-p:leading-8 prose-li:leading-7 prose-a:text-blue-700"
                    v-html="renderMarkdown(resource.body)"
                  ></div>
                </article>
              </div>
            </div>

            <div v-if="structuredReport.sources.length" class="rounded-[28px] border border-slate-200 bg-slate-50 p-5">
              <p class="text-sm font-semibold text-slate-900">Sources</p>
              <div class="mt-4 flex flex-wrap gap-3">
                <a
                  v-for="entry in structuredReport.sources"
                  :key="entry.url"
                  class="rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-700 transition hover:bg-blue-100"
                  :href="entry.url"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {{ entry.label || entry.url }}
                </a>
              </div>
            </div>
          </div>

          <div
            v-else-if="readableReport"
            class="markdown-body prose prose-slate mt-6 max-w-none rounded-[28px] border border-slate-200 bg-white p-6 prose-headings:font-semibold prose-h1:text-2xl prose-h2:mt-8 prose-p:leading-8 prose-li:leading-7"
            v-html="renderMarkdown(readableReport)"
          ></div>
          <p v-else class="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-500">
            当前静态快照里还没有这篇论文的可读报告。
          </p>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { marked } from 'marked'

const { fetchJson } = useStaticSiteData()
const runtimeConfig = useRuntimeConfig()
const route = useRoute()
const routeId = computed(() => String(route.params.id || '').trim())

const loading = ref(true)
const errorMessage = ref('')
const card = ref(null)
const paper = ref(null)
const scoreReport = ref('')
const readableReport = ref('')

const paperRouteId = computed(() => String(card.value?.paper_route_id || '').trim())
const appBaseUrl = computed(() => {
  const value = String(runtimeConfig.app.baseURL || '/')
  return value.endsWith('/') ? value : value + '/'
})
const todoDetailLink = computed(() => appBaseUrl.value + 'todo/' + routeId.value)

useHead(() => ({
  title: card.value ? card.value.title + ' | Paper Compass' : 'Paper Compass',
}))

const cleanInlineMarkdown = (value) => String(value || '')
  .replace(/\*\*/g, '')
  .replace(/`/g, '')
  .replace(/\[(.*?)\]\((.*?)\)/g, '$1')
  .replace(/^#+\s*/gm, '')
  .trim()

const materialClass = (enabled) => {
  return enabled
    ? 'border-blue-200 bg-blue-50 text-blue-700'
    : 'border-slate-200 bg-slate-50 text-slate-400'
}

const sourceLink = computed(() => {
  const doi = String(card.value?.doi || '').trim()
  return doi ? 'https://doi.org/' + doi : ''
})

const keepValue = (value) => value !== null && value !== undefined && value !== ''

const ratingEntries = computed(() => {
  const rating = paper.value?.rating
  if (rating == null) return []

  const compassEntries = [
    { label: '发表信号', value: rating.publication_signal },
    { label: '作者信号', value: rating.author_signal },
    { label: '引用牵引', value: rating.citation_traction },
    { label: '被引质量', value: rating.citation_quality },
    { label: '新颖性', value: rating.novelty },
    { label: '业界信号', value: rating.industry_signal },
    { label: '方向影响', value: rating.field_shaping },
  ].filter((entry) => keepValue(entry.value))

  if (compassEntries.length) return compassEntries

  return [
    { label: '创新性', value: rating.innovation },
    { label: '技术质量', value: rating.technical_quality },
    { label: '实验验证', value: rating.experimental_validation },
    { label: '写作质量', value: rating.writing_quality },
    { label: '相关性', value: rating.relevance },
  ].filter((entry) => keepValue(entry.value))
})

const splitMarkdownSections = (markdown) => {
  const normalized = String(markdown || '').replace(/\r/g, '')
  const sections = []
  let currentTitle = ''
  let currentLines = []

  for (const line of normalized.split('\n')) {
    const match = line.match(/^##\s+(.+)$/)
    if (match) {
      if (currentTitle) {
        sections.push({ title: currentTitle, body: currentLines.join('\n').trim() })
      }
      currentTitle = cleanInlineMarkdown(match[1])
      currentLines = []
      continue
    }
    if (currentTitle) currentLines.push(line)
  }

  if (currentTitle) {
    sections.push({ title: currentTitle, body: currentLines.join('\n').trim() })
  }

  return sections
}

const findSectionBody = (sections, keyword) => {
  const section = sections.find((entry) => entry.title.includes(keyword))
  return section ? section.body : ''
}

const parseBulletEntries = (body) => {
  return String(body || '')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('- '))
    .map((line) => line.slice(2).trim())
    .map((line) => {
      const index = line.indexOf(':')
      if (index === -1) return { label: '', value: cleanInlineMarkdown(line) }
      return {
        label: cleanInlineMarkdown(line.slice(0, index)),
        value: cleanInlineMarkdown(line.slice(index + 1)),
      }
    })
    .filter((entry) => entry.label || entry.value)
}

const parseMarkdownTable = (body) => {
  const lines = String(body || '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  const tableLines = []
  let collecting = false
  for (const line of lines) {
    if (line.startsWith('|')) {
      tableLines.push(line)
      collecting = true
      continue
    }
    if (collecting) break
  }

  if (tableLines.length < 3) return []

  const parseRow = (line) => line.split('|').slice(1, -1).map((cell) => cleanInlineMarkdown(cell))
  const headers = parseRow(tableLines[0])
  return tableLines.slice(2).map((line) => {
    const cells = parseRow(line)
    if (cells.length !== headers.length) return null
    const row = {}
    headers.forEach((header, index) => {
      row[header] = cells[index]
    })
    return row
  }).filter(Boolean)
}

const parseOrderedItems = (body) => {
  return String(body || '')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => /^\d+\.\s+/.test(line))
    .map((line) => cleanInlineMarkdown(line.replace(/^\d+\.\s+/, '')))
}

const parseSubsections = (body) => {
  const normalized = String(body || '').replace(/\r/g, '')
  const sections = []
  let currentTitle = ''
  let currentLines = []

  for (const line of normalized.split('\n')) {
    const match = line.match(/^###\s+(.+)$/)
    if (match) {
      if (currentTitle) {
        sections.push({ title: cleanInlineMarkdown(currentTitle), body: currentLines.join('\n').trim() })
      }
      currentTitle = match[1]
      currentLines = []
      continue
    }
    if (currentTitle) currentLines.push(line)
  }

  if (currentTitle) {
    sections.push({ title: cleanInlineMarkdown(currentTitle), body: currentLines.join('\n').trim() })
  }

  return sections.filter((entry) => entry.body)
}

const parseSourceLinks = (body) => {
  return String(body || '')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.startsWith('- '))
    .map((line) => line.slice(2).trim())
    .map((line) => {
      const match = line.match(/https?:\/\/\S+/)
      const url = match ? match[0] : ''
      const label = cleanInlineMarkdown(url ? line.replace(url, '').replace(/[\s:-]+$/, '') : line)
      return { label: label || url, url }
    })
    .filter((entry) => entry.url)
}

const parseReadableReport = (markdown) => {
  const sections = splitMarkdownSections(markdown)
  const prerequisites = parseMarkdownTable(findSectionBody(sections, '必学先修知识')).map((row) => ({
    order: row['顺序'] || '',
    title: row['知识点'] || '',
    reason: row['为什么必学'] || '',
    location: row['论文使用位置'] || '',
    evidence: row['证据锚点'] || '',
    goal: row['最小学习目标'] || '',
    time: row['预计时间'] || '',
  })).filter((entry) => entry.title)

  const bridges = parseMarkdownTable(findSectionBody(sections, '桥接知识')).map((row) => ({
    title: row['知识点'] || '',
    role: row['角色'] || '',
    location: row['论文使用位置'] || '',
    evidence: row['证据'] || '',
    action: row['建议动作'] || '',
  })).filter((entry) => entry.title)

  return {
    snapshot: parseBulletEntries(findSectionBody(sections, '论文快照')),
    prerequisites,
    bridges,
    personalizedMarkdown: findSectionBody(sections, '个性化增量'),
    resources: parseSubsections(findSectionBody(sections, '推荐学习资源')),
    learningOrder: parseOrderedItems(findSectionBody(sections, '建议学习顺序')),
    quickStartMarkdown: findSectionBody(sections, '30 分钟快速起步'),
    sources: parseSourceLinks(findSectionBody(sections, 'Sources')),
    hasStructuredContent: Boolean(markdown) && (
      prerequisites.length > 0 ||
      bridges.length > 0 ||
      parseBulletEntries(findSectionBody(sections, '论文快照')).length > 0 ||
      parseSubsections(findSectionBody(sections, '推荐学习资源')).length > 0 ||
      parseOrderedItems(findSectionBody(sections, '建议学习顺序')).length > 0 ||
      Boolean(findSectionBody(sections, '30 分钟快速起步'))
    ),
  }
}

const parseScoreReport = (markdown) => {
  const sections = splitMarkdownSections(markdown)
  const conclusionEntries = parseBulletEntries(findSectionBody(sections, '最终结论'))

  return {
    snapshot: parseBulletEntries(findSectionBody(sections, '论文快照')),
    conclusion: conclusionEntries.filter((entry) => entry.label && entry.label !== '一句话判断'),
    oneLine: conclusionEntries.find((entry) => entry.label === '一句话判断')?.value || '',
    scoringRows: parseMarkdownTable(findSectionBody(sections, '分项评分')).map((row) => ({
      dimension: row['维度'] || '',
      fullMark: row['满分'] || '',
      score: row['得分'] || '',
      rationale: row['评分依据'] || '',
      evidence: row['关键证据'] || '',
    })).filter((row) => row.dimension),
    peers: parseMarkdownTable(findSectionBody(sections, '相似论文对比集合')).map((row) => ({
      peer: row['Peer'] || '',
      category: row['类别'] || '',
      title: row['论文'] || '',
      arxiv: row['arXiv'] || '',
      year: row['年份'] || '',
      venue: row['Venue'] || '',
      citations: row['引用量'] || '',
      reason: row['选入理由'] || '',
    })).filter((row) => row.title),
    observations: parseBulletEntries(findSectionBody(sections, '横向对比观察')),
    reasons: parseBulletEntries(findSectionBody(sections, '分数形成原因')),
    priority: parseBulletEntries(findSectionBody(sections, '是否值得优先读')),
    sources: parseSourceLinks(findSectionBody(sections, 'Sources')),
  }
}

const structuredReport = computed(() => parseReadableReport(readableReport.value))
const structuredScore = computed(() => parseScoreReport(scoreReport.value))

const conclusionValue = (label) => {
  return structuredScore.value.conclusion.find((entry) => entry.label === label)?.value || ''
}

const ratingNote = computed(() => paper.value?.rating?.one_line_verdict || paper.value?.rating?.notes || '')
const overallScore = computed(() => paper.value?.rating?.overall_score)
const overallRatingText = computed(() => {
  if (overallScore.value == null) return 'n/a'
  return Number(overallScore.value).toFixed(1)
})
const overallGradeText = computed(() => conclusionValue('等级'))
const readingPriorityText = computed(() => conclusionValue('阅读优先级'))
const heroSummaryText = computed(() => {
  if (structuredScore.value.oneLine) return structuredScore.value.oneLine
  if (ratingNote.value) return ratingNote.value
  if (card.value?.one_line_summary) return card.value.one_line_summary
  return '当前静态快照里还没有更细的 verdict，完整内容会随着评分报告一并更新。'
})
const showTodoSummarySnippet = computed(() => {
  const summary = String(card.value?.one_line_summary || '').trim()
  return Boolean(summary) && summary !== heroSummaryText.value
})
const heroMaterialEntries = computed(() => [
  { label: 'Score Report', ready: Boolean(scoreReport.value) },
  { label: 'Learnpath Report', ready: Boolean(readableReport.value) },
  { label: '结构化 Rating', ready: Boolean(paper.value?.rating) },
])
const heroStatusText = computed(() => {
  const readyCount = heroMaterialEntries.value.filter((entry) => entry.ready).length
  if (readyCount === heroMaterialEntries.value.length) return '评分与报告已就绪'
  if (readyCount > 0) return '部分材料已就绪'
  return '材料待补全'
})
const heroStatusClass = computed(() => {
  const readyCount = heroMaterialEntries.value.filter((entry) => entry.ready).length
  if (readyCount === heroMaterialEntries.value.length) return 'bg-emerald-100 text-emerald-700'
  if (readyCount > 0) return 'bg-amber-100 text-amber-700'
  return 'bg-slate-100 text-slate-500'
})

const scoreBarWidth = (value) => {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return '0%'
  return String(Math.min(Math.max(numeric, 0), 10) * 10) + '%'
}

const scoreRatioWidth = (score, fullMark) => {
  const earned = Number(score)
  const total = Number(fullMark)
  if (!Number.isFinite(earned) || !Number.isFinite(total) || total <= 0) return '0%'
  return String(Math.min(Math.max(earned / total, 0), 1) * 100) + '%'
}

const goBackToTodo = () => navigateTo(todoDetailLink.value)

const renderMarkdown = (text) => {
  if (!text) return ''
  try {
    return marked.parse(String(text))
  } catch (error) {
    console.error('Markdown rendering error:', error)
    return ''
  }
}

const applyPaperPayload = (payload) => {
  paper.value = payload
  scoreReport.value = payload?.score_report || ''
  readableReport.value = payload?.readable_report || ''
}

const loadLinkedPaper = async (matchedCard) => {
  paper.value = null
  scoreReport.value = ''
  readableReport.value = ''

  const linkedRouteId = String(matchedCard?.paper_route_id || '').trim()
  if (!linkedRouteId) return

  try {
    const payload = await fetchJson('papers/' + linkedRouteId + '.json')
    applyPaperPayload(payload)
  } catch (error) {
    console.error('Failed to load linked paper snapshot:', error)
  }
}

const loadCard = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const todoData = await fetchJson('todo-cards.json')
    const cards = Array.isArray(todoData?.cards) ? todoData.cards : []
    const matched = cards.find((item) => item.route_id === routeId.value)
    if (!matched) {
      throw new Error('Paper Compass item not found in snapshot.')
    }
    card.value = {
      ...matched,
      read_status: 'unread',
    }
    await loadLinkedPaper(matched)
  } catch (error) {
    console.error('Failed to load compass detail:', error)
    errorMessage.value = 'Failed to load Paper Compass detail.'
  } finally {
    loading.value = false
  }
}

onMounted(loadCard)
</script>
