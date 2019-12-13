from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from logic.forms import SignupForm, LoginForm
from datamodel import constants
from datamodel.models import Game, GameStatus, Move, Counter
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from datetime import datetime, timezone
from django.core.paginator import Paginator

ELEMENTS_PER_PAGE = 3


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
        context_dict = {
            'user_form': login_form,
            'return_service': return_service
        }

        user = authenticate(username=username, password=password)

        if user:
            if user.is_active:
                login(request, user)
                request.session['counter_session'] = 0
                return redirect(return_service)
            else:
                login_form.add_error(
                    None,
                    'La cuenta indicada se encuentra deshabilitada'
                )
                return render(request, 'mouse_cat/login.html', context_dict)
        else:
            login_form.add_error(None, 'Username/password is not valid')
            return render(request, 'mouse_cat/login.html', context_dict)
    else:
        login_form = LoginForm()
        return_service = request.GET.get('next', '/index/')
        context_dict = {
            'user_form': login_form,
            'return_service': return_service
        }
        return render(request, 'mouse_cat/login.html', context_dict)


# Autor: Alejandro Pascual Pozo
@login_required
@require_http_methods(['GET'])
def logout_service(request):
    context_dict = {'user': request.user.username}
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

    context_dict = {'user_form': signup_form}
    return render(request, 'mouse_cat/signup.html', context_dict)


# Autor: Alejandro Pascual Pozo
@require_http_methods(['GET'])
def counter_service(request):
    inc_counters(request)

    counter_session = request.session['counter_session']
    counter_global = Counter.objects.get_current_value()

    context_dict = {
        'counter_session': counter_session,
        'counter_global': counter_global
    }
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
    context_dict = {'game': game}
    return render(request, 'mouse_cat/new_game.html', context_dict)


# Autor: Víctor Yrazusta Ibarra
@login_required
@require_http_methods(['GET'])
def join_game_service(request):
    open_games = Game.objects.filter(
        status=GameStatus.CREATED
    ).filter(
        ~Q(cat_user=request.user)
    ).order_by('-id')
    if len(open_games) > 0:
        game = open_games[0]
        game.mouse_user = request.user
        game.save()
        context_dict = {'game': game}
    else:
        context_dict = {'msg_error': 'There is no available games'}

    return render(request, 'mouse_cat/join_game.html', context_dict)


# Autor: Alejandro Pascual Pozo
@login_required
@require_http_methods(['GET', 'POST'])
def select_game_service(request, game_type=None, game_id=None):
    if game_id is not None:
        if game_type == 'current':
            request.session['game_selected'] = game_id
            return redirect(reverse('show_game'))
        elif game_type == 'open':
            games = Game.objects.filter(id=game_id)
            if len(games) == 0:
                context_dict = {'msg_error': 'The game does not exist'}
            elif games[0].status == GameStatus.CREATED:
                games[0].mouse_user = request.user
                games[0].save()
                context_dict = {'game': games[0]}
            else:
                context_dict = {'msg_error': 'There game is no longer open'}
            return render(request, 'mouse_cat/join_game.html', context_dict)
        elif game_type == 'replay':
            request.session['game_selected'] = game_id
            request.session['current_move'] = 0
            return redirect(reverse('show_replay'))
        else:
            return errorHTTP(
                request,
                exception='The game category selected was not found.',
                status=404
            )
    else:
        if game_type == 'current':
            as_cat = Game.objects.filter(
                cat_user=request.user
            ).filter(
                status=GameStatus.ACTIVE
            ).order_by('-id')
            as_mouse = Game.objects.filter(
                mouse_user=request.user
            ).filter(
                status=GameStatus.ACTIVE
            ).order_by('-id')
            context_dict = {
                'cat_num_pages': len(as_cat)//ELEMENTS_PER_PAGE,
                'mouse_num_pages': len(as_mouse)//ELEMENTS_PER_PAGE,
                'game_type': 'current'
            }
        elif game_type == 'open':
            as_mouse = Game.objects.filter(
                status=GameStatus.CREATED
            ).filter(
                ~Q(cat_user=request.user)
            ).order_by('-id')
            context_dict = {
                'cat_num_pages': 0,
                'mouse_num_pages': len(as_mouse)//ELEMENTS_PER_PAGE,
                'game_type': 'open'
            }
        elif game_type == 'replay':
            as_cat = Game.objects.filter(
                cat_user=request.user
            ).filter(
                status=GameStatus.FINISHED
            ).order_by('-id')
            as_mouse = Game.objects.filter(
                mouse_user=request.user
            ).filter(
                status=GameStatus.FINISHED
            ).order_by('-id')
            context_dict = {
                'cat_num_pages': len(as_cat)//ELEMENTS_PER_PAGE,
                'mouse_num_pages': len(as_mouse)//ELEMENTS_PER_PAGE,
                'game_type': 'replay'
            }
        else:
            return errorHTTP(
                request,
                exception='The game category selected was not found.',
                status=400
            )
        return render(request, 'mouse_cat/select_game.html', context_dict)


