import styled from 'styled-components'

export const Container = styled.div`
  background: ${({ theme }) => theme.windowPadding};
  border: 1px solid ${({ theme }) => theme.windowStrong};
  padding: 8px;
  position: relative;
`

export const TypeName = styled.h2`
  color: ${({ theme }) => theme.foreground};
  font-size: 13px;
  line-height: 16px;
  font-weight: 600;
  padding: 0;
  margin: 0;
`

export const PostFrom = styled.div`
  margin-top: 4px;
`

export const PostContent = styled.div`
  overflow: hidden;
  background: ${({ theme }) => theme.higlightBackground};
  padding: 8px;
  margin-top: 8px;
  border-radius: 4px;

  *,
  *::before,
  *::after {
    box-sizing: content-box;
  }
`

export const PostName = styled.h3`
  margin-top: 4px;
  padding: 0;
  margin-bottom: 0;
  font-size: 13px;
  line-height: 16px;
  font-weight: 600;
`

export const RevisionFields = styled.div`
  background: ${({ theme }) => theme.higlightBackground};
  padding: 8px;
  margin-top: 8px;
  border-radius: 4px;
  display: grid;
  grid-template-columns: 1fr max-content max-content max-content;
`

const RevisionField = styled.div`
  padding: 8px;
`

export const RevisionArticle = styled(RevisionField)``
export const RevisionFlags = styled(RevisionField)``
export const RevisionNumber = styled(RevisionField)``
export const RevisionUser = styled(RevisionField)``

export const RevisionComment = styled.div`
  margin-top: 8px;
  color: ${({ theme }) => theme.uiBorder};
  font-size: 90%;
`

export const RevisionCommentCaption = styled.span`
  font-weight: 500;
  color: ${({ theme }) => theme.uiForeground};
  opacity: 0.9;
`

export const NotificationDate = styled.div`
  position: absolute;
  top: 8px;
  right: 8px;
  color: ${({ theme }) => theme.uiForeground};
  opacity: 0.7;
  font-size: 90%;
`
