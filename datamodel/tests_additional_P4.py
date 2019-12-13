"""
@author: Víctor Yrazusta Ibarra
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from . import tests
from datamodel.models import Game, GameStatus, Move


class GameEndTests(tests.BaseModelTest):
    def setUp(self):
        super().setUp()

    def test1(self):
        """ Comprobar que el juego se encuentra activo al empezar """
        game = Game(cat_user=self.users[0])
        game.full_clean()
        game.save()
        self.assertIsNone(game.mouse_user)
        self.assertTrue(game.cat_turn)
        self.assertEqual(game.status, GameStatus.CREATED)
        game.mouse_user = self.users[1]
        game.save()
        self.assertEqual(game.status, GameStatus.ACTIVE)
        self.assertEqual(self.get_array_positions(game), [0, 2, 4, 6, 59])

    def test2(self):
        """ Comprobar que el juego se encuentra activo tras una serie de movimientos """
        game = Game(cat_user=self.users[0])
        game.full_clean()
        game.mouse_user = self.users[1]
        game.cat2 += 9
        game.cat3 += 9
        game.cat4 += 9
        game.mouse -= 9
        game.save()
        self.assertEqual(game.status, GameStatus.ACTIVE)
        self.assertEqual(self.get_array_positions(game), [0, 2+9, 4+9, 6+9, 59-9])

    def test3(self):
        """ Comprobar que el juego se termina correctamente cuando el ratón es encerrado en una esquina """
        game = Game(cat_user=self.users[0])
        game.full_clean()
        game.mouse_user = self.users[1]
        game.cat2 = 54
        game.mouse = 63
        game.save()
        self.assertEqual(game.status, GameStatus.FINISHED)

    def test4(self):
        """ Comprobar que el juego se termina correctamente cuando el ratón es encerrado en un lateral"""
        game = Game(cat_user=self.users[0])
        game.full_clean()
        game.mouse_user = self.users[1]
        game.cat1 = 38
        game.cat2 = 54
        game.mouse = 47
        game.save()
        self.assertEqual(game.status, GameStatus.FINISHED)

    def test5(self):
        """ Comprobar que el juego no se termina cuando el ratón tiene aún una salida"""
        game = Game(cat_user=self.users[0])
        game.full_clean()
        game.mouse_user = self.users[1]
        game.cat1 = 38
        game.cat2 = 52
        game.cat3 = 54
        game.mouse = 45
        game.save()
        self.assertEqual(game.status, GameStatus.ACTIVE)

    def test6(self):
        """ Comprobar que el juego se termina correctamente cuando el ratón está completamente rodeado"""
        game = Game(cat_user=self.users[0])
        game.full_clean()
        game.mouse_user = self.users[1]
        game.cat1 = 36
        game.cat2 = 38
        game.cat3 = 52
        game.cat4 = 54
        game.mouse = 45
        game.save()
        self.assertEqual(game.status, GameStatus.FINISHED)

    def test7(self):
        """ Comprobar que el juego no se termina cuando el ratón ha superado a la mitad de los gatos"""
        game = Game(cat_user=self.users[0])
        game.full_clean()
        game.mouse_user = self.users[1]
        game.cat1 = 34
        game.cat2 = 38
        game.cat3 = 52
        game.cat4 = 54
        game.mouse = 45
        game.save()
        self.assertEqual(game.status, GameStatus.ACTIVE)
    
    def test8(self):
        """ Comprobar que el juego se termina correctamente cuando el ratón ha superado a los gatos"""
        game = Game(cat_user=self.users[0])
        game.full_clean()
        game.mouse_user = self.users[1]
        game.cat1 = 36
        game.cat2 = 38
        game.cat3 = 52
        game.cat4 = 54
        game.mouse = 20
        game.save()
        self.assertEqual(game.status, GameStatus.FINISHED)

