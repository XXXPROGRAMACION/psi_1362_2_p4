from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from logic.forms import SignupForm, MoveForm, LoginForm
from datamodel import constants
from datamodel.models import Game, GameStatus, Move, Counter
from django.db.models import Q
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET'])
def index(request):    
    return render(request, 'mouse_cat/index.html')


def anonymous_required(f):
    def wrapped(request):
        if request.user.is_authenticated:
            return HttpResponseForbidden(
                errorHTTP(request, exception='Action restricted to anonymous users')
            )
        else:
            return f(request)
    return wrapped


@anonymous_required
@require_http_methods(['GET', 'POST'])
def login_service(request):
    # /!\ Username already exists innecesario
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        login_form = LoginForm(data=request.POST)
        return_service = request.POST.get('return_service', '/index/')
        context_dict = { 'user_form': login_form, 'return_service': return_service }

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                request.session['counter_session'] = 0
                return redirect(return_service)
            else:
                login_form.add_error(None, 'La cuenta indicada se encuentra deshabilitada')
                return render(request, 'mouse_cat/login.html', context_dict)
        else:
            login_form.add_error(None, 'Username/password is not valid|Usuario/clave no válidos')
            return render(request, 'mouse_cat/login.html', context_dict)
    else:
        login_form = LoginForm()
        return_service = request.GET.get('next', '/index/')
        context_dict = { 'user_form': login_form, 'return_service': return_service }
        return render(request, 'mouse_cat/login.html', context_dict)


@login_required
@require_http_methods(['GET'])
def logout_service(request):
    context_dict = { 'user': request.user.username }
    logout(request)
    return render(request, 'mouse_cat/logout.html', context_dict)


@anonymous_required
@require_http_methods(['GET', 'POST'])
def signup_service(request):
    if request.method == 'POST':
        signup_form = SignupForm(data=request.POST)
        if signup_form.is_valid():
            user = signup_form.save()

            user.set_password(user.password)
            user.save()

            login(request, user)
            request.session['counter_session'] = 0
            return redirect(reverse('index'))
    else:
        signup_form = SignupForm()

    context_dict = { 'user_form': signup_form }
    return render(request, 'mouse_cat/signup.html', context_dict)


@require_http_methods(['GET'])
def counter_service(request):
    inc_counters(request)

    counter_session = request.session['counter_session']
    counter_global = Counter.objects.get_current_value()

    context_dict = { 'counter_session': counter_session, 'counter_global': counter_global }
    return render(request, 'mouse_cat/counter.html', context_dict)


def inc_counters(request):
    if 'counter_session' in request.session:
        request.session['counter_session'] += 1
    else:
        request.session['counter_session'] = 1
    Counter.objects.inc()


@login_required
@require_http_methods(['GET'])
def create_game_service(request):
    game = Game(cat_user=request.user)
    game.save()
    context_dict = { 'game': game }
    return render(request, 'mouse_cat/new_game.html', context_dict)


@login_required
@require_http_methods(['GET'])
def join_game_service(request):
    open_games = Game.objects.filter(status=GameStatus.CREATED).filter(~Q(cat_user=request.user)).order_by('-id')
    if len(open_games) > 0:
        game = open_games[0]
        game.mouse_user = request.user
        game.save()
        context_dict = { 'game': game }
    else:
        context_dict = { 'msg_error': 'There is no available games|No hay juegos disponibles' }   
     
    return render(request, 'mouse_cat/join_game.html', context_dict)


@login_required
@require_http_methods(['GET', 'POST'])
def select_game_service(request, game_id=None):
    if game_id is not None:
        request.session['game_selected'] = game_id
        return redirect(reverse('show_game'))
    else:
        as_cat = Game.objects.filter(cat_user=request.user).filter(status=GameStatus.ACTIVE)
        if len(as_cat) == 0:
            as_cat = None
        as_mouse = Game.objects.filter(mouse_user=request.user).filter(status=GameStatus.ACTIVE)
        if len(as_mouse) == 0:
            as_mouse = None

        context_dict = { 'as_cat': as_cat, 'as_mouse': as_mouse }
        return render(request, 'mouse_cat/select_game.html', context_dict)


@login_required
@require_http_methods(['GET'])
def show_game_service(request):
    if 'game_selected' not in request.session:
        return errorHTTP(request, 'No se ha seleccionado una partida a la que jugar')    

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        return HttpResponseNotFound('La partida seleccionada no es válida') 

    game = games[0]

    if game.status != GameStatus.ACTIVE:
        return HttpResponseNotFound('La partida no está activa')

    if game.cat_user != request.user and game.mouse_user != request.user:
        return HttpResponseNotFound('No eres jugador de la partida seleccionada')

    board = [0]*64
    board[game.cat1] = 1
    board[game.cat2] = 1
    board[game.cat3] = 1
    board[game.cat4] = 1
    board[game.mouse] = -1

    move_form = MoveForm()
    
    # /!\
    # En teoría también se necesita el usuario actual, pero no veo que se use en game.html
    # Falta move_form (?)
    # /!\
    context_dict = { 'game': game, 'board': board, 'move_form': move_form }
    return render(request, 'mouse_cat/game.html', context_dict)


@login_required
@require_http_methods(['POST'])
def move_service(request):
    if 'game_selected' not in request.session:
        return errorHTTP(request, 'No se ha seleccionado una partida a la que jugar')    

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        return HttpResponseNotFound('La partida seleccionada no es válida') 

    game = games[0]

    if game.status != GameStatus.ACTIVE:
        return HttpResponseNotFound('La partida no está activa')

    if game.cat_user != request.user and game.mouse_user != request.user:
        return HttpResponseNotFound('No eres jugador de la partida seleccionada')

    # /!\
    # Revisar que exista la variable game_selected y que sea una partida válida
    # Averiguar nombres de los movimientos
    # /!\
    player = request.user_form
    origin = int(request.POST.get('origin'))
    target = int(request.POST.get('target'))
    
    if game.cat_turn is True:
        # /!\
        # if ningún game.cat == initial_pos:
        #     error
        # /!\
        # Comprobación de movimientos válidos
        game.cat1 = target
        #       ^ No necesariamente el 1
    else:
        # /!\
        # if game.mouse != initial_pos:
        #     error
        # /!\
        # Comprobación de movimientos válidos
        game.mouse = target

    move = Move(origin=origin, target=target, game=game, player=player)
    move.save()
    game.cat_turn = not game.cat_turn
    game.save()
    return redirect(reverse('show_game'))


def errorHTTP(request, exception=None):
    context_dict = {}
    context_dict[constants.ERROR_MESSAGE_ID] = exception
    return render(request, 'mouse_cat/error.html', context_dict)
