import { sprintf } from 'sprintf-js'
import { ModuleRateResponse, ratePage } from '../api/rate'
import { showErrorModal } from '../util/wikidot-modal'

async function onClick(e: MouseEvent, pageId: string, vote: number): Promise<ModuleRateResponse> {
  e.preventDefault()
  e.stopPropagation()
  try {
    return await ratePage({ pageId, value: vote })
  } catch (e) {
    showErrorModal(e.error || 'Ошибка связи с сервером')
    throw e
  }
}

function updateRating(number: HTMLElement, votes: HTMLElement, popularity: HTMLElement, control: HTMLElement, votesData: ModuleRateResponse) {
  number.textContent = votesData.voteCount ? sprintf('%.1f', votesData.rating) : '—'
  votes.textContent = sprintf('%d', votesData.voteCount)
  popularity.textContent = sprintf('%d', votesData.popularity)
  control.style.width = `${Math.floor(votesData.rating * 20)}%`
}

export function makeStarsRateModule(node: HTMLElement) {
  if ((node as any)._rateStars) {
    return
  }
  ;(node as any)._rateStars = true

  const pageId = node.dataset.pageId

  const number: HTMLElement = node.querySelector('.w-stars-rate-rating .w-stars-rate-number')
  const votes: HTMLElement = node.querySelector('.w-stars-rate-votes .w-stars-rate-number')
  const popularity: HTMLElement = node.querySelector('.w-stars-rate-votes .w-stars-rate-popularity')
  const rateWrapper: HTMLElement = node.querySelector('.w-stars-rate-stars-wrapper')
  const control: HTMLElement = rateWrapper.querySelector('.w-stars-rate-stars-view')
  const cancel: HTMLElement = node.querySelector('.w-stars-rate-cancel')

  let originalRateWidth = control.style.width
  let rateWith: number = null

  const callback = function (votesData: ModuleRateResponse) {
    updateRating(number, votes, popularity, control, votesData)
    originalRateWidth = control.style.width
    window.postMessage({ type: 'rate_updated' })
  }

  rateWrapper.addEventListener('mousemove', e => {
    const rect = rateWrapper.getBoundingClientRect()
    const total = rect.width
    const offset = e.clientX - rect.x
    const value = Math.round((offset / total) * 10) / 2
    control.style.width = `${Math.floor(value * 20)}%`
    rateWith = value
  })

  rateWrapper.addEventListener('mouseout', () => {
    control.style.width = originalRateWidth
  })

  rateWrapper.addEventListener('click', e => onClick(e, pageId, rateWith).then(callback))
  cancel.addEventListener('click', e => onClick(e, pageId, null).then(callback))
}
