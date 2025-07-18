# Generated by Django 5.2 on 2025-04-14 15:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_rename_uploaded_at_content_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='content',
            name='board',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='file_contents', to='core.board'),
        ),
        migrations.AlterField(
            model_name='content',
            name='content_type',
            field=models.CharField(choices=[('image', 'Image'), ('pdf', 'PDF'), ('doc', 'Document'), ('other', 'Other')], max_length=50),
        ),
    ]
