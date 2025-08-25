import React from 'react'

export function highlightWords(text: string, words: Array<string>): React.ReactNode {
  const ranges: Array<{ start: number; end: number }> = []
  const searchText = text.toLowerCase()
  const searchWords = words.map(x => x.toLowerCase()).filter((x, i, a) => a.indexOf(x) === i)
  searchWords.forEach(word => {
    const allPositions = findAll(searchText, word)
    allPositions.forEach(pos => {
      ranges.push({ start: pos, end: pos + word.length })
    })
  })
  if (!ranges.length) {
    return text
  }
  ranges.sort((a, b) => a.start - b.start)
  for (let i = 0; i < ranges.length - 1; i++) {
    if (ranges[i + 1].start < ranges[i].end) {
      ranges[i].end = ranges[i + 1].end
      ranges.splice(i + 1, 1)
      i--
    }
  }
  const results: Array<React.ReactNode> = []
  for (let i = 0; i <= ranges.length; i++) {
    if (i === ranges.length) {
      results.push(<React.Fragment key={i}>{text.substring(ranges[ranges.length - 1].end)}</React.Fragment>)
      break
    }
    results.push(<React.Fragment key={`pre-${i}`}>{text.substring(i ? ranges[i - 1].end : 0, ranges[i].start)}</React.Fragment>)
    results.push(
      <span className="highlight" key={i}>
        {text.substring(ranges[i].start, ranges[i].end)}
      </span>,
    )
  }
  return results
}

function findAll(text: string, word: string): Array<number> {
  // returns all positions of the specified word "p" in the string "s".
  // to-do: detect if words are part of other words, and don't treat them as separate.
  let i = text.indexOf(word)
  const positions: Array<number> = []
  while (i !== -1) {
    positions.push(i)
    i = text.indexOf(word, i + 1)
  }
  return positions
}
