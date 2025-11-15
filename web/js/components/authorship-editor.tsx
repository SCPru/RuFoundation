import * as React from 'react'
import { useCallback, useEffect, useRef, useState, useMemo } from 'react'
import styled from 'styled-components'
import { UserData } from '../api/user'
import UserView from '../util/user-view'

interface IndexedUserData extends UserData {
  index?: number
}

interface Props {
  authors: UserData[]
  allUsers: IndexedUserData[]
  editable?: boolean
  onChange?: (author: UserData[]) => void
}

const AuthorshipEditorContainer = styled.div`
  * {
    box-sizing: border-box;
  }
`

const AuthorsListContainer = styled.div`
  display: flex;
  justify-items: start;
  max-width: 300px;
  flex-wrap: wrap;
`

const Author = styled.div`
  white-space: nowrap;
  background: #eee;
  border-radius: 4px;
  margin: 2px;
  padding: 2px 4px;
  padding-right: 0;
  display: flex;
  color: black;
`

const AuthorDelete = styled.div`
  cursor: pointer;
  margin-left: 4px;
  border-left: 1px solid #aaa;
  padding: 0 4px;
  margin-right: 2px;
  border-radius: 0 2px 2px 0;

  &:hover {
    background: #eaa;
  }

  &:after {
    content: '×';
  }
`

const AuthorshipInputArea = styled.div`
  height: 300px;
  max-height: 300px;
  margin-top: 8px;
  display: flex;
  flex-direction: column;
`

const AuthorInputTitle = styled.div`
  margin-bottom: 4px;
  font: inherit;
`

const UserInput = styled.input`
  width: 100%;
`

const UsersSuggestionList = styled.div`
  border: 1px solid #ccc;
  background: white;
  color: black;
  border-top: 0;
  width: 100%;
  overflow-y: auto;
`

const UserSuggestion = styled.div`
  padding: 4px 8px;
  border-bottom: 1px solid #aaa;
  color: black;
  cursor: pointer;
  &:last-child {
    border-bottom: 0;
  }
  &:hover,
  &.active {
    background: #446060;
    color: white;
  }
`

