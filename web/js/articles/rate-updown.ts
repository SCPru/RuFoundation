import { ModuleRateResponse, ratePage, RATING_HIDDEN_TOOLTIP } from '../api/rate'
import { makeCustomTooltips } from '../util/tooltip'
import { showErrorModal } from '../util/wikidot-modal'

async function onClick(e: MouseEvent, pageId: string, vote: number | null): Promise<ModuleRateResponse> {
  e.preventDefault()
  e.stopPropagation()
  try {
    return await ratePage({ pageId, value: vote })
  } catch (e) {
    showErrorModal(e.error || 'Ошибка связи с сервером')
    throw e
  }
}

function updateRating(element: HTMLElement, votesData: ModuleRateResponse) {
  let rating = String(votesData.rating)
  if (votesData.rating >= 0) {
    rating = '+' + rating
  }
  element.innerText = rating
  element.classList.toggle('w-rating-concealed', votesData.ratingHidden)

  const module = element.closest<HTMLElement>('.w-rate-module')
  const wrapper = element.closest<HTMLElement>('.w-rating-visibility')
  if (module) module.dataset.ratingHidden = String(votesData.ratingHidden)
  if (wrapper) {
    wrapper.dataset.tooltip = votesData.ratingHidden ? RATING_HIDDEN_TOOLTIP : ''
    wrapper.classList.toggle('w-rating-hidden', votesData.ratingHidden)
    makeCustomTooltips(wrapper)
  }
}

export function makeUpDownRateModule(node: HTMLElement) {
  if ((node as any)._rate) {
    return
  }
  ;(node as any)._rate = true

  const pageId = node.dataset.pageId!

  const number: HTMLElement = node.querySelector('.number')!
  const rateup: HTMLElement = node.querySelector('.rateup a')!
  const ratedown: HTMLElement = node.querySelector('.ratedown a')!
  const cancel: HTMLElement = node.querySelector('.cancel a')!

  const callback = function (votesData: ModuleRateResponse) {
    updateRating(number, votesData)
    window.postMessage({ type: 'rate_updated' })
  }

  rateup.addEventListener('click', e => onClick(e, pageId, 1).then(callback))
  ratedown.addEventListener('click', e => onClick(e, pageId, -1).then(callback))
  cancel.addEventListener('click', e => onClick(e, pageId, null).then(callback))
}
