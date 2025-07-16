from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Board, Content, BoardContent, ContentLike, ContentComment
from .forms import BoardForm, ContentForm, BoardContentForm
from django.contrib import messages
from users.models import UserProfile, Notification
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.db.models.functions import TruncMonth
import json

from .forms import BoardForm

@login_required
def dashboard(request):
    try:
        # Ensure user has a profile
        request.user.profile
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=request.user)
    
    form = BoardForm()
    # Show only the current user's boards
    public_boards = Board.objects.filter(user=request.user, is_public=True)
    private_boards = Board.objects.filter(user=request.user, is_public=False)

    # Get recommended boards (other users' public boards)
    recommended_boards = Board.objects.filter(
        is_public=True
    ).exclude(user=request.user).annotate(
        num_likes=Count('likes')
    ).order_by('-num_likes')[:5]

    # Get collaborating boards (boards where the user is a collaborator)
    collaborating_boards = Board.objects.filter(collaborators=request.user).exclude(user=request.user)

    unread_notifications_count = get_unread_notifications_count(request)

    return render(request, 'core/dashboard.html', {
        'form': form,
        'public_boards': public_boards,
        'private_boards': private_boards,
        'recommended_boards': recommended_boards,
        'collaborating_boards': collaborating_boards,
        'unread_notifications_count': unread_notifications_count,
    })

@login_required
def create_board(request):
    if request.method == 'POST':
        form = BoardForm(request.POST)
        if form.is_valid():
            board = form.save(commit=False)
            board.user = request.user
            board.save()
            return redirect('dashboard')
    else:
        form = BoardForm()
    return render(request, 'core/create_board.html', {'form': form})

