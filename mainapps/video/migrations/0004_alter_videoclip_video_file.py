# Generated by Django 4.2.16 on 2024-09-08 02:31

from django.db import migrations, models
import mainapps.video.models


class Migration(migrations.Migration):

    dependencies = [
        ('video', '0003_videoclip_is_favorite_videoclip_user_delete_userclip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videoclip',
            name='video_file',
            field=models.FileField(upload_to=mainapps.video.models.video_clip_upload_path),
        ),
    ]