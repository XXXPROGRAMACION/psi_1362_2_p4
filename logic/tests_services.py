"""
@author: rlatorre
"""

import re
from decimal import Decimal

from django.contrib.auth.models import User
from django.db.models import Max, Q
from django.test import Client, TestCase
from django.urls import reverse

from datamodel import constants
from datamodel.models import Counter, Game, GameStatus, Move
from datamodel.tests import BaseModelTest

from . import forms

# Tests classes:
# - LogInOutServiceTests
# - SignupServiceTests
# - CounterServiceTests
# - LogInOutCounterServiceTests
# - CreateGameServiceTests
# - JoinGameServiceTests
# - SelectGameServiceTests
# - PlayServiceTests
# - MoveServiceTests

TEST_USERNAME_1 = "testUserMouseCatBaseTest_1"
TEST_PASSWORD_1 = "hskjdhfhw"
TEST_USERNAME_2 = "testUserMouseCatBaseTest_2"
TEST_PASSWORD_2 = "kj83jfbhg"

USER_SESSION_ID = "_auth_user_id"

LANDING_PAGE = "landing"
LANDING_TITLE = r"<h1>Service catalog</h1>|<h1>Servicios</h1>"

ANONYMOUSE_ERROR = "Anonymous required"
ERROR_TITLE = "<h1>Error</h1>"

LOGIN_SERVICE = "login"
LOGIN_ERROR = "login_error"
LOGIN_TITLE = "<h1>Login</h1>"

LOGOUT_SERVICE = "logout"

SIGNUP_SERVICE = "signup"
SIGNUP_ERROR_PASSWORD = "signup_error1"
SIGNUP_ERROR_USER = "signup_error2"
SIGNUP_ERROR_AUTH_PASSWORD = "signup_error3"
SIGNUP_TITLE = r"<h1>Signup user</h1>|<h1>Alta de usuarios</h1>"

COUNTER_SERVICE = "counter"
COUNTER_SESSION_VALUE = "session_counter"
COUNTER_GLOBAL_VALUE = "global_counter"
COUNTER_TITLE = r"<h1>Request counters</h1>|<h1>Contadores de peticiones</h1>"

CREATE_GAME_SERVICE = "create_game"

JOIN_GAME_SERVICE = "join_game"
JOIN_GAME_ERROR_NOGAME = "join_game_error"
JOIN_GAME_TITLE = r"<h1>Join game</h1>|<h1>Unirse a juego</h1>"

CLEAN_SERVICE = "clean_db"
CLEAN_TITLE = r"<h1>Clean orphan games</h1>|<h1>Borrar juegos huérfanos</h1>"

SELECT_GAME_SERVICE = "select_game"
SELECT_GAME_ERROR_NOCAT = "select_game_error1"
SELECT_GAME_ERROR_NOMOUSE = "select_game_error2"
SELECT_GAME_TITLE = r"<h1>Select game</h1>|<h1>Seleccionar juego</h1>"

SHOW_GAME_SERVICE = "show_game"
PLAY_GAME_MOVING = "play_moving"
PLAY_GAME_WAITING = "play_waiting"
SHOW_GAME_TITLE = r"<h1>Play</h1>|<h1>Jugar</h1>"

MOVE_SERVICE = "move"

