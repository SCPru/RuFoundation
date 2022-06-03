import {getCookie} from "./cookie-util";

interface WRequestInit extends RequestInit {
    sendJson?: boolean
    headers?: Record<string, string>
    body?: any
}

export class APIError extends Error {
    error: string;
    fields?: Record<string, string>;
    exception?: Error;
    status: number;

    constructor(message: string, status: number, fields?: Record<string, string>, exception?: Error) {
        super(message);
        Object.setPrototypeOf(this, APIError.prototype);
        this.error = message;
        this.status = status;
        this.fields = fields;
        this.exception = exception;
    }
}

const readErrorFromBody = (e: Response): Promise<APIError | null> => {
    return new Promise(resolve => {
        if (e.body) {
            const r = e.body.getReader();
            const readAll = (r: ReadableStreamDefaultReader<Uint8Array>, c: (result: string) => void) => {
                const readMore = (s: string) => {
                    r.read().then(({value, done}) => {
                        if (!value) {
                            c(s);
                            return;
                        }
                        const ss = String.fromCharCode.apply(String, Array.from(value));
                        s += ss;
                        if (done) {
                            c(s);
                        } else {
                            readMore(s);
                        }
                    })
                };
                readMore('');
            };

            readAll(r, (s: string) => {
                try {
                    const j = JSON.parse(s) || {};
                    const e = j.error || null;
                    const fields = j.fields || null;
                    if (e) {
                        resolve(new APIError(e.charAt(0).toUpperCase() + e.substr(1), e.status, fields, null));
                        return;
                    }
                    resolve(null);
                } catch (e) {
                    resolve(null);
                }
            });
        } else {
            resolve(null);
        }
    });
};

export async function wFetch<T>(url: string, props?: WRequestInit): Promise<T> {
    props = Object.assign({}, props);

    const headers = (props && props.headers) || {};
    headers['X-CSRFToken'] = getCookie("csrftoken");
    if (props.sendJson) {
        headers['Content-Type'] = 'application/json';
        if (typeof props.body !== 'string') {
            props.body = JSON.stringify(props.body);
        }
    }

    props.headers = headers;

    let rsp, j;
    try {
        rsp = await fetch(url, props);
        j = await rsp.json();
    } catch (e) {
        const error = await readErrorFromBody(e);
        throw new APIError(error.error || 'Ошибка чтения ответа', e.status || 0, error.fields || null, null);
    }
    if (!rsp.ok) {
        throw new APIError(j.error, rsp.status, j.fields || null, null);
    }
    return j as T;
}
