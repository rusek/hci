# -*- coding: utf-8 -*-

import json
import os
import urlparse
from bottle import Bottle, request, response, template, redirect, static_file, run

STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static')

app = Bottle()
app_state = None
app_request_tokens = {}


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


@app.route('/')
@app.route('/static')
def static_index():
    redirect('/static/')


@app.route('/authorized')
def authorize():
    if request.params.get('error') == 'access_denied':
        return 'Access denied'

    with app_state as state:
        request_token = app_request_tokens.pop(request.params['oauth_token'])
        verifier = request.params['oauth_verifier']
        client = state.make_client(request_token)
        data = client.services.oauth.access_token(oauth_verifier=verifier)
        access_token = data['oauth_token'], data['oauth_token_secret']
        client.token = access_token
        cards = client.services.cards.user()
        user = client.services.users.user()

        for card in cards:
            state.db.setdefault('cards', {})[card['contactless_chip_uid']] = dict(
                user_id=user['id'],
                first_name=user['first_name'],
                last_name=user['last_name'],
                token=access_token,
            )
        state.db.sync()

        return template(u"""
<!DOCTYPE html>
<html>
<head>
    <title>Przyznano dostęp</title>
</head>
<body>

<p>Użytkownik: {{user['first_name']}} {{user['last_name']}}</p>

<p>Karty:</p>

<ul>
    % for card in cards:
    <li>{{card['contactless_chip_uid']}} (kod paskowy: {{card['barcode_number']}})</li>
    % end
</ul>

</body>
</html>
        """, user=user, cards=cards)


@app.route('/register')
def register():
    with app_state as state:
        scheme, netloc, _, _, _ = request.urlparts
        callback_url = urlparse.urlunsplit((scheme, netloc, '/authorized', '', ''))

        client = state.make_client()
        data = client.services.oauth.request_token(
            oauth_callback=callback_url,
            scopes='studies|offline_access|cards|crstests|grades|student_exams'
        )
        token = data['oauth_token'], data['oauth_token_secret']
        redirect_url = client.base_url + 'services/oauth/authorize?oauth_token=' + token[0]
        app_request_tokens[token[0]] = token

        redirect(redirect_url)


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
