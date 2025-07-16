# Register your models here.
from django.contrib import admin
from .models import Board, BoardContent, Content, ContentLike, ContentComment, BoardLike, BoardComment
# from .models import Content
admin.site.register(Board)
admin.site.register(BoardContent)
admin.site.register(Content)
admin.site.register(ContentLike)
admin.site.register(ContentComment)
admin.site.register(BoardLike)
admin.site.register(BoardComment)
# admin.site.register(Content)