SERVICE_DEF = {
    LANDING_PAGE: {
        "title": LANDING_TITLE,
        "pattern": r"<span class=\"username\">(?P<username>\w+)</span>"
    },
    ANONYMOUSE_ERROR: {
        "title": ERROR_TITLE,
        "pattern": r"Action restricted to anonymous users|Servicio restringido a usuarios anónimos"
    },
    LOGIN_SERVICE: {
        "title": LOGIN_TITLE,
        "pattern": r"Log in to continue:|Autenticarse para continuar:"
    },
    LOGIN_ERROR: {
        "title": LOGIN_TITLE,
        "pattern": r"Username/password is not valid|Usuario/clave no válidos"
    },
    SIGNUP_ERROR_PASSWORD: {
        "title": SIGNUP_TITLE,
        "pattern": r"Password and Repeat password are not the same|La clave y su repetición no coinciden"
    },
    SIGNUP_ERROR_USER: {
        "title": SIGNUP_TITLE,
        "pattern": r"A user with that username already exists|Usuario duplicado"
    },
    SIGNUP_ERROR_AUTH_PASSWORD: {
        "title": SIGNUP_TITLE,
        "pattern": r"(?=.*too short)(?=.*at least 6 characters)(?=.*too common)"
    },
    COUNTER_SESSION_VALUE: {
        "title": COUNTER_TITLE,
        "pattern": r"Counter session: <b>(?P<session_counter>\d+)</b>"
    },
    COUNTER_GLOBAL_VALUE: {
        "title": COUNTER_TITLE,
        "pattern": r"Counter global: <b>(?P<global_counter>\d+)</b>"
    },
    JOIN_GAME_ERROR_NOGAME: {
        "title": JOIN_GAME_TITLE,
        "pattern": r"There is no available games|No hay juegos disponibles"
    },
    CLEAN_SERVICE: {
        "title": CLEAN_TITLE,
        "pattern": r"<b>(?P<n_games_delete>\d+)</b> (games removed from db|juegos borrados de la bd)"
    },
    SELECT_GAME_SERVICE: {
        "title": SELECT_GAME_TITLE,
        "pattern": r""
    },
    SELECT_GAME_ERROR_NOCAT: {
        "title": SELECT_GAME_TITLE,
        "pattern": r"No games as cat|No hay juegos disponibles como gato"
    },
    SELECT_GAME_ERROR_NOMOUSE: {
        "title": SELECT_GAME_TITLE,
        "pattern": r"No games as mouse|No hay juegos disponibles como ratón"
    },
    SHOW_GAME_SERVICE: {
        "title": SHOW_GAME_TITLE,
        "pattern": r"(Board|Tablero): (?P<board>\[.*?\])"
    },
    PLAY_GAME_MOVING: {
        "title": SHOW_GAME_TITLE,
        "pattern": r"<blockquote class=\"(?P<turn>\w+)\">(.|\n)*?"
                   r"<input type=\"submit\" value=\"Move\" />(.|\n)*?</blockquote>"
    },
    PLAY_GAME_WAITING: {
        "title": SHOW_GAME_TITLE,
        "pattern": r"(Waiting for the|Esperando al) (?P<turn>\w+).{3}"
    },
}