// TODO: idea by perseiide - to suggest users who made срфтпуы for this article
const AuthorshipEditorComponent: React.FC<Props> = ({ authors, allUsers, editable, onChange }) => {
  const [inputValue, setInputValue] = useState('')
  const [suggestionsOpen, setSuggestionsOpen] = useState(false)
  const [selectedToAdd, setSelectedToAdd] = useState<number>()
  const [authorSet, setAuthorSet] = useState<Set<UserData>>()
  const inputRef = useRef<HTMLInputElement>()
  const suggestionsRef = useRef<HTMLDivElement>()

  // TODO: fix seleced user filtering
  const filteredUsers = useMemo(() => {
    return allUsers
      .reduce((acc, user) => {
        // if (authorSet?.has(user)) return acc  // Maybe
        const idx = user.name.toLowerCase().indexOf(inputValue.toLowerCase())
        if (idx !== -1) acc.push({ ...user, index: idx })
        return acc
      }, [] as IndexedUserData[])
      .sort((a, b) => a.index - b.index || a.name.localeCompare(b.name))
  }, [authorSet, inputValue])

  const onDeleteAuthor = (e: React.MouseEvent, user: UserData) => {
    e.preventDefault()
    e.stopPropagation()

    if (onChange) onChange(authors.filter(x => x.id !== user.id))
  }

  const onInputChange = (e: React.ChangeEvent) => {
    const value = (e.target as HTMLInputElement).value
    if (value.length <= 1) {
      setSelectedToAdd(undefined)
      if (!value.length) {
        setSuggestionsOpen(false)
      }
    }
    if (value.length) {
      setSuggestionsOpen(true)
    }
    setInputValue(value)
  }

  const onInputFocus = () => {
    setSuggestionsOpen(true)
  }

  const onSelectAuthor = (e: React.MouseEvent, userId: number) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }

    if (!onChange) return

    const user = allUsers.find(x => x.id === userId)

    setInputValue('')
    onChange([...authors.filter(x => x.id !== user.id), user as UserData])
  }

  const checkIfInTree = (p: Node) => {
    while (p) {
      if (p === inputRef.current || p === suggestionsRef.current) {
        return true
      }
      p = p.parentNode
    }
    return false
  }

  const onFocusOutside = useCallback((e: FocusEvent | MouseEvent) => {
    if (!checkIfInTree(e.target as Node)) {
      setSuggestionsOpen(false)
    }
  }, [])

  useEffect(() => {
    setAuthorSet(new Set(authors as IndexedUserData[]))
  }, [authors])

  useEffect(() => {
    window.addEventListener('focus', onFocusOutside)
    window.addEventListener('mousedown', onFocusOutside)

    return () => {
      window.removeEventListener('mousedown', onFocusOutside)
      window.removeEventListener('focus', onFocusOutside)
    }
  }, [])

  useEffect(() => {
    if (!suggestionsRef.current) {
      return
    }
    const el = suggestionsRef.current.querySelector(`[data-selector="${selectedToAdd}"]`)
    if (!el) {
      return
    }
    el.scrollIntoView({ block: 'nearest' })
  }, [selectedToAdd])

  const findSelectedUser = () => {
    let currentUserIndex
    for (let i = 0; i < filteredUsers.length; i++) {
      const user = filteredUsers[i]
      if (user.id == selectedToAdd) {
        currentUserIndex = i
        break
      }
    }
    return currentUserIndex
  }

  const onInputKeyDown = (e: React.KeyboardEvent) => {
    let currentUserIndex = findSelectedUser()
    if (e.key === 'Enter' && selectedToAdd && currentUserIndex !== undefined) {
      onSelectAuthor(undefined, selectedToAdd)
      e.preventDefault()
      e.stopPropagation()
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      e.preventDefault()
      e.stopPropagation()

      if (e.key === 'ArrowUp') {
        if (currentUserIndex === undefined && filteredUsers.length > 0) {
          currentUserIndex = filteredUsers.length - 1
        } else if (currentUserIndex) {
          currentUserIndex--
        } else if (currentUserIndex === 0) {
          currentUserIndex = filteredUsers.length - 1
        }
      } else if (e.key === 'ArrowDown') {
        if (currentUserIndex === undefined && filteredUsers.length > 0) {
          currentUserIndex = 0
        } else if (currentUserIndex !== undefined && currentUserIndex < filteredUsers.length - 1) {
          currentUserIndex++
        } else if (currentUserIndex === filteredUsers.length - 1) {
          currentUserIndex = 0
        }
      }

      setSelectedToAdd(currentUserIndex !== undefined ? filteredUsers[currentUserIndex].id : undefined)
    }
  }

  return (
    <AuthorshipEditorContainer>
      <AuthorsListContainer>
        {authors.map(user => (
          <React.Fragment key={user.id}>
            <Author key={user.id}>
              <UserView data={user} />
              {editable && <AuthorDelete onClick={e => onDeleteAuthor(e, user)} />}
            </Author>
          </React.Fragment>
        ))}
      </AuthorsListContainer>
      {editable && (
        <AuthorshipInputArea>
          <AuthorInputTitle>
            Добавить автора:
            <br />
            (начните печатать для поиска по пользователям)
          </AuthorInputTitle>
          <UserInput onChange={onInputChange} type="text" value={inputValue} onFocus={onInputFocus} ref={inputRef} onKeyDown={onInputKeyDown} />
          {!!inputValue.trim().length && !!filteredUsers.length && suggestionsOpen && (
            <UsersSuggestionList ref={suggestionsRef}>
              {filteredUsers.map(user => (
                <React.Fragment key={user.id}>
                  <UserSuggestion
                    data-selector={user.id}
                    key={user.id}
                    className={selectedToAdd === user.id ? 'active' : ''}
                    onClick={e => onSelectAuthor(e, user.id)}
                  >
                    {user.name}
                  </UserSuggestion>
                </React.Fragment>
              ))}
            </UsersSuggestionList>
          )}
        </AuthorshipInputArea>
      )}
    </AuthorshipEditorContainer>
  )
}

export default AuthorshipEditorComponent