@login_required
def board_detail(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    # Only owner or collaborators can access
    if request.user != board.user and request.user not in board.collaborators.all():
        messages.error(request, "You don't have permission to view this board.")
        return redirect('dashboard')

    # Collaboration only for public boards
    show_collaboration = board.is_public

    # Handle collaborator invite (public boards only)
    if show_collaboration and request.method == 'POST' and 'invite_username' in request.POST:
        username = request.POST.get('invite_username').strip()
        if username:
            try:
                user_to_invite = User.objects.get(username=username)
                if user_to_invite == board.user:
                    messages.warning(request, 'You are already the owner of this board.')
                elif user_to_invite in board.collaborators.all():
                    messages.info(request, f'{username} is already a collaborator.')
                else:
                    from users.models import Notification
                    Notification.objects.create(
                        user=user_to_invite,
                        message=f"You have been invited to collaborate on the board '{board.title}' by {request.user.username}.",
                        notification_type='collab_invite',
                        extra_data={
                            'board_id': board.id,
                            'board_title': board.title,
                            'inviter': request.user.username
                        }
                    )
                    messages.success(request, f'Collaboration invite sent to {username}!')
            except User.DoesNotExist:
                messages.error(request, f'User {username} does not exist.')
        return redirect('board_detail', board_id=board.id)

    # Handle collaborator removal (public boards only)
    if show_collaboration and request.method == 'POST' and 'remove_collaborator' in request.POST and request.user == board.user:
        username = request.POST.get('remove_collaborator').strip()
        try:
            user_to_remove = User.objects.get(username=username)
            if user_to_remove in board.collaborators.all():
                board.collaborators.remove(user_to_remove)
                messages.success(request, f'{username} has been removed as a collaborator.')
            else:
                messages.warning(request, f'{username} is not a collaborator.')
        except User.DoesNotExist:
            messages.error(request, f'User {username} does not exist.')
        return redirect('board_detail', board_id=board.id)

    content_form = ContentForm()
    text_form = BoardContentForm()
    contents = board.file_contents.all()
    text_contents = board.text_contents.all()
    collaborators = board.collaborators.all()
    return render(request, 'core/board_detail.html', {
        'board': board,
        'contents': contents,
        'text_contents': text_contents,
        'content_form': content_form,
        'text_form': text_form,
        'collaborators': collaborators,
        'show_collaboration': show_collaboration,
    })

@login_required
def upload_file_content(request, board_id):
    # Get the board and check permissions
    board = get_object_or_404(Board, id=board_id)
    # Only owner or collaborators can upload to this board
    if request.user != board.user and request.user not in board.collaborators.all():
        messages.error(request, "You don't have permission to upload content to this board.")
        return redirect('dashboard')

    contents = board.file_contents.all()

    if request.method == 'POST':
        file_form = ContentForm(request.POST, request.FILES)
        if file_form.is_valid():
            try:
                content = file_form.save(commit=False)
                content.board = board
                content.save()
                messages.success(request, 'File uploaded successfully!')
                return redirect('board_detail', board_id=board.id)
            except Exception as e:
                messages.error(request, f'Error uploading file: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        file_form = ContentForm()

    return render(request, 'core/upload_content.html', {
        'board': board,
        'form': file_form,
        'contents': contents,
    })

@login_required
def upload_text_content(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    # Only owner or collaborators can add notes
    if request.user != board.user and request.user not in board.collaborators.all():
        messages.error(request, "You don't have permission to add notes to this board.")
        return redirect('dashboard')

    if request.method == 'POST':
        text_form = BoardContentForm(request.POST)
        if text_form.is_valid():
            text_content = text_form.save(commit=False)
            text_content.board = board
            text_content.save()
            return redirect('board_detail', board_id=board.id)

    return redirect('board_detail', board_id=board.id)

from django.shortcuts import render, get_object_or_404
from .models import Content

@login_required
def content_detail_view(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    # Check if the user has access to this content
    if not content.board.is_public and content.board.user != request.user:
        messages.error(request, "You don't have permission to view this content.")
        return redirect('dashboard')
        
    return render(request, 'core/content_detail.html', {
        'content': content,
        'board': content.board
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Board, BoardLike, BoardComment

@login_required
def like_board(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    like, created = BoardLike.objects.get_or_create(user=request.user, board=board)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'like_count': board.likes.count()})

@login_required
def comment_board(request, board_id):
    if request.method == 'POST':
        comment_text = request.POST.get('comment')
        board = get_object_or_404(Board, id=board_id)
        BoardComment.objects.create(user=request.user, board=board, comment=comment_text)
        return redirect('dashboard')

@login_required
def delete_content(request, board_id, content_id):
    board = get_object_or_404(Board, id=board_id)
    # Only the board owner can delete content
    if request.user != board.user:
        messages.error(request, "Only the board owner can delete content from this board.")
        return redirect('dashboard')
    
    # Try to find the content in both Content and BoardContent models
    content = None
    try:
        content = Content.objects.get(id=content_id, board=board)
    except Content.DoesNotExist:
        try:
            content = BoardContent.objects.get(id=content_id, board=board)
        except BoardContent.DoesNotExist:
            messages.error(request, 'Content not found.')
            return redirect('board_detail', board_id=board_id)
    
    try:
        content.delete()
        messages.success(request, 'Content deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting content: {str(e)}')
    
    return redirect('board_detail', board_id=board_id)

@login_required
def edit_note(request, board_id, content_id):
    board = get_object_or_404(Board, id=board_id)
    # Only owner or collaborators can edit notes
    if request.user != board.user and request.user not in board.collaborators.all():
        messages.error(request, "You don't have permission to edit notes on this board.")
        return redirect('dashboard')
    
    content = get_object_or_404(BoardContent, id=content_id, board=board)
    
    if request.method == 'POST':
        form = BoardContentForm(request.POST, instance=content)
        if form.is_valid():
            form.save()
            messages.success(request, 'Note updated successfully!')
            return redirect('board_detail', board_id=board_id)
    else:
        form = BoardContentForm(instance=content)
    
    return render(request, 'core/edit_note.html', {
        'form': form,
        'content': content,
        'board': board
    })

@login_required
def like_content(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    like, created = ContentLike.objects.get_or_create(user=request.user, content=content)
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'likes_count': content.likes.count()
    })

@login_required
def comment_content(request, content_id):
    if request.method == 'POST':
        content = get_object_or_404(Content, id=content_id)
        # Try to get comment from JSON body first
        try:
            data = json.loads(request.body)
            comment_text = data.get('comment')
        except Exception:
            comment_text = request.POST.get('comment')
        if comment_text:
            comment = ContentComment.objects.create(
                user=request.user,
                content=content,
                comment=comment_text
            )
            return JsonResponse({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'text': comment.comment,
                    'user': comment.user.username,
                    'commented_at': comment.commented_at.strftime('%Y-%m-%d %H:%M')
                }
            })
    return JsonResponse({'success': False})

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(ContentComment, id=comment_id)
    
    if comment.user == request.user:
        comment.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def content_detail(request, content_id):
    content = get_object_or_404(Content, id=content_id)
    
    # Increment view count
    content.increment_views()
    
    # Get likes and comments
    likes = content.likes.all()
    comments = content.comments.all().order_by('-commented_at')
    
    # Check if current user has liked the content
    user_liked = False
    if request.user.is_authenticated:
        user_liked = ContentLike.objects.filter(user=request.user, content=content).exists()
    
    context = {
        'content': content,
        'likes': likes,
        'comments': comments,
        'user_liked': user_liked,
    }
    
    return render(request, 'core/content_detail.html', context)

@login_required
def search(request):
    query = request.GET.get('q', '')
    if query:
        # Search for users
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)
        
        # Search for public boards
        public_boards = Board.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
            is_public=True
        ).exclude(user=request.user)
        
        # Search for public content
        public_content = Content.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
            board__is_public=True
        ).exclude(board__user=request.user)
        
        # Search for public notes
        public_notes = BoardContent.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query),
            board__is_public=True
        ).exclude(board__user=request.user)
        
        context = {
            'query': query,
            'users': users,
            'public_boards': public_boards,
            'public_content': public_content,
            'public_notes': public_notes,
        }
        return render(request, 'core/search_results.html', context)
    
    return redirect('dashboard')

