import { existsSync, readFileSync } from 'node:fs'
import path from 'node:path'

function loadPrerenderRoutes() {
  const manifestPath = path.resolve(process.cwd(), 'public/site-data/manifest.json')
  const todoCardsPath = path.resolve(process.cwd(), 'public/site-data/todo-cards.json')
  const baseRoutes = ['/', '/explore', '/graph']

  const routes = [...baseRoutes]

  if (existsSync(manifestPath)) {
    try {
      const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8'))
      const paperRoutes = Array.isArray(manifest.paper_routes) ? manifest.paper_routes : []
      routes.push(...paperRoutes)
    } catch {}
  }

  if (existsSync(todoCardsPath)) {
    try {
      const todoCards = JSON.parse(readFileSync(todoCardsPath, 'utf-8'))
      const todoRouteIds = Array.isArray(todoCards.cards)
        ? todoCards.cards
            .map((card: { route_id?: string }) => card.route_id)
            .filter(Boolean)
        : []

      routes.push(
        ...todoRouteIds.map((routeId: string) => `/todo/${routeId}`),
        ...todoRouteIds.map((routeId: string) => `/compass/${routeId}`)
      )
    } catch {}
  }

  return [...new Set(routes)]
}

const prerenderRoutes = loadPrerenderRoutes()

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: process.env.NODE_ENV !== 'production' },
  modules: ['@nuxtjs/tailwindcss'],
  runtimeConfig: {
    public: {
      githubOwner: process.env.NUXT_PUBLIC_GITHUB_OWNER || '',
      githubRepo: process.env.NUXT_PUBLIC_GITHUB_REPO || '',
      githubRef: process.env.NUXT_PUBLIC_GITHUB_REF || 'main',
      githubReadStatusWorkflow: process.env.NUXT_PUBLIC_GITHUB_READ_STATUS_WORKFLOW || 'read-status.yml'
    }
  },
  app: {
    baseURL: process.env.NUXT_APP_BASE_URL || '/',
    head: {
      title: 'ScholarAIO',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'ScholarAIO read-only static library snapshot' }
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: 'anonymous' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap'
        },
        { rel: 'stylesheet', href: 'https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css' }
      ]
    }
  },
  nitro: {
    port: 5815,
    host: '0.0.0.0',
    prerender: {
      crawlLinks: true,
      failOnError: true,
      routes: prerenderRoutes
    }
  },
  routeRules: {
    '/graph': { redirect: '/explore' },
    '/graph/**': { redirect: '/explore' },
    '/**': { prerender: true }
  },
  compatibilityDate: '2024-04-03'
})
