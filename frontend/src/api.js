function getCookie(name) {
  const match = document.cookie.split('; ').find((row) => row.startsWith(name + '='))
  return match ? decodeURIComponent(match.split('=')[1]) : ''
}

export class ApiError extends Error {
  constructor(status, data) {
    super(`API error ${status}`)
    this.status = status
    this.data = data || {}
  }
}

/**
 * Запрос к Django API. body — объект (уйдёт как JSON) или FormData (multipart).
 */
export async function api(path, { method = 'GET', body } = {}) {
  const headers = {}
  let payload
  if (method !== 'GET') headers['X-CSRFToken'] = getCookie('csrftoken')
  if (body instanceof FormData) {
    payload = body
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  const res = await fetch('/api' + path, { method, headers, body: payload, credentials: 'same-origin' })
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(res.status, data)
  return data
}

export const ensureCsrf = () => api('/auth/csrf/')

/** Первое сообщение об ошибке для поля из ответа DRF. */
export function fieldError(errors, name) {
  const value = errors?.[name]
  if (!value) return ''
  return Array.isArray(value) ? value[0] : String(value)
}

/** Общая ошибка формы: non_field_errors, detail или сетевой сбой. */
export function formError(err) {
  if (!(err instanceof ApiError)) return 'Не удалось связаться с сервером. Попробуйте ещё раз.'
  return fieldError(err.data, 'non_field_errors') || err.data.detail || ''
}
