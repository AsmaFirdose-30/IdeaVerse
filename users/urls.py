from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/settings/', views.account_settings, name='account_settings'),
    path('profile/notifications/', views.notification_settings, name='notification_settings'),
    path('notifications/', views.notifications, name='notifications'),
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('my-activity/', views.my_activity, name='my_activity'),
]
