import os
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'ratonGato.settings'
)

import django
django.setup()

from datamodel.models import Game, Move
from django.contrib.auth.models import User

user_10 = User.objects.get_or_create(id=10)[0]
user_10.username = "Usuario10"
user_10.save()

user_11 = User.objects.get_or_create(id=11)[0]
user_11.username = "Usuario11"
user_11.save()

game = Game(cat_user=user_10)
game.save()

games_one_player = Game.objects.filter(mouse_user=None).order_by("id")
print("Partidas con un único jugador:")
for game_one_player in games_one_player:
    print(" -> " + str(game_one_player))

game = games_one_player[0]
game.mouse_user = user_11
game.save()
print("Partida comenzada - " + str(game))

move = Move(game=game, player=user_10, origin=2, target=11)
move.save()
print("Gato movido a 11 - " + str(game))

move = Move(game=game, player=user_11, origin=59, target=52)
move.save()
print("Ratón movido a 52 - " + str(game))