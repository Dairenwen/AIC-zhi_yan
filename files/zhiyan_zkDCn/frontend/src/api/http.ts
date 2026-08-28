import axios from 'axios'

import { clearStoredAuth, getCsrfToken } from '@/auth/storage'

export interface ApiEnvelope<T> {
  success: boolean
  data: T
  meta?: Record<string, unknown>
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.request.use((config) => {
  const csrfToken = getCsrfToken()
  if (csrfToken && config.method && ['post', 'put', 'patch', 'delete'].includes(config.method)) {
    config.headers.set('X-CSRF-Token', csrfToken)
  }
  if (config.method === 'post' && config.url === '/tasks' && config.data && typeof config.data === 'object' && !config.data.project_id) {
    const projectId = projectContextFromSearch(window.location.search)
    if (projectId) config.data = { ...config.data, project_id: projectId }
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearStoredAuth()
      const requestUrl = String(error.config?.url ?? '')
      if (window.location.pathname !== '/login' && requestUrl !== '/auth/me') {
        const redirect = `${window.location.pathname}${window.location.search}`
        window.location.assign(`/login?redirect=${encodeURIComponent(redirect)}`)
      }
    }
    return Promise.reject(error)
  },
)

export async function getData<T>(url: string, config = {}): Promise<T> {
  const response = await http.get<ApiEnvelope<T>>(url, config)
  return response.data.data
}

export function projectContextFromSearch(search: string): string | null {
  const value = new URLSearchParams(search).get('project')?.trim()
  return value || null
}