class ServiceBaseTest(TestCase):
    def setUp(self):
        self.paramsUser1 = {"username": TEST_USERNAME_1, "password": TEST_PASSWORD_1}
        self.paramsUser2 = {"username": TEST_USERNAME_2, "password": TEST_PASSWORD_2}

        User.objects.filter(
            Q(username=self.paramsUser1["username"]) |
            Q(username=self.paramsUser2["username"])).delete()

        self.user1 = User.objects.create_user(
            username=self.paramsUser1["username"],
            password=self.paramsUser1["password"])
        self.user2 = User.objects.create_user(
            username=self.paramsUser2["username"],
            password=self.paramsUser2["password"])

        self.client1 = self.client
        self.client2 = Client()

    def tearDown(self):
        User.objects.filter(
            Q(username=self.paramsUser1["username"]) |
            Q(username=self.paramsUser2["username"])).delete()

    @classmethod
    def loginTestUser(cls, client, user):
        client.force_login(user)

    @classmethod
    def logoutTestUser(cls, client):
        client.logout()

    @classmethod
    def decode(cls, txt):
        return txt.decode("utf-8")

    def validate_login_required(self, client, service):
        self.logoutTestUser(client)
        response = client.get(reverse(service), follow=True)
        self.assertEqual(response.status_code, 200)
        self.is_login(response)

    def validate_anonymous_required(self, client, service):
        self.loginTestUser(client, self.user1)
        response = client.get(reverse(service), follow=True)
        self.assertEqual(response.status_code, 403)
        self.is_anonymous_error(response)

    def validate_response(self, service, response):
        definition = SERVICE_DEF[service]
        self.assertRegex(self.decode(response.content), definition["title"])
        m = re.search(definition["pattern"], self.decode(response.content))
        self.assertTrue(m)
        return m

    def is_login(self, response):
        self.validate_response(LOGIN_SERVICE, response)

    def is_login_error(self, response):
        self.validate_response(LOGIN_ERROR, response)

    def is_anonymous_error(self, response):
        self.validate_response(ANONYMOUSE_ERROR, response)

    def is_landing_autenticated(self, response, user):
        m = self.validate_response(LANDING_PAGE, response)
        self.assertEqual(m.group("username"), user.username)

    def is_signup_error1(self, response):
        self.validate_response(SIGNUP_ERROR_PASSWORD, response)

    def is_signup_error2(self, response):
        self.validate_response(SIGNUP_ERROR_USER, response)

    def is_signup_error3(self, response):
        self.validate_response(SIGNUP_ERROR_AUTH_PASSWORD, response)

    def is_counter_session(self, response, value):
        m = self.validate_response(COUNTER_SESSION_VALUE, response)
        self.assertEqual(Decimal(m.group("session_counter")), value)

    def is_counter_global(self, response, value):
        m = self.validate_response(COUNTER_GLOBAL_VALUE, response)
        self.assertEqual(Decimal(m.group("global_counter")), value)

    def is_join_game_error(self, response):
        self.validate_response(JOIN_GAME_ERROR_NOGAME, response)

    def is_clean_db(self, response, n_games):
        m = self.validate_response(CLEAN_SERVICE, response)
        self.assertEqual(Decimal(m.group("n_games_delete")), n_games)

    def is_select_game(self, response):
        self.validate_response(SELECT_GAME_SERVICE, response)

    def is_select_game_nocat(self, response):
        self.validate_response(SELECT_GAME_ERROR_NOCAT, response)

    def is_select_game_nomouse(self, response):
        self.validate_response(SELECT_GAME_ERROR_NOMOUSE, response)

    def is_play_game(self, response, game):
        m = self.validate_response(SHOW_GAME_SERVICE, response)
        board = ([0] * (Game.MAX_CELL - Game.MIN_CELL + 1))
        board[game.cat1] = board[game.cat2] = board[game.cat3] = board[game.cat4] = 1
        board[game.mouse] = -1
        self.assertEquals(m.group("board"), str(board))

    def is_play_game_moving(self, response, game):
        m = self.validate_response(PLAY_GAME_MOVING, response)
        self.assertEqual(game.cat_turn, m.group("turn") == "cat")
        self.assertEqual(not game.cat_turn, m.group("turn") == "mouse")

    def is_play_game_waiting(self, response, game):
        m = self.validate_response(PLAY_GAME_WAITING, response)
        self.assertEqual(game.cat_turn, m.group("turn") == "cat")
        self.assertEqual(not game.cat_turn, m.group("turn") == "mouse")


