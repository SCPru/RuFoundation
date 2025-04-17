import * as React from 'react';
import { BrowserRouter, Switch, Route } from "react-router-dom";
import Notifications from './notifications';


export default function ReactivePage() {
    const reactiveRoot: HTMLElement = document.querySelector('#reactive-root');
    const config = JSON.parse(reactiveRoot.dataset.config);

    return (
        <BrowserRouter basename='/-'>
            <Switch>
                <Route path='/notifications' render={() => <Notifications {...config} />} />
            </Switch>
        </BrowserRouter>
    );
}
