import * as React from 'react'
import { Component } from 'react'
import styled from 'styled-components'
import { ArticleFile, deleteFile, fetchArticleFiles, renameFile, uploadFile } from '../api/files'
import Loader from '../util/loader'
import WikidotModal from '../util/wikidot-modal'

interface Props {
  pageId: string
  onClose: () => void
  editable: boolean
}

interface UploadFileRecord {
  file: File
  name: string
  progress: number
  uploading: boolean
  error: string | null
}

interface State {
  loading: boolean
  files?: Array<ArticleFile>
  softLimit?: number
  hardLimit?: number
  softUsed?: number
  hardUsed?: number
  error?: string
  uploadFiles: Array<UploadFileRecord>
  optionsIndex: number | null
  renameIndex: number | null
  renameName: string | null
}

const Styles = styled.div<{ loading?: boolean }>`
  min-height: 600px;

  .w-files-area.loading {
    position: relative;
    min-height: calc(32px + 16px + 16px);
    &::after {
      content: ' ';
      position: absolute;
      background: #0000003f;
      z-index: 0;
      left: 0;
      right: 0;
      top: 0;
      bottom: 0;
    }
    .loader {
      position: absolute;
      left: 16px;
      top: 16px;
      z-index: 1;
    }
  }

  * {
    box-sizing: border-box;
  }

  .w-upload-files {
    margin-top: 32px;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;

    .w-upload-control {
      position: relative;
      border: 2px dashed white;
      border-radius: 8px;
      padding: 8px;
      background: #ddd;
      box-shadow: 0 0 0 3px #ddd;
      font-weight: bold;
      text-align: center;

      input[type='file'] {
        opacity: 0;
        z-index: 999;
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        bottom: 0;
        width: 100%;
        height: 100%;
        cursor: pointer;
      }
    }

    .w-upload-btn {
      background: #446060;
      &:hover {
        background: #517a7a;
      }
      border-radius: 4px;
      color: white;
      font-weight: bold;
      display: inline-block;
      padding: 4px 8px;
      text-decoration: none;
      text-align: center;
    }

    .w-upload-all {
      margin-left: auto;
      margin-right: auto;
      max-width: 140px;
      display: block;
      margin-top: 16px;
    }

    .w-upload-rows {
      margin-top: 32px;
      .w-upload-row {
        padding: 8px 0;
        border-bottom: 1px dotted #ddd;
        &:last-of-type {
          border-bottom: 0;
        }
        .w-upload-info {
          display: flex;
          align-items: center;
          .w-upload-name {
            flex-basis: 40%;
            font-weight: bold;
            padding: 0 4px;
          }
          .w-upload-size,
          .w-upload-type {
            flex-basis: 20%;
            padding: 0 4px;
          }
          .w-upload-btn {
            margin-left: auto;
          }
        }
        .w-upload-progress {
          margin: 4px;
          margin-top: 8px;
          border: 2px solid #ddd;
          padding: 2px;
          border-radius: 999px;

          & > div {
            background: #446060;
            border-radius: 999px;
            height: 5px;
          }
        }
        .w-upload-progress-error {
          margin: 4px;
          margin-top: 8px;
          background: #fee;
          border: 1px dashed #f66;
          padding: 8px;
          color: #f33;
          font-weight: bold;
        }
      }
    }
  }
`

class ArticleFiles extends Component<Props, State> {
  constructor(props) {
    super(props)
    this.state = {
      loading: false,
      uploadFiles: [],
      optionsIndex: null,
      renameIndex: null,
      renameName: null,
    }
  }

  componentDidMount() {
    this.loadFiles()
  }

  async loadFiles() {
    const { pageId } = this.props
    this.setState({ loading: true, error: null })
    try {
      const { files, softLimit, hardLimit, softUsed, hardUsed } = await fetchArticleFiles(pageId)
      this.setState({ loading: false, error: null, files, softLimit, hardLimit, softUsed, hardUsed, optionsIndex: null, renameIndex: null })
    } catch (e) {
      this.setState({ loading: false, error: e.error || 'Ошибка связи с сервером' })
    }
  }

