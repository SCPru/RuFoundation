import * as React from 'react'
import useConstCallback from './const-callback'

interface Props {
  maxPages: number
  page: number
  onChange: (nextPage: number) => void
}

const Pagination: React.FC<Props> = ({ page, maxPages, onChange }) => {
  const aroundPages = 2
  const leftFrom = 1
  let leftTo = leftFrom + 1

  if (page < aroundPages * 2 + 1) {
    leftTo = aroundPages + 1
  }

  if (leftTo > maxPages) {
    leftTo = maxPages
  }

  const rightTo = maxPages
  let rightFrom = Math.max(leftTo + 1, rightTo - 1)

  if (page > rightTo - (aroundPages * 2 + 1)) {
    rightFrom = Math.max(leftTo + 1, maxPages - (aroundPages + 1))
  }

  const centerFrom = Math.max(leftTo + 1, page - aroundPages)
  const centerTo = Math.min(rightFrom - 1, page + aroundPages)

  const showLeftDots = centerFrom > leftTo + 1
  const showRightDots = centerTo < rightFrom - 1

  const leftPages = []
  const centerPages = []
  const rightPages = []

  for (let i = leftFrom; i <= leftTo; i++) {
    if (i === page) {
      leftPages.push(
        <span key={i} className="target current">
          {i}
        </span>,
      )
    } else {
      leftPages.push(
        <span key={i} className="target">
          <a href="#" onClick={e => onClick(e, i)}>
            {i}
          </a>
        </span>,
      )
    }
  }

  for (let i = centerFrom; i <= centerTo; i++) {
    if (i === page) {
      centerPages.push(
        <span key={i} className="target current">
          {i}
        </span>,
      )
    } else {
      centerPages.push(
        <span key={i} className="target">
          <a href="#" onClick={e => onClick(e, i)}>
            {i}
          </a>
        </span>,
      )
    }
  }

  for (let i = rightFrom; i <= rightTo; i++) {
    if (i === page) {
      rightPages.push(
        <span key={i} className="target current">
          {i}
        </span>,
      )
    } else {
      rightPages.push(
        <span key={i} className="target">
          <a href="#" onClick={e => onClick(e, i)}>
            {i}
          </a>
        </span>,
      )
    }
  }

  const onClick = useConstCallback((e, nextPage) => {
    e.preventDefault()
    e.stopPropagation()
    onChange(nextPage)
  })

  return (
    <div className="pager">
      <span className="pager-no">
        страница&nbsp;{page}&nbsp;из&nbsp;{maxPages}
      </span>
      {page > 1 && (
        <span className="target">
          <a href="#" onClick={e => onClick(e, page - 1)}>
            &laquo;&nbsp;предыдущая
          </a>
        </span>
      )}
      {leftPages}
      {showLeftDots && <span className="dots">...</span>}
      {centerPages}
      {showRightDots && <span className="dots">...</span>}
      {rightPages}
      {page < maxPages && (
        <span className="target">
          <a href="#" onClick={e => onClick(e, page + 1)}>
            следующая&nbsp;&raquo;
          </a>
        </span>
      )}
    </div>
  )
}

export default Pagination