@login_required
def analytics_dashboard(request):
    user = request.user
    # Total uploads
    total_uploads = Content.objects.filter(board__user=user).count()
    # Uploads by type
    uploads_by_type = Content.objects.filter(board__user=user).values('content_type').annotate(count=Count('id'))
    # Uploads over time (by month)
    uploads_over_time = Content.objects.filter(board__user=user)
    uploads_over_time = uploads_over_time.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
    # Most popular content (by likes)
    popular_content_qs = Content.objects.filter(board__user=user).annotate(like_count=Count('likes')).order_by('-like_count')[:5]
    popular_content = list(popular_content_qs.values('title', 'like_count'))
    # Engagement stats (received)
    total_likes = Content.objects.filter(board__user=user).aggregate(total=Count('likes'))['total']
    total_comments = Content.objects.filter(board__user=user).aggregate(total=Count('comments'))['total']
    total_views = Content.objects.filter(board__user=user).aggregate(total=Count('views'))['total'] if hasattr(Content, 'views') else 0
    # Engagement stats (given)
    given_likes = ContentLike.objects.filter(user=user).count()
    given_comments = ContentComment.objects.filter(user=user).count()

    context = {
        'total_uploads': total_uploads,
        'uploads_by_type': list(uploads_by_type),
        'uploads_over_time': list(uploads_over_time),
        'popular_content': popular_content,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_views': total_views,
        'given_likes': given_likes,
        'given_comments': given_comments,
    }
    return render(request, 'core/analytics.html', context)

def get_unread_notifications_count(request):
    if request.user.is_authenticated:
        return Notification.objects.filter(user=request.user, is_read=False).count()
    return 0

def about_us(request):
    return render(request, 'core/about_us.html')

@login_required
def delete_board(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    if request.user != board.user:
        messages.error(request, "Only the board owner can delete this board.")
        return redirect('board_detail', board_id=board.id)
    if request.method == 'POST':
        board.delete()
        messages.success(request, "Board deleted successfully!")
        return redirect('dashboard')
    return render(request, 'core/confirm_delete_board.html', {'board': board})

@login_required
def rename_board(request, board_id):
    board = get_object_or_404(Board, id=board_id)
    if request.user != board.user:
        messages.error(request, "Only the board owner can rename this board.")
        return redirect('board_detail', board_id=board.id)
    if request.method == 'POST':
        form = BoardForm(request.POST, instance=board)
        if form.is_valid():
            form.save()
            messages.success(request, "Board renamed successfully!")
            return redirect('board_detail', board_id=board.id)
    else:
        form = BoardForm(instance=board)
    return render(request, 'core/rename_board.html', {'form': form, 'board': board})
