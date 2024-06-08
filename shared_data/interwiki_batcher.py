import logging
import multiprocessing
import threading
import time
import queue
import requests
import json


REQUESTS_PER_SECOND = 1


# These default values are used in dev server.
# When running via multiprocessing, this should be replaced with Manager by calling init() before forking.
manager = None
state = None
lock = None


def fetch_batch(urls):
    urls = list(urls)

    queries = [{
        'query': """
        query {
            sites {
                language
                url
                type
                displayName
            }
        }
        """
    }]

    for url in urls:
        queries.append({
            'query': """
            query InterwikiQuery($url: URL!) {
              page(url: $url) {
                translations {
                  url
                }
                translationOf {
                  url
                  translations {
                    url
                  }
                }
              }
            }
            """,
            'variables': {
                'url': url
            }
        })

    base_result = requests.post(
        'https://api.crom.avn.sh/graphql',
        data=json.dumps(queries),
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        timeout=10
    ).json()

    sites_response = base_result[0]
    response_by_url = dict()
    for i, url in enumerate(urls):
        page_response = dict(base_result[i+1])
        # see if we need to merge either data or errors
        if 'errors' in sites_response:
            page_response['errors'] = (page_response.get('errors') or []) + sites_response['errors']
        if 'data' in sites_response and isinstance(sites_response['data'], dict):
            page_response['data'] = {**(page_response.get('data') or {}), **sites_response['data']}
        response_by_url[url] = page_response

    return response_by_url


def process_batches():
    global client_requests

    while True:
        with lock:
            current_state = dict(state)
            state.clear()

        if current_state:
            logging.info('InterWiki Batch: %s' % repr(list(current_state.keys())))
            try:
                response_by_url = fetch_batch(current_state.keys())
                for url, response_queues in current_state.items():
                    for response_queue in response_queues:
                        response_queue.put(response_by_url[url])
            except Exception as e:
                logging.error('InterWiki: Failed to process batch:', exc_info=True)
                for url, response_queues in current_state.items():
                    for response_queue in response_queues:
                        response_queue.put({
                            'data': None,
                            'errors': [{
                                'message': str(e.args[0])
                            }]
                        })

        time.sleep(1 / REQUESTS_PER_SECOND)


def query_interwiki(url, timeout=10):
    global state, lock, manager

    response_queue = manager.Queue(1)

    with lock:
        if url in state:
            state[url].append(response_queue)
        else:
            state[url] = manager.list([response_queue])

    try:
        result = response_queue.get(block=True, timeout=timeout)
    except queue.Empty:
        raise RuntimeError('InterWiki: unable to fetch translations in %.2f seconds' % timeout)

    errors = result.get('errors', [])
    if errors:
        raise RuntimeError('InterWiki: Error: %s' % errors[0]['message'])
    else:
        return result['data']


def init():
    global state, lock, manager

    manager = multiprocessing.Manager()
    lock = manager.RLock()
    state = manager.dict()

    t = threading.Thread(target=process_batches, daemon=True)
    t.start()
