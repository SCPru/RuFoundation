import { getCookie } from './cookie-util'

export type WRequestUploadProgressHandler = (lengthComputable: boolean, total: number, loaded: number) => void

interface WRequestInit extends RequestInit {
  sendJson?: boolean
  headers?: Record<string, string>
  body?: any
  backend?: 'fetch' | 'xhr'
  uploadProgressHandler?: WRequestUploadProgressHandler
}

export class APIError extends Error {
  error: string
  fields?: Record<string, string>
  exception?: Error
  status: number

  constructor(message: string, status: number, fields?: Record<string, string>, exception?: Error) {
    super(message)
    Object.setPrototypeOf(this, APIError.prototype)
    this.error = message
    this.status = status
    this.fields = fields
    this.exception = exception
  }
}

const readErrorFromBody = (e: Response): Promise<APIError | null> => {
  return new Promise(resolve => {
    if (e.body) {
      const r = e.body.getReader()
      const readAll = (r: ReadableStreamDefaultReader<Uint8Array>, c: (result: string) => void) => {
        const readMore = (s: string) => {
          r.read().then(({ value, done }) => {
            if (!value) {
              c(s)
              return
            }
            const ss = String.fromCharCode.apply(String, Array.from(value))
            s += ss
            if (done) {
              c(s)
            } else {
              readMore(s)
            }
          })
        }
        readMore('')
      }

      readAll(r, (s: string) => {
        try {
          const j = JSON.parse(s) || {}
          const e = j.error || null
          const fields = j.fields || null
          if (e) {
            resolve(new APIError(e.charAt(0).toUpperCase() + e.substr(1), e.status, fields, undefined))
            return
          }
          resolve(null)
        } catch (e) {
          resolve(null)
        }
      })
    } else {
      resolve(null)
    }
  })
}

export async function wFetch<T>(url: string, props?: WRequestInit): Promise<T> {
  props = Object.assign({}, props)

  const headers = (props && props.headers) || {}
  headers['X-CSRFToken'] = getCookie('csrftoken')
  if (props.sendJson) {
    headers['Content-Type'] = 'application/json'
    if (typeof props.body !== 'string') {
      props.body = JSON.stringify(props.body)
    }
  }

  props.headers = headers

  let rsp, j
  try {
    rsp = await doFetch(url, props)
    j = await rsp.json()
  } catch (e) {
    const error: any = (await readErrorFromBody(e)) || {}
    throw new APIError(error.error || 'Ошибка чтения ответа', e.status || 0, error.fields || null, undefined)
  }
  if (!rsp.ok) {
    throw new APIError(j.error, rsp.status, j.fields || null, undefined)
  }
  return j as T
}

async function doFetch(url: string, props?: WRequestInit): Promise<Response> {
  props = Object.assign({}, props)
  if (!props.backend || props.backend === 'fetch') return fetch(url, props)
  // do XMLHTTPRequest but pretend it's a fetch
  const xhr = new XMLHttpRequest()
  return new Promise<Response>((resolve, reject) => {
    xhr.open(props.method || 'GET', url)
    const headers = props.headers || {}
    Object.getOwnPropertyNames(headers).forEach(k => {
      xhr.setRequestHeader(k, encodeURIComponent(headers[k]))
    })
    xhr.upload.addEventListener('progress', e => {
      if (props.uploadProgressHandler) {
        props.uploadProgressHandler(e.lengthComputable, e.total, e.loaded)
      }
    })
    xhr.addEventListener('load', () => {
      if (xhr.readyState === 4) {
        const response: Response = {
          headers: new Headers({}),
          ok: true,
          redirected: false,
          status: xhr.status,
          statusText: xhr.statusText,
          type: 'basic',
          url,
          clone() {
            return Object.assign({}, response)
          },
          body: new ReadableStream({
            start(controller) {
              const chunkEncoder = new TextEncoder()
              controller.enqueue(chunkEncoder.encode(xhr.response))
              controller.close()
            },
          }),
          bodyUsed: false,
          async arrayBuffer(): Promise<ArrayBuffer> {
            const chunkEncoder = new TextEncoder()
            return chunkEncoder.encode(xhr.response).buffer as ArrayBuffer
          },
          async blob(): Promise<Blob> {
            return new Blob([xhr.response])
          },
          async formData(): Promise<FormData> {
            throw new DOMException('Not supported')
          },
          async json(): Promise<any> {
            return JSON.parse(xhr.responseText)
          },
          async text(): Promise<string> {
            return xhr.responseText
          },
          async bytes(): Promise<Uint8Array> {
            const chunkEncoder = new TextEncoder()
            return chunkEncoder.encode(xhr.response)
          },
        }
        if (response.status >= 200 && response.status <= 299) {
          resolve(response)
        } else {
          reject(response)
        }
      }
    })
    xhr.addEventListener('error', reject)
    xhr.send(props.body)
  })
}
