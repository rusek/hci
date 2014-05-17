import json
import os
from bottle import Bottle, response, static_file, run

STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static')

app = Bottle()
app_state = None


def iter_panels():
    with app_state as state:
        panel_index, panel_data = state.panel

    yield panel_data

    prev_panel_index = panel_index
    while True:
        with app_state as state:
            while True:
                panel_index, panel_data = state.panel
                if panel_index != prev_panel_index:
                    break
                state.wait_panel()

        yield panel_data
        prev_panel_index = panel_index


@app.route('/static/<filepath:path>')
@app.route('/static/')
def static(filepath='index.html'):
    return static_file(filepath, root=STATIC_ROOT)


@app.route('/panel-feed')
def panel_feed():
    def gen():
        for panel in iter_panels():
            yield 'data: {}\n\n'.format(json.dumps(panel))

    response.content_type = 'text/event-stream'
    return gen()


def run_server(state):
    global app_state

    app_state = state
    run(app, host='localhost', port=8080, server='cherrypy')
