from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class Board(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    collaborators = models.ManyToManyField(User, related_name='collaborating_boards', blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug is unique
            original_slug = self.slug
            counter = 1
            while Board.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class BoardContent(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='text_contents')
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Content(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='file_contents')
    file = models.FileField(upload_to='media/')
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    content_type = models.CharField(max_length=50, choices=[
        ('image', 'Image'),
        ('pdf', 'PDF'),
        ('doc', 'Document'),
        ('video', 'Video'),
        ('other', 'Other')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    views = models.PositiveIntegerField(default=0)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.title or self.file.name

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])


class ContentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='likes')
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content')

    def __str__(self):
        return f"{self.user.username} liked {self.content.title}"


class ContentComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    commented_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} commented on {self.content.title}"


class BoardLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='likes')
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'board')

    def __str__(self):
        return f"{self.user.username} liked {self.board.title}"


class BoardComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    commented_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} commented on {self.board.title}"