class LogInOutServiceTests(ServiceBaseTest):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test1(self):
        """ Carga del formulario de login """
        self.assertFalse(self.client1.session.get(USER_SESSION_ID, False))
        response = self.client1.get(reverse(LOGIN_SERVICE), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.client1.session.get(USER_SESSION_ID, False))
        self.is_login(response)

    def test2(self):
        """ Login correcto y almacenamiento de las credenciales en sesión """
        self.assertFalse(self.client1.session.get(USER_SESSION_ID, False))
        self.client1.post(reverse(LOGIN_SERVICE), self.paramsUser1, follow=True)
        self.assertEqual(Decimal(self.client1.session.get(USER_SESSION_ID)), self.user1.id)

        self.validate_login_required(self.client2, LOGIN_SERVICE)
        self.assertFalse(self.client2.session.get(USER_SESSION_ID, False))

    def test3(self):
        """ Solo los usuarios anónimos pueden invocar al servicio """
        self.validate_anonymous_required(self.client1, LOGIN_SERVICE)

    def test4(self):
        """ Identificación de los usuarios autenticados en la página de landing """
        sessions = [
            {"client": self.client1, "user": self.user1},
            {"client": self.client2, "user": self.user2}
        ]

        for session in sessions:
            self.loginTestUser(session["client"], session["user"])

        for session in sessions:
            response = session["client"].get(reverse(LANDING_PAGE), follow=True)
            self.is_landing_autenticated(response, session["user"])

    def test5(self):
        """ Error de login si el usuario no existe """
        User.objects.filter(id=self.user1.id).delete()

        response = self.client1.post(reverse(LOGIN_SERVICE), self.paramsUser1, follow=True)
        self.is_login_error(response)

    def test6(self):
        """ Error de login la clave no es correcta """
        User.objects.filter(id=self.user1.id).delete()
        User.objects.create_user(
            username=self.paramsUser1["username"],
            password=self.paramsUser1["password"]+"XXX")

        response = self.client1.post(reverse(LOGIN_SERVICE), self.paramsUser1, follow=True)
        self.is_login_error(response)

    def test7(self):
        """ Logout válido """
        self.loginTestUser(self.client1, self.user1)
        self.assertEqual(Decimal(self.client1.session.get(USER_SESSION_ID)), self.user1.id)
        self.client1.get(reverse(LOGOUT_SERVICE), follow=True)
        self.assertFalse(self.client1.session.get(USER_SESSION_ID, False))


class SignupServiceTests(ServiceBaseTest):
    def setUp(self):
        super().setUp()
        self.paramsUser1.update({"password2": self.paramsUser1["password"]})

    def tearDown(self):
        super().tearDown()

    def test0(self):
        """ Validación correcta del formulario de alta """
        User.objects.filter(id=self.user1.id).delete()
        self.assertTrue(forms.SignupForm(self.paramsUser1).is_valid())

    def test1(self):
        """ Solo los usuarios anónimos tienen acceso """
        self.validate_anonymous_required(self.client1, SIGNUP_SERVICE)

    def test2(self):
        """ Alta correcta de usuarios """
        User.objects.filter(id=self.user1.id).delete()
        n_user = User.objects.count()

        self.client1.post(reverse(SIGNUP_SERVICE), self.paramsUser1, follow=True)
        self.assertEquals(User.objects.count(), n_user + 1)

        user = User.objects.get(username=self.paramsUser1["username"])
        self.assertEqual(user.username, self.paramsUser1["username"])
        self.assertNotEqual(user.password, self.paramsUser1["password"])
        self.assertTrue(user.check_password(self.paramsUser1["password"]))

    def test3(self):
        """ Clave y repetición de clave no coinciden """
        self.paramsUser1["username"] = self.paramsUser1["username"] + "XXX"
        self.paramsUser1["password2"] = self.paramsUser1["password"] + "XXX"
        n_user = User.objects.count()

        response = self.client1.post(reverse(SIGNUP_SERVICE), self.paramsUser1, follow=True)
        self.is_signup_error1(response)
        self.assertEquals(User.objects.count(), n_user)
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username=self.paramsUser1["username"])

    def test4(self):
        """ Usuario duplicado """
        User.objects.filter(id=self.user1.id).delete()
        pass_dummy = self.paramsUser1["username"] + "XXX"
        User.objects.create(username=self.paramsUser1["username"], password=pass_dummy)
        n_user = User.objects.count()

        user = User.objects.get(username=self.paramsUser1["username"])
        self.assertEqual(user.username, self.paramsUser1["username"])
        self.assertEqual(user.password, pass_dummy)

        response = self.client1.post(reverse(SIGNUP_SERVICE), self.paramsUser1, follow=True)
        self.is_signup_error2(response)
        self.assertEquals(User.objects.count(), n_user)

        user = User.objects.get(username=self.paramsUser1["username"])
        self.assertEqual(user.username, self.paramsUser1["username"])
        self.assertEqual(user.password, pass_dummy)

    def test5(self):
        """ Clave demasiado corta y simple """
        self.paramsUser1["username"] = self.paramsUser1["username"] + "XXX"
        self.paramsUser1["password2"] = self.paramsUser1["password"] = "abc"
        n_user = User.objects.count()

        response = self.client1.post(reverse(SIGNUP_SERVICE), self.paramsUser1, follow=True)
        self.is_signup_error3(response)
        self.assertEquals(User.objects.count(), n_user)


