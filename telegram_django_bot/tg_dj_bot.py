import time
import sys
import logging
from telegram import (
    Update,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaAudio,
    InputMediaAnimation,
    InputMediaDocument,
    Message,
    error,
)
from django.conf import settings  # LANGUAGES, USE_I18N
from django.utils import translation

from .models import BotMenuElem, MESSAGE_FORMAT
from .utils import add_log_action, ERROR_MESSAGE
from .telegram_lib_redefinition import (
    InlineKeyboardMarkupDJ,
    BotDJ,
    # TelegramDjangoObject2Json,
)


class TG_DJ_Bot(BotDJ):
    """
    no_error_send
    bot_menu_elem
    """

    def edit_or_send(bot, update, mess, buttons=None, only_send=False, decorate_buttons=True, **kwargs):
        if decorate_buttons and buttons:
            marked_buttons = InlineKeyboardMarkupDJ(buttons)
        else:
            marked_buttons = buttons

        if not marked_buttons:
            marked_buttons = None

        kwargs['reply_markup'] = marked_buttons

        res_mess, _ = bot.send_format_message(
            MESSAGE_FORMAT.TEXT,
            mess,
            update=update,
            only_send=only_send,
            **kwargs,
        )
        return res_mess

    def send_botmenuelem(bot, update, user, menu_elem):
        if menu_elem is None:
            menu_elem = BotMenuElem.objects.filter(empty_block=True, is_visable=True).first()

        media_files_list = None
        extra_kwargs = {}

        if menu_elem is None:
            if settings.USE_I18N:
                translation.activate(user.language_code)

            message_format = MESSAGE_FORMAT.TEXT
            mess = str(ERROR_MESSAGE)
        else:
            language_code = settings.LANGUAGE_CODE
            if settings.USE_I18N and user.language_code != settings.LANGUAGE_CODE:
                language_code = user.language_code

            message_format = menu_elem.message_format
            mess = menu_elem.get_message(language_code)
            buttons = menu_elem.get_buttons(language_code)

            if len(buttons):
                extra_kwargs['reply_markup'] = InlineKeyboardMarkupDJ(buttons)

            if menu_elem.message_format != MESSAGE_FORMAT.TEXT:
                media_file = menu_elem.telegram_file_code or open(menu_elem.media.path, 'rb')
                # if menu_elem.message_format == MESSAGE_FORMAT.PHOTO:
                #     media_file = telegram.InputMediaPhoto(media_file)
                # elif menu_elem.message_format == MESSAGE_FORMAT.VIDEO:
                #     media_file = telegram.InputMediaVideo(media_file)
                # elif menu_elem.message_format == MESSAGE_FORMAT.AUDIO:
                #     media_file = telegram.InputMediaAudio(media_file)
                # elif menu_elem.message_format == MESSAGE_FORMAT.GIF:
                #     media_file = telegram.InputMediaAnimation(media_file)
                # else:  # menu_elem.message_format == MESSAGE_FORMAT.DOCUMENT:
                #     media_file = telegram.InputMediaDocument(media_file)

                media_files_list = [media_file]

        response, media_codes = bot.send_format_message(
            message_format,
            mess,
            media_files_list,
            update,
            user.id,

            **extra_kwargs,
        )

        if menu_elem and menu_elem.telegram_file_code is None and menu_elem.media and len(media_codes) > 0:
            menu_elem.telegram_file_code = media_codes[0]
            menu_elem.save()
        return [response]

    def send_format_message(
            bot,
            message_format: str = MESSAGE_FORMAT.TEXT,
            text: str = None,
            media_files_list: list = None,
            update: Update = None,
            chat_id: int = None,
            only_send=False,

            **telegram_message_kwargs

    ):
        """

        :param message_format:
        :param text:
        :param media_files_list: for send_media_group must be prepared with InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
        :param update:
        :param chat_id:
        :param only_send:

        telegram_message_kwargs - parse_mode, timeout, reply_markup, disable_web_page_preview, disable_notification and maybe other
        :return:
        """

        input_media_dict = {
            MESSAGE_FORMAT.PHOTO: InputMediaPhoto,
            MESSAGE_FORMAT.VIDEO: InputMediaVideo,
            MESSAGE_FORMAT.AUDIO: InputMediaAudio,
            MESSAGE_FORMAT.GIF: InputMediaAnimation,
            MESSAGE_FORMAT.DOCUMENT: InputMediaDocument,
        }

        # checks data
        if message_format == MESSAGE_FORMAT.TEXT:
            if text is None:
                raise ValueError(f'text message could not be without text: got message_format={message_format}, text={text}')
        elif media_files_list is None:
            raise ValueError(f'not text message without media: got message_format={message_format}, media_files_list={media_files_list}')
        elif type(media_files_list) != list:
            raise ValueError(f'media_files_list should be list, got {type(media_files_list)}: {media_files_list}')
        elif len(media_files_list) == 0:
            raise ValueError(f'not text message without media: got message_format={message_format}, media_files_list={media_files_list}')
        elif message_format != MESSAGE_FORMAT.GROUP_MEDIA and len(media_files_list) > 1:
            raise ValueError(f'not group media message with more then 1 file: got message_format={message_format}, media_files_list={media_files_list}')
        elif message_format == MESSAGE_FORMAT.GROUP_MEDIA and (len(media_files_list) < 2 or len(media_files_list) > 10):
            raise ValueError(f'group media message should be with [2, 10] media, got {len(media_files_list)}')

        if update is None and chat_id is None:
            raise ValueError(f'update and chat_id could be together None -- to which chat send message then?')

        chat_id = chat_id or update.effective_user.id
        # text = str(text)  # for internalization (django __proxy__ error)

        telegram_message_kwargs = telegram_message_kwargs.copy()
        if not 'parse_mode' in telegram_message_kwargs:
            telegram_message_kwargs['parse_mode'] = 'HTML'

        delete_message_id = None
        is_editing_message = False
        if update and update.callback_query:
            prev_mess = update.callback_query.message
            if only_send:
                delete_message_id = prev_mess.message_id
            elif prev_mess.text         and message_format != MESSAGE_FORMAT.TEXT or \
                 prev_mess.text is None and message_format == MESSAGE_FORMAT.TEXT:
                # prev_mess.document and message_format != MESSAGE_FORMAT.DOCUMENT or \
                #  prev_mess.audio and message_format != MESSAGE_FORMAT.AUDIO or \
                #  prev_mess.photo and message_format != MESSAGE_FORMAT.PHOTO or \
                #  prev_mess.video and message_format != MESSAGE_FORMAT.VIDEO or \
                #  prev_mess.video and message_format != MESSAGE_FORMAT.VIDEO or \
                #  prev_mess.animation and message_format != MESSAGE_FORMAT.GIF or \
                #  prev_mess.text and message_format != MESSAGE_FORMAT.TEXT or \
                #  prev_mess.media_group_id:

                delete_message_id = prev_mess.message_id
            else:
                is_editing_message = True

        if delete_message_id:
            bot.delete_message(chat_id, delete_message_id)

        if is_editing_message:
            edit_message_id = update.callback_query.message.message_id
            telegram_message_kwargs.pop('disable_notification', None)
            if message_format == MESSAGE_FORMAT.TEXT:
                response = bot.edit_message_text(
                    text,
                    chat_id,
                    message_id=edit_message_id,
                    **telegram_message_kwargs
                )
            else:
                telegram_message_kwargs.pop('disable_web_page_preview', None)

                input_media = input_media_dict[message_format]

                media_file = input_media(
                    media_files_list[0],
                    caption=text,
                    parse_mode= telegram_message_kwargs.pop('parse_mode', None)
                )

                response = bot.edit_message_media(
                    chat_id,
                    message_id=edit_message_id,
                    media=media_file,
                    **telegram_message_kwargs
                )
        else:
            if message_format == MESSAGE_FORMAT.TEXT:
                response = bot.send_message(
                    chat_id,
                    text,
                    **telegram_message_kwargs
                )
            else:
                telegram_message_kwargs.pop('disable_web_page_preview', None)

                if message_format == MESSAGE_FORMAT.GROUP_MEDIA:
                    telegram_message_kwargs.pop('reply_markup', None)
                    response = bot.send_media_group(
                        chat_id,
                        media=media_files_list,

                    )
                else:
                    if message_format == MESSAGE_FORMAT.PHOTO:
                        telega_func = bot.send_photo
                    elif message_format == MESSAGE_FORMAT.AUDIO:
                        telega_func = bot.send_audio
                    elif message_format == MESSAGE_FORMAT.VIDEO:
                        telega_func = bot.send_video
                    elif message_format == MESSAGE_FORMAT.GIF:
                        telega_func = bot.send_animation
                    # elif message_format == MESSAGE_FORMAT.DOCUMENT:
                    else:
                        telega_func = bot.send_document

                    response = telega_func(
                        chat_id,
                        media_files_list[0],
                        caption=text,
                        **telegram_message_kwargs
                    )

        media_files_codes = []
        if type(response) == Message:
            media_file = response.document or response.audio or response.video or response.animation
            if media_file is None and response.photo:
                media_file = response.photo[-1] # last -- biggest
            if media_file:
                media_files_codes.append(media_file.file_id)

            # todo: add support for group media

        return response, media_files_codes

    def _message(
        self,
        endpoint: str,
        data,
        reply_to_message_id: int = None,
        disable_notification=None,
        reply_markup=None,
        allow_sending_without_reply=None,
        timeout=None,
        api_kwargs=None,
        protect_content=None,
    ):

        for field in ['text', 'caption']:
            if field in data and hasattr(data[field], '__call__'):
                data[field] = data[field].__call__()
            elif data.get(field):
                data[field] = str(data[field])

        return super()._message(
            endpoint,
            data,
            reply_to_message_id,
            disable_notification,
            reply_markup,
            allow_sending_without_reply,
            timeout,
            api_kwargs,
            protect_content
        )

    def task_send_message_handler(bot, user, func, func_args, func_kwargs):
        is_sent = False
        res_mess = None
        try:
            if settings.USE_I18N:
                translation.activate(user.language_code)

            res_mess = func(*func_args, **func_kwargs)
            is_sent = True
            time.sleep(0.035)

        except error.Unauthorized as e:
            logging.info(f'user blocked {e}, {user.id}\n')
            user.is_active = False
            user.save()
            add_log_action(user.id, 'TYPE_BLOCKED')

        except error.BadRequest as ee:
            if ee.message == 'Chat not found':
                user.is_active = False
                user.save()
                add_log_action(user.id, 'TYPE_BLOCKED')

            else:
                logging.error(
                    f'{ee.with_traceback(sys.exc_info()[2])} \n user={user.id}, {func}, {func_args}, {func_kwargs}'
                )

        except Exception as ee:
            logging.error(
                f'{ee.with_traceback(sys.exc_info()[2])} \n user={user.id}, {func}, {func_args}, {func_kwargs}'
            )
            time_in_seconds = 0.4
            try:
                if 'Flood control exceeded. Retry in ' in str(ee):
                    time_in_seconds = str(ee)[len('Flood control exceeded. Retry in '):].split()[0]
                    time_in_seconds = float(time_in_seconds)

                time.sleep(time_in_seconds)
            except Exception as e:
                time.sleep(0.5)

        return is_sent, res_mess


