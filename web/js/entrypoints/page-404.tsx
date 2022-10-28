import * as React from 'react';
import { Component } from 'react';


interface Props {
    pageId?: string
    pathParams?: { [key: string]: string }
}

interface State {
    isCreate: boolean
}


class Page404 extends Component<Props, State> {
    constructor(props) {
        super(props)
        this.state = {
            isCreate: !!this.props.pathParams['edit'],
        };
    }

    onCreate = (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.setState({isCreate: true});
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
        } else {
            return <></>
        }
    }
}


export default Page404