class GameRequiredBaseServiceTests(ServiceBaseTest):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        self.user1.games_as_cat.all().delete()
        self.user2.games_as_cat.all().delete()
        super().tearDown()


class BckGamesServiceTests(GameRequiredBaseServiceTests):
    def setUp(self):
        super().setUp()
        self.bck_games = None

    def tearDown(self):
        if self.bck_games:
            for game in self.bck_games:
                game.mouse_user = None
                game.save()

        super().tearDown()

    def clean_games(self):
        self.bck_games = Game.objects.filter(mouse_user__isnull=True)
        for game in self.bck_games:
            game.mouse_user = self.user1
            game.save()


class CreateGameServiceTests(GameRequiredBaseServiceTests):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test1(self):
        """ Solo puede invocarse por usuarios autenticados """
        self.validate_login_required(self.client1, CREATE_GAME_SERVICE)

    def test2(self):
        """ Crear juego correctamente """
        n_games = Game.objects.count()
        if n_games == 0:
            id_max = -1
        else:
            id_max = Game.objects.order_by('-id')[0:1].get().id

        self.loginTestUser(self.client1, self.user1)
        response = self.client1.get(reverse(CREATE_GAME_SERVICE), follow=True)
        self.assertEqual(response.status_code, 200)

        games = Game.objects.filter(id__gt=id_max)
        self.assertEqual(games.count(), 1)
        self.assertEqual(games[0].cat_user.username, self.user1.username)
        self.assertIsNone(games[0].mouse_user)
        self.assertTrue(games[0].cat_turn)


class JoinGameServiceTests(BckGamesServiceTests):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test1(self):
        """ Solo puede invocarse por usuarios autenticados """
        self.validate_login_required(self.client1, JOIN_GAME_SERVICE)

    def test2(self):
        """ Unirse correctamente a un juego del que no eres raton """
        sessions = [
            {"client": self.client1, "user": self.user1},
            {"client": self.client2, "user": self.user2}
        ]

        games = []
        for session in sessions:
            self.loginTestUser(session["client"], session["user"])
            for _ in range(1, 4):
                games.append(Game.objects.create(cat_user=session["user"]))

        for game in games:
            self.assertIsNone(game.mouse_user)

        for session in sessions:
            session["client"].get(reverse(JOIN_GAME_SERVICE), follow=True)
            id_game = max(game.id for game in list(filter(lambda g: g.cat_user != session["user"], games)))
            self.assertEqual(Game.objects.get(id=id_game).mouse_user, session["user"])

    def test3(self):
        """ No hay juegos a los que unirse """
        self.clean_games()

        self.loginTestUser(self.client2, self.user2)
        response = self.client2.get(reverse(JOIN_GAME_SERVICE), follow=True)
        self.is_join_game_error(response)

    def test4(self):
        """ No hay juegos de los que no soy el gato a los que unirse """
        self.clean_games()

        for _ in range(1, 4):
            Game.objects.create(cat_user=self.user2)

        self.loginTestUser(self.client2, self.user2)
        response = self.client2.get(reverse(JOIN_GAME_SERVICE), follow=True)
        self.is_join_game_error(response)


