from django.http import HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from logic.forms import SignupForm, MoveForm, LoginForm
from datamodel import constants
from datamodel.models import Game, GameStatus, Move, Counter
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from datetime import datetime, timezone

# Autor: Alejandro Pascual Pozo
def errorHTTP(request, exception=None, status=200):
    context_dict = {}
    context_dict[constants.ERROR_MESSAGE_ID] = exception
    return render(request, 'mouse_cat/error.html', context_dict, status=status)


# Autor: Víctor Yrazusta Ibarra
def anonymous_required(f):
    def wrapped(request):
        if request.user.is_authenticated:
            # Modificado para evitar el error "connection already closed"
            return errorHTTP(
                request,
                exception='Action restricted to anonymous users',
                status=403
            )
        else:
            return f(request)
    return wrapped


# Autor: Alejandro Pascual Pozo
@require_http_methods(['GET'])
def index(request):    
    return render(request, 'mouse_cat/index.html')


# Autor: Víctor Yrazusta Ibarra
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
            login_form.add_error(None, 'Username/password is not valid')
            return render(request, 'mouse_cat/login.html', context_dict)
    else:
        login_form = LoginForm()
        return_service = request.GET.get('next', '/index/')
        context_dict = { 'user_form': login_form, 'return_service': return_service }
        return render(request, 'mouse_cat/login.html', context_dict)


# Autor: Alejandro Pascual Pozo
@login_required
@require_http_methods(['GET'])
def logout_service(request):
    context_dict = { 'user': request.user.username }
    logout(request)
    return render(request, 'mouse_cat/logout.html', context_dict)


# Autor: Víctor Yrazusta Ibarra
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


# Autor: Alejandro Pascual Pozo
@require_http_methods(['GET'])
def counter_service(request):
    inc_counters(request)

    counter_session = request.session['counter_session']
    counter_global = Counter.objects.get_current_value()

    context_dict = { 'counter_session': counter_session, 'counter_global': counter_global }
    return render(request, 'mouse_cat/counter.html', context_dict)


# Autor: Víctor Yrazusta Ibarra
def inc_counters(request):
    if 'counter_session' in request.session:
        request.session['counter_session'] += 1
    else:
        request.session['counter_session'] = 1
    Counter.objects.inc()


# Autor: Alejandro Pascual Pozo
@login_required
@require_http_methods(['GET'])
def create_game_service(request):
    game = Game(cat_user=request.user)
    game.save()
    context_dict = { 'game': game }
    return render(request, 'mouse_cat/new_game.html', context_dict)


# Autor: Víctor Yrazusta Ibarra
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
        context_dict = { 'msg_error': 'There is no available games' }   
     
    return render(request, 'mouse_cat/join_game.html', context_dict)


# Autor: Alejandro Pascual Pozo
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


# Autor: Alejandro Pascual Pozo
@login_required
@require_http_methods(['GET', 'POST'])
def select_replay_service(request, game_id=None):
    if game_id is not None:
        request.session['game_selected'] = game_id
        return redirect(reverse('show_replay'))
    else:
        games = Game.objects.filter(status=GameStatus.FINISHED)
        if len(games) == 0:
            games = None

        context_dict = {'games': games}
        return render(request, 'mouse_cat/select_replay.html', context_dict)


# Autor: Víctor Yrazusta Ibarra
@login_required
@require_http_methods(['GET'])
def show_game_service(request):
    if 'game_selected' not in request.session:
        return errorHTTP(
            request,
            exception='You have not selected a game',
            status=404
        )

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        return errorHTTP(
            request,
            exception='The selected game is not valid',
            status=404
        )

    game = games[0]

    if game.status != GameStatus.ACTIVE:
        return errorHTTP(
            request,
            exception='The selected game is not active',
            status=404
        )

    if game.cat_user != request.user and game.mouse_user != request.user:
        return errorHTTP(
            request,
            exception='You are not a player of the selected game',
            status=404
        )

    board = [0]*64
    board[game.cat1] = 1
    board[game.cat2] = 1
    board[game.cat3] = 1
    board[game.cat4] = 1
    board[game.mouse] = -1
    
    context_dict = {'game': game, 'board': board}
    return render(request, 'mouse_cat/game.html', context_dict)