# Autor: Alejandro Pascual Pozo
@login_required
@require_http_methods(['POST'])
def get_new_page_service(request):
    game_type = request.POST.get('game_type')
    if game_type is None:
        return errorHTTP(
            request,
            exception='No game type provided.',
            status=404
        )

    page_num = request.POST.get('page_num')
    if page_num is None:
        return errorHTTP(
            request,
            exception='No page number provided.',
            status=404
        )

    try:
        page_num = int(page_num)
    except ValueError:
        return errorHTTP(
            request,
            exception='Page number invalid.',
            status=404
        )

    cat_or_mouse = request.POST.get('cat_or_mouse')
    if cat_or_mouse is None:
        return errorHTTP(
            request,
            exception='No cat or mouse provided.',
            status=404
        )
    is_cat = (cat_or_mouse == 'cat')

    if game_type == 'current':
        if is_cat:
            data = Game.objects.filter(
                cat_user=request.user
            ).filter(
                status=GameStatus.ACTIVE
            ).order_by('-id')
        else:
            data = Game.objects.filter(
                mouse_user=request.user
            ).filter(
                status=GameStatus.ACTIVE
            ).order_by('-id')
        page = Paginator(data, ELEMENTS_PER_PAGE)
        if page.num_pages < page_num:
            return errorHTTP(
                request,
                exception='Page not in range.',
                status=404
            )
        context_dict = {'page': page.page(page_num), 'game_type': 'current'}
    elif game_type == 'open':
        data = Game.objects.filter(
            status=GameStatus.CREATED
        ).filter(
            ~Q(cat_user=request.user)
        ).order_by('-id')
        page = Paginator(data, ELEMENTS_PER_PAGE)
        if page.num_pages < page_num:
            return errorHTTP(
                request,
                exception='Page not in range.',
                status=404
            )
        context_dict = {'page': page.page(page_num), 'game_type': 'open'}
    elif game_type == 'replay':
        if is_cat:
            data = Game.objects.filter(
                cat_user=request.user
            ).filter(
                status=GameStatus.FINISHED
            ).order_by('-id')
        else:
            data = Game.objects.filter(
                mouse_user=request.user
            ).filter(
                status=GameStatus.FINISHED
            ).order_by('-id')
        page = Paginator(data, ELEMENTS_PER_PAGE)
        if page.num_pages < page_num:
            return errorHTTP(
                request,
                exception='Page not in range.',
                status=404
            )
        context_dict = {'page': page.page(page_num), 'game_type': 'replay'}
    else:
        return errorHTTP(
            request,
            exception='The game category selected was not found.',
            status=400
        )
    return render(request, 'mouse_cat/select_game_page.html', context_dict)


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

    if game.status != GameStatus.ACTIVE and game.status != GameStatus.FINISHED:
        return errorHTTP(
            request,
            exception='The selected game is not active or finished',
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
            exception='You have not selected a replay',
            status=404
        )

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        return errorHTTP(
            request,
            exception='The selected replay is not valid',
            status=404
        )

    game = games[0]

    if game.status != GameStatus.FINISHED:
        return errorHTTP(
            request,
            exception='The selected replay is not a finished game',
            status=404
        )

    game.cat1 = 0
    game.cat2 = 2
    game.cat3 = 4
    game.cat4 = 6
    game.mouse = 59

    current_move = request.session['current_move']
    moves = Move.objects.filter(game=game_id).order_by('date')
    if current_move > 0:
        for move in moves[0:current_move]:
            if move.origin == game.cat1:
                game.cat1 = move.target
            elif move.origin == game.cat2:
                game.cat2 = move.target
            elif move.origin == game.cat3:
                game.cat3 = move.target
            elif move.origin == game.cat4:
                game.cat4 = move.target
            elif move.origin == game.mouse:
                game.mouse = move.target

    has_next = current_move < len(moves)
    has_previous = current_move > 0

    board = [0]*64
    board[game.cat1] = 1
    board[game.cat2] = 1
    board[game.cat3] = 1
    board[game.cat4] = 1
    board[game.mouse] = -1

    context_dict = {
        'game': game,
        'board': board,
        'has_next': has_next,
        'has_previous': has_previous
    }
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
    except Exception:
        pass

    return redirect(reverse('show_game'))


@login_required
@require_http_methods(['POST'])
def get_move_service(request):
    shift = int(request.POST.get('shift', '0'))

    if shift != -1 and shift != 1:
        data = {'valid': False}
        return JsonResponse(data, safe=False)

    if 'game_selected' not in request.session:
        data = {'valid': False}
        return JsonResponse(data, safe=False)

    game_id = request.session['game_selected']
    games = Game.objects.filter(id=game_id)

    if len(games) == 0:
        data = {'valid': False}
        return JsonResponse(data, safe=False)

    game = games[0]

    if game.status != GameStatus.FINISHED:
        data = {'valid': False}
        return JsonResponse(data, safe=False)

    current_move = request.session.get('current_move', 0)
    moves = Move.objects.filter(game=game_id).order_by('date')

    if (
        (shift == -1 and current_move <= 0) or
        (shift == 1 and current_move >= len(moves))
    ):
        data = {'valid': False}
        return JsonResponse(data, safe=False)

    current_move += int(shift)
    request.session['current_move'] = current_move

    previous_exists = (current_move > 0)
    next_exists = (current_move < len(moves))
    if shift == 1:
        origin = moves[current_move - 1].origin
        target = moves[current_move - 1].target
    else:
        origin = moves[current_move].target
        target = moves[current_move].origin

    data = {
        'origin': origin,
        'target': target,
        'previous': previous_exists,
        'next': next_exists,
        'valid': True
    }
    return JsonResponse(data, safe=False)
