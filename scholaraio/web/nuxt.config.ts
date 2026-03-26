// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: ['@nuxtjs/tailwindcss'],
  app: {
    head: {
      title: 'ScholarAIO',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'ScholarAIO - Academic Paper Management' }
      ],
      link: [
        { rel: 'stylesheet', href: 'https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css' }
      ]
    }
  },
  nitro: {
    port: 5815,
    host: '0.0.0.0'
  },
  compatibilityDate: '2024-04-03'
})
