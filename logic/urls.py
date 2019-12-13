from django.urls import path
from logic import views

urlpatterns = [
    path('',  views.index, name='landing'),
    path('index/',  views.index, name='index'),
    path('login/',  views.login_service, name='login'),
    path('logout/',  views.logout_service, name='logout'),
    path('signup/',  views.signup_service, name='signup'),
    path('counter/',  views.counter_service, name='counter'),
    path('create_game/',  views.create_game_service, name='create_game'),
    path('join_game/',  views.join_game_service, name='join_game'),
    path('select_game/<slug:game_type>/',  views.select_game_service, name='select_game'),
    path('get_new_page/',  views.get_new_page_service, name='get_new_page'),
    path('select_game/<slug:game_type>/<int:game_id>/',  views.select_game_service, name='select_game'),
    path('show_game/',  views.show_game_service, name='show_game'),
    path('show_replay/',  views.show_replay_service, name='show_replay'),
    path('move/',  views.move_service, name='move'),
    path('get_move/<str:shift>/',  views.get_move_service, name='get_move'),
    path('get_board/',  views.get_board, name='get_board'),
    path('get_update/',  views.get_update, name='get_update')
]
