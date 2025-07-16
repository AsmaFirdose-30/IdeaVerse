from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('search/', views.search, name='search'),
    path('create_board/', views.create_board, name='create_board'),
    path('board/<int:board_id>/', views.board_detail, name='board_detail'),
    path('board/<int:board_id>/upload-content/', views.upload_file_content, name='upload_content'),
    path('board/<int:board_id>/upload-text/', views.upload_text_content, name='upload_text_content'),
    path('content/<int:content_id>/', views.content_detail, name='content_detail'),
    path('like/<int:board_id>/', views.like_board, name='like_board'),
    path('comment/<int:board_id>/', views.comment_board, name='comment_board'),    
    path('board/<int:board_id>/delete-content/<int:content_id>/', views.delete_content, name='delete_content'),
    path('board/<int:board_id>/edit-note/<int:content_id>/', views.edit_note, name='edit_note'),
    path('content/<int:content_id>/like/', views.like_content, name='like_content'),
    path('content/<int:content_id>/comment/', views.comment_content, name='comment_content'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('about/', views.about_us, name='about_us'),
    path('board/<int:board_id>/delete/', views.delete_board, name='delete_board'),
    path('board/<int:board_id>/rename/', views.rename_board, name='rename_board'),
]
