# Generated by Django 4.2.13 on 2024-09-20 05:51

from django.db import migrations, models
import mainapps.vidoe_text.models


class Migration(migrations.Migration):

    dependencies = [
        ('vidoe_text', '0009_alter_textfile_audio_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textfile',
            name='text_file',
            field=models.FileField(blank=True, null=True, upload_to=mainapps.vidoe_text.models.text_file_upload_path),
        ),
    ]