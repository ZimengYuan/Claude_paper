function normalizeBaseUrl(baseUrl) {
  const value = String(baseUrl || '/')
  return value.endsWith('/') ? value : `${value}/`
}

export function useStaticSiteData() {
  const runtimeConfig = useRuntimeConfig()
  const baseUrl = normalizeBaseUrl(runtimeConfig.app.baseURL)

  const toUrl = (relativePath) => {
    const cleanPath = String(relativePath || '').replace(/^\/+/, '')
    return `${baseUrl}site-data/${cleanPath}`
  }

  const fetchJson = async (relativePath) => {
    return await $fetch(toUrl(relativePath), { responseType: 'json' })
  }

  const fetchText = async (relativePath) => {
    return await $fetch(toUrl(relativePath), { responseType: 'text' })
  }

  return {
    toUrl,
    fetchJson,
    fetchText,
  }
}
