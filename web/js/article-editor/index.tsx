import * as React from 'react'
import { Component } from 'react'


interface Props {
    pageId: string
    isNew?: boolean
    onCancel?: () => void
}

interface State {
    title: string
    source: string
}


function guessTitle(pageId) {
    const pageIdSplit = pageId.split(':', 1);
    if (pageIdSplit.length === 2)
        pageId = pageIdSplit[1];
    else pageId = pageIdSplit[0];

    let result = '';
    let brk = true;
    for (let i = 0; i < pageId.length; i++) {
        let char = pageId[i];
        if (char === '-') {
            if (!brk) {
                result += ' ';
            }
            brk = true;
            continue;
        }
        if (brk) {
            char = char.toUpperCase();
            brk = false;
        } else {
            char = char.toLowerCase();
        }
        result += char;
    }
    return result;
}


class ArticleEditor extends Component<Props, State> {
    constructor(props) {
        super(props);
        this.state = {
            title: guessTitle(props.pageId),
            source: ''
        }
    }

    componentDidMount() {
        if (!this.props.isNew) {
            // load existing source. not yet
        }
    }

    onSubmit = () => {

    };

    onCancel = () => {
        if (this.props.onCancel)
            this.props.onCancel()
    };

    onChange = (e) => {
        // @ts-ignore
        this.setState({[e.target.name]: e.target.value})
    };

    render() {
        const { title, source } = this.state;
        return (
            <div>
                <h1>Создать страницу</h1>
                <form id="edit-page-form" onSubmit={this.onSubmit}>
                    <table className="form" style={{ margin: '0.5em auto 1em 0' }}>
                        <tbody>
                        <tr>
                            <td>Заголовок страницы:</td>
                            <td>
                                <input id="edit-page-title" value={title} onChange={this.onChange} name="title" type="text" size={35} maxLength={128} style={{ fontWeight: 'bold', fontSize: '130%' }} />
                            </td>
                        </tr>
                        </tbody>
                    </table>
                    <div>
                        <textarea id="edit-page-textarea" value={source} onChange={this.onChange} name="source" rows={20} cols={60} style={{ width: '95%' }} />
                    </div>
                    <div className="buttons alignleft">
                        <input id="edit-cancel-button" className="btn btn-danger" type="button" name="cancel" value="Отмена" onClick={this.onCancel} />
                        <input id="edit-save-button" className="btn btn-primary" type="button" name="save" value="Сохранить" onClick={this.onSubmit} />
                    </div>
                </form>
            </div>
        )
    }
}


export default ArticleEditor