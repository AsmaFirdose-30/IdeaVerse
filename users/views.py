from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .forms import UserRegisterForm, UserProfileForm, AccountSettingsForm
from .models import UserProfile, Notification
from core.models import Board, BoardLike, BoardComment, Content, ContentLike, ContentComment
import re

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully!")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})

def verify_email(request, token):
    profile = get_object_or_404(UserProfile, email_verification_token=token)
    if not profile.email_verified:
        profile.email_verified = True
        profile.save()
        messages.success(request, "Your email has been verified successfully! You can now log in.")
    else:
        messages.info(request, "Your email was already verified.")
    return redirect('login')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Welcome back!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'users/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def profile_view(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user)
    
    # Get user's boards
    boards = Board.objects.filter(user=request.user)
    
    # Get user's likes
    likes = BoardLike.objects.filter(user=request.user)
    content_likes = ContentLike.objects.filter(user=request.user)
    
    # Get user's comments
    comments = BoardComment.objects.filter(user=request.user)
    content_comments = ContentComment.objects.filter(user=request.user)
    
    # Get user's uploads
    uploads = Content.objects.filter(board__user=request.user)
    
    context = {
        'profile': user_profile,
        'boards': boards,
        'likes': likes,
        'comments': comments,
        'uploads': uploads,
        'content_likes': content_likes,
        'content_comments': content_comments,
    }
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def account_settings(request):
    if request.method == 'POST':
        form = AccountSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account settings have been updated successfully!')
            return redirect('account_settings')
    else:
        form = AccountSettingsForm(instance=request.user)
    
    return render(request, 'users/account_settings.html', {'form': form})

@login_required
def my_activity(request):
    uploads = Content.objects.filter(board__user=request.user).order_by('-created_at')
    content_likes = ContentLike.objects.filter(user=request.user).order_by('-liked_at')
    content_comments = ContentComment.objects.filter(user=request.user).order_by('-commented_at')

    return render(request, 'users/my_activity.html', {
        'uploads': uploads,
        'content_likes': content_likes,
        'content_comments': content_comments,
    })

@login_required
def notification_settings(request):
    if request.method == 'POST':
        preferences = request.POST.dict()
        preferences.pop('csrfmiddlewaretoken', None)
        
        profile = request.user.profile
        profile.notification_preferences = preferences
        profile.save()
        
        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('notification_settings')
        
    return render(request, 'users/notification_settings.html', {
        'preferences': request.user.profile.notification_preferences
    })

@login_required
def toggle_theme(request):
    profile = request.user.profile
    profile.theme_preference = 'dark' if profile.theme_preference == 'light' else 'light'
    profile.save()
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    # Get user's boards, likes, comments, uploads for profile page
    boards = Board.objects.filter(user=user)
    likes = BoardLike.objects.filter(user=user)
    comments = BoardComment.objects.filter(user=user)
    uploads = Content.objects.filter(board__user=user)
    context = {
        'profile': profile,
        'boards': boards,
        'likes': likes,
        'comments': comments,
        'uploads': uploads,
    }
    return render(request, 'users/profile.html', context)

@login_required
def notifications(request):
    notifications = request.user.notifications.order_by('-created_at')
    # Mark all as read
    notifications.update(is_read=True)
    unread_notifications_count = 0
    if request.method == 'POST':
        notif_id = request.POST.get('notif_id')
        action = request.POST.get('action')
        notif = get_object_or_404(Notification, id=notif_id, user=request.user)
        if notif.notification_type == 'collab_invite':
            board_id = notif.extra_data.get('board_id')
            board = get_object_or_404(Board, id=board_id)
            if action == 'accept':
                board.collaborators.add(request.user)
                notif.delete()
            elif action == 'reject':
                notif.delete()
        return redirect('notifications')
    return render(request, 'users/notifications.html', {'notifications': notifications, 'unread_notifications_count': unread_notifications_count})
