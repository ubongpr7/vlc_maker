# Generated by Django 4.2.16 on 2024-09-08 02:31

from django.db import migrations, models
import mainapps.vidoe_text.models


class Migration(migrations.Migration):

    dependencies = [
        ('vidoe_text', '0004_textlinevideoclip_video_file_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textlinevideoclip',
            name='video_file_path',
            field=models.FileField(upload_to=mainapps.vidoe_text.models.text_clip_upload_path),
        ),
    ]
