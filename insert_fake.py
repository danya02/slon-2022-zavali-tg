from database import *

words = get_words()
data = {}
for round_id in words:
    round = words[round_id]
    for index, word in enumerate(round['words']):
        data[f'{round_id}-{index}-fake'] = word['fake']

team, _ = Team.get_or_create(name='π')
team.memory = data
team.save()