from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, g
import secrets
import os
import re
from werkzeug import serving
from database import *
import database
import random

DO_SHUFFLE = True

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
    g.str = str
    g.database = database

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/events')
def get_events():
    if 'admin' in request.headers['referer']:
        return jsonify({})
    return jsonify(get_game_state().__data__)


@app.route('/create-team', methods=['POST'])
def create_team():
    """Create a new team."""
    if g.game.phase != 'waiting': return redirect(url_for('index'))
    team = Team.create(name=request.form['team-name'])
    session['team'] = team.join_key
    return redirect(url_for('index'))

@app.route('/fakes')
def fake_form():
    if g.game.phase != 'write-fake': return redirect(url_for('index'))
    if g.team is None: return 'Вы не в команде, <a href="/">нужно создать ее</a>'
    round = g.game.current_round
    words = []
    data = get_words()
    round = data[round]
    for index, word in enumerate(round['words']):
        words.append((index, word['text']))
    return render_template('input_fakes.html', words_list=words, round=round, str=str)

@app.route('/api/submit-fakes', methods=['POST'])
def submit_fakes():
    if g.game.phase != 'write-fake': return redirect(url_for('index'))
    team = get_team()
    if not team:
        return 403, 'Ваша команда не найдена, присоединитесь к одной из команд.'
    for item in request.form:
        print(item, request.form[item])
        team.memory[item] = request.form[item]
    team.save()
    if request.args.get('htmlform'):
        flash('Данные сохранены.')
        return redirect(url_for('fake_form'))
    else:
        return 'ok'


@app.route('/guess')
def guess_page():
    if g.game.phase != 'guess-fake-for-word': return redirect(url_for('index'))
    if g.team is None: return 'Вы не в команде, <a href="/">нужно создать ее</a>'
    round = g.game.current_round
    words = []
    data = get_words()
    round = data[round]['words']
    word = round[g.game.current_word_index]
    word_text = word['text']
    correct_answer = word['definition']
    fakes = [correct_answer]
    answers = ['truth']

    for team in Team.select():
        if not team.memory.get(f'{g.game.current_round}-{g.game.current_word_index}-fake'):
            team.memory[f'{g.game.current_round}-{g.game.current_word_index}-fake'] = "(обманка не отправлена)"
            team.save()
        fakes.append(team.memory[f'{g.game.current_round}-{g.game.current_word_index}-fake'])
        answers.append(f'fake-{team.id}')

    randomer = random.Random()
    randomer.seed(word_text)
    if DO_SHUFFLE:
        randomer.shuffle(fakes)
    randomer.seed(word_text)
    if DO_SHUFFLE:
        randomer.shuffle(answers)
    
    their_answer = team.memory.get(f'{g.game.current_round}-{g.game.current_word_index}-guess')
    print(their_answer)

    return render_template('guess_fake.html', word=word_text, fakes=enumerate(fakes), answers=answers, their_answer=their_answer)



@app.route('/api/submit-guess', methods=['POST'])
def submit_guess():
    if g.game.phase != 'guess-fake-for-word': return redirect(url_for('index'))
    if g.team is None: return 'Вы не в команде, <a href="/">нужно создать ее</a>'

    try:
        int(request.form['guess'])
    except ValueError:
        return 'Некорректный ответ', 400

    fakes = ['truth']
    for team in Team.select():
        fakes.append(f'fake-{team.id}')

    data = get_words()
    round = data[g.game.current_round]['words']
    word = round[g.game.current_word_index]
    word_text = word['text']


    randomer = random.Random()
    randomer.seed(word_text)
    if DO_SHUFFLE:
        randomer.shuffle(fakes)

    their_guess = fakes[int(request.form['guess'])]
    g.team.memory[f'{g.game.current_round}-{g.game.current_word_index}-guess'] = their_guess
    g.team.save()
    if request.args.get('htmlform'):
        flash(f'Данные сохранены: ваш выбор - строка {int(request.form["guess"])+1}.')
        return redirect(url_for('guess_page'))
    else:
        return 'ok'




@app.route('/results')
def results_page():
    if g.game.phase != 'results': return redirect(url_for('index'))
    if g.team is None: return 'Вы не в команде, <a href="/">нужно создать ее</a>'
    data = get_words()
    round = data[g.game.current_round]['words']
    word = round[g.game.current_word_index]['text']
    correct_answer = round[g.game.current_word_index]['definition']
    fakes = []
    for team in Team.select():
        fakes.append( (team.name, team.memory.get(f'{g.game.current_round}-{g.game.current_word_index}-fake', "(обманка не отправлена)")) )

    return render_template('results-page.html', word=word, correct_answer=correct_answer, fakes=fakes)





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
        return 'Доступ запрещен.', 403
    game = get_game_state()
    try:
        word = request.form['word']
        word = int(word)
        if word < 0 or word > len(get_words()[game.current_round]['words']):
            return str(game.current_word_index), 400
        game.current_word_index = word
        game.save()
        return str(game.current_word_index)
    except:
        return str(game.current_word_index), 400

@app.route('/admin/get-teams-list')
def admin_get_teams_list():
    if request.remote_addr != '127.0.0.1':
        return 'Доступ запрещен.', 403
    answer = '<ul class="list-unstyled">'
    for team in Team.select():
        answer += f'<li>{team.id}: {team.name} ({team.memory})'
        answer += f'<button class="btn btn-danger m-2" onclick="deleteTeam({team.id})">Удалить</button>'
        answer += '</li>'
    answer += '</ul>'
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

@app.route('/admin/get-fakes-list')
def admin_get_fakes_list():
    if request.remote_addr != '127.0.0.1':
        return 'Доступ запрещен.', 403
    return render_template('results-text.html')

@app.route('/admin/get-fake-submissions-list')
def admin_get_submitted_fakes_list():
    if request.remote_addr != '127.0.0.1':
        return 'Доступ запрещен.', 403
    
    data = get_words()
    round = data[g.game.current_round]['words']
    word = round[g.game.current_word_index]['text']
    answer = f'<p>Fakes for word {word}:</p>'

    answer += '<ul class="list-unstyled">'
    

    for team in Team.select():
        their_fake = team.memory.get(f'{g.game.current_round}-{g.game.current_word_index}-fake', '(no fake submitted)')
        answer += f'<li>{team.id}. {team.name}: {their_fake}'
        answer += f'<button class="btn btn-danger m-2" onclick="purgeFake({team.id}, `{g.game.current_round}-{g.game.current_word_index}-fake`)">Очистить</button>'
        answer += '</li>'

    answer += '</ul>'
    return answer

@app.route('/admin/purge-fake', methods=['POST'])
def admin_purge_fake():
    if request.remote_addr != '127.0.0.1':
        return 'Доступ запрещен.', 403
    team = Team.get_or_none(Team.id == request.form['team_id'])
    if not team:
        return 'Команда не найдена.', 404
    team.memory[f'{g.game.current_round}-{g.game.current_word_index}-fake'] = '(обманка стерта администратором)'
    team.save()
    return 'ok'