  onClose = e => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (this.props.onClose) this.props.onClose()
  }

  onCloseError = () => {
    this.setState({ error: null })
    this.onClose(null)
  }

  formatSize(size) {
    const sizeKb = 1024
    const sizeMb = 1024 * 1024
    const sizeGb = 1024 * 1024 * 1024

    const roundTo2 = value => Math.round(value * 100) / 100

    if (size < sizeKb) {
      return `${size} б`
    }
    if (size < sizeMb) {
      return `${roundTo2(size / sizeKb)} кб`
    }
    if (size < sizeGb) {
      return `${roundTo2(size / sizeMb)} мб`
    }
    return `${roundTo2(size / sizeGb)} гб`
  }

  onFileChange = e => {
    const uploadFiles = [...this.state.uploadFiles]
    ;[...e.target.files].forEach(file => {
      uploadFiles.push({
        file,
        name: file.name,
        progress: 0,
        uploading: false,
        error: null,
      })
    })
    e.target.value = null
    this.setState({ uploadFiles })
  }

  updateFile(file: UploadFileRecord, props: Partial<UploadFileRecord>) {
    this.state.uploadFiles.forEach(f => {
      if (file.file === f.file) {
        Object.assign(file, props)
      }
    })
    this.setState({ uploadFiles: this.state.uploadFiles })
  }

  async doUpload(file: UploadFileRecord) {
    const { pageId } = this.props
    try {
      await uploadFile(pageId, file.file, file.name, (_, total, loaded) => {
        this.updateFile(file, { progress: loaded / total })
      })
      // file successfully uploaded
      const uploadFiles = this.state.uploadFiles.filter(x => x.file !== file.file)
      this.setState({ uploadFiles })
      this.loadFiles()
    } catch (e) {
      this.updateFile(file, { error: e.error || 'Ошибка загрузки файла', uploading: false })
    }
  }

  onUploadFile = (e, file) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    if (file.uploading) {
      return
    }
    this.updateFile(file, { uploading: true, error: null })
    this.doUpload(file)
  }

  onUploadAll = e => {
    e.preventDefault()
    e.stopPropagation()
    this.state.uploadFiles.forEach(file => {
      if (!file.uploading) {
        this.onUploadFile(null, file)
      }
    })
  }

  renderUpload() {
    const { uploadFiles } = this.state
    return (
      <>
        <div className="w-upload-files">
          <div className="w-upload-control">
            <span>Нажмите, чтобы загрузить файл, или перетащите файлы сюда</span>
            <input type="file" onChange={this.onFileChange} multiple />
          </div>
          {uploadFiles.length ? (
            <div className="w-upload-rows">
              {uploadFiles.map((file, i) => {
                return (
                  <div key={i} className="w-upload-row">
                    <div className="w-upload-info">
                      <span className="w-upload-name">{file.name}</span>
                      <span className="w-upload-type">{file.file.type}</span>
                      <span className="w-upload-size">{this.formatSize(file.file.size)}</span>
                      {!file.uploading ? (
                        <a href="#" className="w-upload-btn" onClick={e => this.onUploadFile(e, file)}>
                          Загрузить
                        </a>
                      ) : null}
                    </div>
                    {file.uploading ? (
                      <>
                        <div className="w-upload-progress">
                          <div style={{ width: `${file.progress * 100}%` }} />
                        </div>
                      </>
                    ) : null}
                    {file.error ? <div className="w-upload-progress-error">Файл не загружен: {file.error}</div> : null}
                  </div>
                )
              })}
              <a href="#" className="w-upload-btn w-upload-all" onClick={this.onUploadAll}>
                Загрузить все
              </a>
            </div>
          ) : null}
        </div>
      </>
    )
  }

  onOptions = (e, i) => {
    e.preventDefault()
    e.stopPropagation()
    if (i === this.state.optionsIndex) {
      this.setState({ optionsIndex: null })
    } else {
      this.setState({ optionsIndex: i })
    }
  }

  onOptionsRename = async (e, i) => {
    const { pageId } = this.props
    e.preventDefault()
    e.stopPropagation()
    this.setState({ renameIndex: i, renameName: this.state.files[i].name })
  }

  onOptionsDelete = async (e, i) => {
    const { pageId } = this.props
    e.preventDefault()
    e.stopPropagation()
    const file = this.state.files[i]
    try {
      this.setState({ loading: true })
      await deleteFile(file.id)
      this.setState({ optionsIndex: null })
      this.loadFiles()
    } catch (e) {
      this.setState({ loading: false, error: e.error || 'Ошибка удаления файла' })
    }
  }

  onCancelRename = () => {
    this.setState({ renameIndex: null, renameName: null })
  }

  onRename = async () => {
    const { pageId } = this.props
    const { files, renameIndex, renameName } = this.state
    try {
      this.setState({ loading: true })
      await renameFile(files[renameIndex].id, renameName)
      this.setState({ optionsIndex: null })
      this.loadFiles()
    } catch (e) {
      this.setState({ loading: false, error: e.error || 'Ошибка переименования файла' })
    }
  }

  onRenameChange = e => {
    this.setState({ renameName: e.target.value })
  }

  render() {
    const { editable, pageId } = this.props
    const { error, loading, files, optionsIndex, hardLimit, hardUsed, softLimit, softUsed, renameIndex, renameName } = this.state
    return (
      <Styles>
        {error && (
          <WikidotModal buttons={[{ title: 'Закрыть', onClick: this.onCloseError }]} isError>
            <p>
              <strong>Ошибка:</strong> {error}
            </p>
          </WikidotModal>
        )}
        {renameIndex != null && (
          <WikidotModal
            buttons={[
              { title: 'Переименовать', onClick: this.onRename },
              { title: 'Отмена', onClick: this.onCancelRename },
            ]}
          >
            <h1>Переименовать</h1>
            <div className="w-rename-modal">
              <table className="form">
                <tbody>
                  <tr>
                    <td>Текущее имя:</td>
                    <td>{files[renameIndex].name}</td>
                  </tr>
                  <tr>
                    <td>Новое имя:</td>
                    <td>
                      <input type="text" value={renameName} onChange={this.onRenameChange} />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </WikidotModal>
        )}
        <a className="action-area-close btn btn-danger" href="#" onClick={this.onClose}>
          Закрыть
        </a>
        <h1>Файлы</h1>
        <div className={`w-files-area ${loading ? 'loading' : ''}`}>
          {loading && <Loader className="loader" />}
          {!!files ? (
            <>
              <p>
                Количество файлов: {files.length}
                <br />
                Общий размер: {this.formatSize(files.reduce((v, f) => v + f.size, 0))}
                {(softLimit > 0 || hardLimit > 0) && (
                  <>
                    <br />
                    Использовано места на сайте:
                    {softLimit > 0 && (
                      <>
                        {' '}
                        {this.formatSize(softUsed)} из {this.formatSize(softLimit)}
                      </>
                    )}
                    {hardLimit > 0 && (
                      <>
                        {` ${softLimit > 0 ? '(' : ''}`}
                        {this.formatSize(hardUsed)} из {this.formatSize(hardLimit)}
                        {`${softLimit > 0 ? ')' : ''}`}
                      </>
                    )}
                  </>
                )}
              </p>
              <table className="table table-striped table-hover page-files">
                <thead>
                  <tr>
                    <th>Имя файла</th>
                    <th>Тип файла</th>
                    <th>Размер</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {files.map((file, i) => {
                    return (
                      <React.Fragment key={i}>
                        <tr id={`file-row-${i}`}>
                          {/* BHL has CSS selector that says tr[id*="file-row"] */}
                          <td>
                            <a href={`/local--files/${pageId}/${encodeURIComponent(file.name)}`} target="_blank">
                              {file.name}
                            </a>
                          </td>
                          <td>{file.mimeType}</td>
                          <td>{this.formatSize(file.size)}</td>
                          <td>
                            <a className="btn btn-primary btn-sm btn-small" href="#" onClick={e => this.onOptions(e, i)}>
                              Опции
                            </a>
                          </td>
                        </tr>
                        {optionsIndex === i ? (
                          <tr className="highlight" id={`file-options-${i}`}>
                            {/* same reasoning for ID as above */}
                            <td />
                            <td />
                            <td />
                            <td colSpan={4} className="options">
                              <a className="btn btn-primary btn-sm btn-small" href="#" onClick={e => this.onOptionsRename(e, i)}>
                                Переименовать
                              </a>
                              &nbsp;
                              <a className="btn btn-primary btn-sm btn-small" href="#" onClick={e => this.onOptionsDelete(e, i)}>
                                Удалить
                              </a>
                            </td>
                          </tr>
                        ) : null}
                      </React.Fragment>
                    )
                  })}
                </tbody>
              </table>
              {editable ? this.renderUpload() : null}
            </>
          ) : null}
        </div>
      </Styles>
    )
  }
}

export default ArticleFiles