class PlayGameBaseServiceTests(GameRequiredBaseServiceTests):
    def setUp(self):
        super().setUp()

        self.sessions = [
            {"client": self.client1, "player": self.user1},
            {"client": self.client2, "player": self.user2},
        ]

    def tearDown(self):
        super().tearDown()

    def set_game_in_session(self, client, user, game_id):
        self.loginTestUser(client, user)
        session = client.session
        session[constants.GAME_SELECTED_SESSION_ID] = game_id
        session.save()


class PlayServiceTests(PlayGameBaseServiceTests):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test1(self):
        """ Solo puede invocarse por usuarios autenticados """
        self.validate_login_required(self.client1, SHOW_GAME_SERVICE)


class MoveServiceTests(PlayGameBaseServiceTests):
    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test0(self):
        """ Campos de formulario válidos """
        self.assertTrue(forms.MoveForm({"origin": 0, "target": 0}).is_valid())
        self.assertFalse(forms.MoveForm({"origin": -1, "target": 0}).is_valid())
        self.assertFalse(forms.MoveForm({"origin": 64, "target": 0}).is_valid())
        self.assertFalse(forms.MoveForm({"origin": 0, "target": -1}).is_valid())
        self.assertFalse(forms.MoveForm({"origin": 0, "target": 64}).is_valid())

    def test1(self):
        """ Solo puede invocarse por usuarios autenticados """
        self.validate_login_required(self.client1, MOVE_SERVICE)

    def test2(self):
        """ GET no permitido """
        game = Game.objects.create(cat_user=self.user1, mouse_user=self.user2, status=GameStatus.ACTIVE)
        self.set_game_in_session(self.client1, self.user1, game.id)
        response = self.client.get(reverse(MOVE_SERVICE), follow=True)
        self.assertEqual(response.status_code, 405)

    def test3(self):
        """ Secuencia de movimientos válidos """
        moves = [
            {**self.sessions[0], **{"origin": 0, "target": 9, "positions": [9, 2, 4, 6, 59]}},
            {**self.sessions[1], **{"origin": 59, "target": 50, "positions": [9, 2, 4, 6, 50]}},
            {**self.sessions[0], **{"origin": 9, "target": 16, "positions": [16, 2, 4, 6, 50]}},
            {**self.sessions[1], **{"origin": 50, "target": 41, "positions": [16, 2, 4, 6, 41]}},
        ]

        game_t0 = Game.objects.create(cat_user=self.user1, mouse_user=self.user2, status=GameStatus.ACTIVE)
        for session in self.sessions:
            self.set_game_in_session(session["client"], session["player"], game_t0.id)

        n_moves = 0
        for move in moves:
            response = move["client"].post(reverse(MOVE_SERVICE), move, follow=True)
            self.assertEqual(response.status_code, 200)

            game_t1 = Game.objects.get(id=game_t0.id)
            n_moves += 1
            self.assertNotEqual(str(game_t0), str(game_t1))
            self.assertEqual(BaseModelTest.get_array_positions(game_t1), move["positions"])
            self.assertEqual(game_t1.cat_turn, move["player"] == self.user2)
            self.assertEqual(game_t1.moves.count(), n_moves)

            game_t0 = game_t1

    def test4(self):
        """ Llamada a mover si no existe un juego seleccionado """
        moves = [
            {**self.sessions[0], **{"origin": 0, "target": 9}},
            {**self.sessions[1], **{"origin": 59, "target": 50}},
        ]

        game_t0 = Game.objects.create(cat_user=self.user1, mouse_user=self.user2, status=GameStatus.ACTIVE)
        for session in self.sessions:
            self.loginTestUser(session["client"], session["player"])

        for move in moves:
            response = move["client"].post(reverse(MOVE_SERVICE), move, follow=True)
            self.assertEqual(response.status_code, 404)
            game_t1 = Game.objects.get(id=game_t0.id)
            self.assertEqual(str(game_t0), str(game_t1))
            self.assertEqual(game_t1.moves.count(), 0)

            game_t0.cat_turn = not game_t1.cat_turn
            game_t0.save()