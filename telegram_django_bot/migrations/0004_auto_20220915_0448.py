# Generated by Django 3.1 on 2022-09-15 04:48

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_django_bot', '0003_botmenuelem_message_format'),
    ]

    operations = [
        migrations.AlterField(
            model_name='botmenuelem',
            name='buttons_db',
            field=models.TextField(blank=True, help_text='InlineKeyboardMarkup buttons list, ({"text": , "url" or "callback_data"})', null=True),
        ),
        migrations.AlterField(
            model_name='botmenuelem',
            name='callbacks_db',
            field=models.TextField(blank=True, help_text='List of regular expressions (so far only an explicit list) for callbacks that call this menu block', null=True),
        ),
        migrations.AlterField(
            model_name='botmenuelem',
            name='command',
            field=models.CharField(blank=True, help_text='Bot command that can call this menu block', max_length=32, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='botmenuelem',
            name='empty_block',
            field=models.BooleanField(default=False, help_text='This block will be shown if there is no catching callback'),
        ),
        migrations.AlterField(
            model_name='botmenuelem',
            name='is_visable',
            field=models.BooleanField(default=True, help_text='Whether to display this menu block to users (can be hidden and not deleted for convenience)'),
        ),
        migrations.AlterField(
            model_name='botmenuelem',
            name='media',
            field=models.FileField(blank=True, help_text='File attachment to the message', null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='botmenuelem',
            name='message',
            field=models.TextField(help_text='Text message'),
        ),
        migrations.AlterField(
            model_name='botmenuelem',
            name='telegram_file_code',
            field=models.CharField(blank=True, help_text='File code in telegram (must be deleted when replacing file)', max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name='teledeeplink',
            name='link',
            field=models.CharField(max_length=64, validators=[django.core.validators.RegexValidator('^[a-zA-Z0-9_-]+$', 'Telegram is only accepted letters, numbers and signs - _')]),
        ),
        migrations.AlterField(
            model_name='trigger',
            name='botmenuelem',
            field=models.ForeignKey(help_text='which trigger message to show', on_delete=django.db.models.deletion.PROTECT, to='telegram_django_bot.botmenuelem'),
        ),
        migrations.AlterField(
            model_name='trigger',
            name='min_duration',
            field=models.DurationField(help_text='the minimum period in which there can be 1 notification for a user of this type'),
        ),
        migrations.AlterField(
            model_name='trigger',
            name='priority',
            field=models.IntegerField(default=1, help_text='the more topics will be executed first'),
        ),
        migrations.CreateModel(
            name='BotMenuElemAttrText',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dttm_added', models.DateTimeField(default=django.utils.timezone.now)),
                ('language_code', models.CharField(max_length=2)),
                ('default_text', models.TextField(help_text='The text which should be translate')),
                ('translated_text', models.TextField(help_text='Default_text Translation', null=True)),
                ('bot_menu_elem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='telegram_django_bot.botmenuelem')),
            ],
            options={
                'unique_together': {('bot_menu_elem', 'language_code', 'default_text')},
                'index_together': {('bot_menu_elem', 'language_code', 'default_text')},
            },
        ),
        migrations.AlterField(
            model_name='botmenuelem',
            name='message_format',
            field=models.CharField(
                choices=[('T', 'Text'), ('P', 'Image'), ('D', 'Document'), ('A', 'Audio'), ('V', 'Video'),
                         ('G', 'GIF/animation'), ('GM', 'Media Group')], default='T', max_length=2),
        ),
    ]
