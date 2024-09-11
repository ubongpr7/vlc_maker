# Generated by Django 4.2.16 on 2024-09-07 23:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vidoe_text', '0002_alter_textfile_subtitle_box_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='AudioClip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('audio_file', models.FileField(upload_to='audio_clips/')),
                ('duration', models.FloatField(blank=True, null=True)),
                ('voice_id', models.CharField(max_length=255)),
            ],
        ),
        migrations.RemoveField(
            model_name='textfile',
            name='processed',
        ),
        migrations.AddField(
            model_name='textfile',
            name='audio_file',
            field=models.FileField(blank=True, null=True, upload_to='audio_files/'),
        ),
        migrations.AddField(
            model_name='textfile',
            name='user',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='textfile',
            name='api_key',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='textfile',
            name='font_color',
            field=models.CharField(max_length=7),
        ),
        migrations.AlterField(
            model_name='textfile',
            name='font_file',
            field=models.FileField(blank=True, null=True, upload_to='fonts/'),
        ),
        migrations.AlterField(
            model_name='textfile',
            name='font_size',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='textfile',
            name='resolution',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='textfile',
            name='subtitle_box_color',
            field=models.CharField(blank=True, max_length=7, null=True),
        ),
        migrations.AlterField(
            model_name='textfile',
            name='text_file',
            field=models.FileField(upload_to='text_files/'),
        ),
        migrations.AlterField(
            model_name='textfile',
            name='voice_id',
            field=models.CharField(max_length=100),
        ),
        migrations.CreateModel(
            name='TextLineVideoClip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('video_file_path', models.FileField(upload_to='text_video_clips/')),
                ('line_number', models.IntegerField()),
                ('timestamp_start', models.FloatField(blank=True, null=True)),
                ('timestamp_end', models.FloatField(blank=True, null=True)),
                ('text_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='video_clips', to='vidoe_text.textfile')),
            ],
        ),
    ]