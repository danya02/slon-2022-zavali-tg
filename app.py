from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
import secrets
import os
import re
from werkzeug import serving
from database import *

app = Flask(__name__)
if not os.path.isfile('secret.bin'):
    with open('secret.bin', 'wb') as f:
        f.write(secrets.token_bytes(32))
app.secret_key = open('secret.bin', 'rb').read()

def disable_endpoint_logs():
    """Disable logs for requests to specific endpoints."""

    disabled_endpoints = ('/api/events',)

    parent_log_request = serving.WSGIRequestHandler.log_request

    def log_request(self, *args, **kwargs):
        if not any(re.match(f"{de}$", self.path) for de in disabled_endpoints):
            parent_log_request(self, *args, **kwargs)

    serving.WSGIRequestHandler.log_request = log_request

disable_endpoint_logs()

def get_team():
    """Get the current team from the database."""

    if 'team' not in session:
        return None
    return Team.get_or_none(Team.join_key == session['team'])

@app.before_request
def before_request():
    g.team = get_team()
    g.game = get_game_state()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events')
def get_events():
    return jsonify([])

@app.route('/fakes')
def fake_form():
    return render_template('input_fakes.html')

@app.route('/create-team', methods=['POST'])
def create_team():
    """Create a new team."""
    team = Team.create(name=request.form['team-name'])
    session['team'] = team.join_key
    return redirect(url_for('index'))

@app.route('/api/submit-fakes', methods=['POST'])
def submit_fakes():
    team = get_team()
    if not team:
        return 403, 'Ваша команда не найдена, присоединитесь к одной из команд.'
    for item in request.form.keys():
        team.memory[item] = request.form[item]
    team.save()
    if request.args.get('htmlform'):
        flash('Данные сохранены.')
        return redirect(url_for('fake_form'))

@app.route('/admin')
def admin():
    if request.remote_addr != '127.0.0.1':
        return 'Доступ запрещен.', 403
    return render_template('admin.html')

@app.route('/admin/set-round', methods=['POST'])
def admin_set_round():
    if request.remote_addr != '127.0.0.1':
        return 'Доступ запрещен.', 403
    game = get_game_state()
    game.current_round = request.form['round']
    game.save()
    return jsonify(game.current_round)

@app.route('/admin/set-word', methods=['POST'])
def admin_set_word():
    if request.remote_addr != '127.0.0.1':
        return 403, 'Доступ запрещен.'
    game = get_game_state()
    try:
        word = request.form['word']
        word = int(word)
        if word < 0 or word > len(get_words()[game.current_round]['words']):
            return jsonify(game.current_word_index or ''), 400
        game.current_word_index = word
        game.save()
        return jsonify(game.current_word_index or '')
    except:
        return jsonify(game.current_word_index) or '', 400

@app.route('/admin/get-teams-list')
def admin_get_teams_list():
    if request.remote_addr != '127.0.0.1':
        return 'Доступ запрещен.', 403
    answer = ''
    for team in Team.select():
        answer += f'<li>{team.id}: {team.name} ({team.memory})'
        answer += f'<button class="btn btn-danger" onclick="deleteTeam({team.id})">Удалить</button>'
        answer += '</li>'
    return answer

@app.route('/admin/delete-team', methods=['POST'])
def admin_delete_team():
    if request.remote_addr != '127.0.0.1':
        return 'Доступ запрещен.', 403
    team = Team.get_or_none(Team.id == request.form['team_id'])
    if not team:
        return 'Команда не найдена.', 404
    team.delete_instance()
    return 'ok'

@app.route('/admin/set-game-phase', methods=['POST'])
def admin_set_game_phase():
    if request.remote_addr != '127.0.0.1':
        return 'Доступ запрещен.', 403
    game = get_game_state()
    game.phase = request.form['phase']
    game.save()
    return jsonify(game.phase)