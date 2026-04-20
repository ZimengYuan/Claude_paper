function normalizeBaseUrl(baseUrl) {
  const value = String(baseUrl || '/')
  return value.endsWith('/') ? value : `${value}/`
}

const READ_STATUS_OVERRIDES_KEY = 'scholaraio.readStatusOverrides.v1'
const VALID_READ_STATUSES = new Set(['read', 'unread'])

function readOverrideStore() {
  if (!import.meta.client) return {}

  try {
    const raw = window.localStorage.getItem(READ_STATUS_OVERRIDES_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function writeOverrideStore(store) {
  if (!import.meta.client) return
  window.localStorage.setItem(READ_STATUS_OVERRIDES_KEY, JSON.stringify(store))
}

function normalizeKey(value) {
  const key = String(value || '').trim()
  return key || ''
}

function itemKeys(item) {
  if (typeof item === 'string') return [normalizeKey(item)].filter(Boolean)
  if (item == null || typeof item !== 'object') return []

  return [
    item.route_id,
    item.paper_route_id,
    item.paper_id,
    item.dir_name,
    item.doi,
  ].map(normalizeKey).filter(Boolean)
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

  const getReadStatusOverride = (item) => {
    const store = readOverrideStore()
    for (const key of itemKeys(item)) {
      const value = store[key]?.status
      if (VALID_READ_STATUSES.has(value)) return value
    }
    return ''
  }

  const setReadStatusOverride = (items, status) => {
    if (!VALID_READ_STATUSES.has(status)) return

    const store = readOverrideStore()
    const keys = (Array.isArray(items) ? items : [items]).flatMap(itemKeys)
    const updatedAt = new Date().toISOString()
    for (const key of keys) {
      store[key] = { status, updated_at: updatedAt }
    }
    writeOverrideStore(store)
  }

  const applyReadStatusOverride = (item) => {
    const status = getReadStatusOverride(item)
    return status ? { ...item, read_status: status } : item
  }

  return {
    toUrl,
    fetchJson,
    fetchText,
    getReadStatusOverride,
    setReadStatusOverride,
    applyReadStatusOverride,
  }
}
