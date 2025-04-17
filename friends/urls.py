from django.urls import path
from . import views

app_name = 'friends'

urlpatterns = [
    # 好友功能
    path('', views.friends_home, name='home'),
    path('search/', views.search_users, name='search_users'),
    path('request/send/<int:user_id>/', views.send_friend_request, name='send_request'),
    path('requests/', views.friend_requests, name='friend_requests'),
    path('request/accept/<int:request_id>/', views.accept_friend_request, name='accept_request'),
    path('request/reject/<int:request_id>/', views.reject_friend_request, name='reject_request'),
    path('remove/<int:friend_id>/', views.remove_friend, name='remove_friend'),
    
    # 聊天功能
    path('chat/', views.chat_list, name='chat_list'),
    path('chat/<int:friend_id>/', views.chat_detail, name='chat_detail'),
    path('chat/<int:friend_id>/send/', views.send_message_ajax, name='send_message_ajax'),
    path('chat/<int:friend_id>/messages/', views.get_new_messages_ajax, name='get_new_messages'),
    
    # 通知功能
    path('notifications/count/', views.get_notifications_count_ajax, name='get_notifications_count'),
] 