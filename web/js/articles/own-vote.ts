import { ModuleRateResponse, RatingMode, RatingVisibilityMode } from '../api/rate'

export function ownVoteText(hidden: boolean, vote: number | null, mode: RatingMode, visibilityMode: RatingVisibilityMode): string {
  if (!hidden || visibilityMode !== 'hidden' || vote == null) return ''
  const value = mode === 'updown' ? `${vote >= 0 ? '+' : ''}${vote}` : vote.toFixed(1)
  return `Ваша оценка: ${value}`
}

export function updateOwnVote(node: HTMLElement, data: ModuleRateResponse) {
  const label = node.querySelector<HTMLElement>('.w-rate-own-vote')
  const text = ownVoteText(data.ratingHidden, data.ownVote, data.ratingMode, data.ratingVisibilityMode)
  if (label) label.textContent = text
  node.classList.toggle('w-rate-show-own-vote', !!text)
}
