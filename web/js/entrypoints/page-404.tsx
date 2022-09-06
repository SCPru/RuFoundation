import * as React from 'react';
import { Component } from 'react';


interface Props {
    pageId?: string
}

interface State {
    isCreate: boolean
}


class Page404 extends Component<Props, State> {
    state = {
        isCreate: false,
        bodyRef: null
    };

    onCreate = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({isCreate: true});
        setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 0);
        (window as any)._openNewEditor(() => {
            this.setState({isCreate: false});
        });
    };

    render() {
        const { isCreate } = this.state;
        const { pageId } = this.props;
        if (!isCreate) {
            return (
                <>
                    <p id="404-message">
                        Запрашиваемая вами страница <em>{pageId}</em> не существует.
                    </p>
                    <ul id="create-it-now-link">
                        <li>
                            <a href="#" onClick={this.onCreate}>Создать страницу</a>
                        </li>
                    </ul>
                </>
            )
        }
    }
}


export default Page404