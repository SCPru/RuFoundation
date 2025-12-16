import formatDate from '../util/date-format'

export function makeDate(node: HTMLElement) {
  // hack: mark node as already processed because it was
  if ((node as any)._date) {
    return
  }
  ;(node as any)._date = true
  // end hack

  try {
    const defaultFormatHere = '%H:%M %d.%m.%Y'

    const timestamp = Number.parseInt(node.dataset.timestamp ?? '')
    const format = node.dataset.format || defaultFormatHere

    const date = new Date(timestamp)

    let formatted
    try {
      formatted = formatDate(date, format)
    } catch (e) {
      formatted = formatDate(date, defaultFormatHere)
    }

    node.textContent = formatted
  } catch (e) {
    /* ... */
  }
}
