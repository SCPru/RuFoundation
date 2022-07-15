import * as React from 'react';
import { Component } from 'react';
import {UserData} from "../api/user";


interface Props {
    user: UserData
}

interface State {
    isOpen: boolean
}


class PageLoginStatus extends Component<Props, State> {
    state: State = {
        isOpen: false
    };

    menuRef: any = null;

    componentDidMount() {
        window.addEventListener('click', this.onPageClick);
    }

    componentWillUnmount() {
        window.removeEventListener('click', this.onPageClick);
    }

    onPageClick = (e) => {
        let p = e.target;
        while (p) {
            if (p === this.menuRef) {
                return;
            }
            p = p.parentNode;
        }
        this.setState({ isOpen: false });
    };

    toggleMenu = (e) => {
        e.preventDefault();
        e.stopPropagation();

        this.setState({ isOpen: !this.state.isOpen });
    };

    render() {
        const { user } = this.props;
        const { isOpen } = this.state;

        if (user.type === 'anonymous') {
            return (
                <>
                    <a href="/-/register">Создать учётную запись</a> или <a href="/-/login">Вход</a>
                </>
            );
        } else {
            return (
                <>
                    <span className="printuser">
                        <a href={`/-/users/${user.username}`}>
                            <img className="small" src={user.avatar} alt={user.username} />
                        </a>
                        {user.username}
                    </span> | <a id="my-account" href={`/-/profile`}>
                        Мой профиль
                    </a>
                    <a id="account-topbutton" href="#" onClick={this.toggleMenu}>▼</a>
                    { isOpen && <div id="account-options" ref={r => this.menuRef = r} style={{ display: 'block' }}>
                        <ul>
                            <li><a href={`/-/profile/edit`}>Настройки</a></li>
                            <li><a href={`/-/logout`}>Выход</a></li>
                        </ul>
                    </div> }
                </>
            )
        }
    }

}


export default PageLoginStatus