# Autor: Víctor Yrazusta Ibarra
@login_required
@require_http_methods(['GET'])
def show_replay_service(request):
    if 'game_selected' not in request.session:
        return errorHTTP(
            request,
            exception='You have not selected a game',
            status=404
        )

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        return errorHTTP(
            request,
            exception='The selected game is not valid',
            status=404
        )

    game = games[0]

    board = [0]*64
    board[game.cat1] = 1
    board[game.cat2] = 1
    board[game.cat3] = 1
    board[game.cat4] = 1
    board[game.mouse] = -1
    
    context_dict = {'game': game, 'board': board}
    return render(request, 'mouse_cat/replay.html', context_dict)


@login_required
@require_http_methods(['POST'])
def get_update(request):    
    if 'game_selected' not in request.session:
        return errorHTTP(
            request,
            exception='You have not selected a game',
            status=404
        )

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        return errorHTTP(
            request,
            exception='The selected game is not valid',
            status=404
        )

    game = games[0]

    if game.status != GameStatus.ACTIVE:
        return errorHTTP(
            request,
            exception='The selected game is not active',
            status=404
        )

    if game.cat_user != request.user and game.mouse_user != request.user:
        return errorHTTP(
            request,
            exception='You are not a player of the selected game',
            status=404
        )

    lasts_moves = Move.objects.filter(game=game_id).order_by('-date')
    if (len(lasts_moves) == 0):
        ret = 0
        return JsonResponse(ret, safe=False)

    last_move = lasts_moves[0]

    if datetime.now(timezone.utc) > last_move.date:
        return get_board(request)
    
    ret = 0
    return JsonResponse(ret, safe=False)


@login_required
@require_http_methods(['POST'])
def get_board(request):
    if 'game_selected' not in request.session:
        return errorHTTP(
            request,
            exception='You have not selected a game',
            status=404
        )

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        return errorHTTP(
            request,
            exception='The selected game is not valid',
            status=404
        )

    game = games[0]

    if game.status != GameStatus.ACTIVE:
        return errorHTTP(
            request,
            exception='The selected game is not active',
            status=404
        )

    if game.cat_user != request.user and game.mouse_user != request.user:
        return errorHTTP(
            request,
            exception='You are not a player of the selected game',
            status=404
        )

    board = [0]*64
    board[game.cat1] = 1
    board[game.cat2] = 1
    board[game.cat3] = 1
    board[game.cat4] = 1
    board[game.mouse] = -1

    return JsonResponse(board, safe=False)



# Autor: Alejandro Pascual Pozo
@login_required
@require_http_methods(['POST'])
def move_service(request):
    if 'game_selected' not in request.session:
        return errorHTTP(
            request,
            exception='You have not selected a game',
            status=404
        )

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        return errorHTTP(
            request,
            exception='The selected game is not valid',
            status=404
        )

    game = games[0]

    if game.status != GameStatus.ACTIVE:
        return errorHTTP(
            request,
            exception='The selected game is not active',
            status=404
        )

    if game.cat_user != request.user and game.mouse_user != request.user:
        return errorHTTP(
            request,
            exception='You are not a player of the selected game',
            status=404
        )

    player = request.user
    origin = int(request.POST.get('origin'))
    target = int(request.POST.get('target'))

    try:
        move = Move(origin=origin, target=target, game=game, player=player)
        move.save()
    except:
        pass

    return redirect(reverse('show_game'))


@login_required
@require_http_methods(['POST'])
def get_move_service(request):
    if 'game_selected' not in request.session:
        return errorHTTP(
            request,
            exception='You have not selected a game',
            status=404
        )

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        return errorHTTP(
            request,
            exception='The selected game is not valid',
            status=404
        )

    game = games[0]

    if game.status != GameStatus.ACTIVE:
        return errorHTTP(
            request,
            exception='The selected game is not active',
            status=404
        )

    moves = Move.objects.filter(game=game_id).order_by('date')
    move_number = request.POST.get('move_number')

    if move_number >= len(moves):
        return errorHTTP(
            request,
            exception='The selected move does not exist',
            status=404
        )

    previous_exists = (move_number != 0)
    next_exists = (move_number != len(moves)-1)
    origin = moves[move_number].origin
    target = moves[move_number].target

    data = {'previous': previous_exists, 'next': next_exists, 'origin': origin, 'target': target}

    return JsonResponse(data, safe=False)
