from ntpath import join
import os
import os.path
import sys
from typing import List
from uuid import uuid4
from dotenv import load_dotenv
import telegram
from telegram.ext.updater import Updater
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.commandhandler import CommandHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.conversationhandler import ConversationHandler
from telegram.ext.filters import Filters
from telegram.ext.defaults import Defaults
from telegram.ext import CallbackQueryHandler
from telegram.parsemode import ParseMode
from database import giveaway_exists, load_giveaway, save_giveaway, delete_giveaway, get_giveaways_of_a_user
from giveaway import Giveaway
from log import Log
from userInfo import UserInfo
from chatFunc import ChatFunc
from locals import get_line

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
LOCAL = bool(int(os.getenv('LOCAL')))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
IP = os.getenv('IP')
PORT = os.getenv('PORT')
LANG_ID = int(os.getenv('LANG_ID'))

SUBSCRIBE_KEYWORD = 'subscribe_'
UNSUBSCRIBE_KEYWORD = 'unsubscribe_'

updater = Updater(BOT_TOKEN, use_context=True)
bot = telegram.Bot(token=BOT_TOKEN)
bot.defaults = Defaults(timeout=180)
chatFunctions = ChatFunc(bot)
log = Log()


def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)


def makeGiveawayPost(giveaway: Giveaway, update: Update):
    button_s = [telegram.InlineKeyboardButton(
        text=get_line(LANG_ID, 'btn_sub_txt'), callback_data=SUBSCRIBE_KEYWORD + str(giveaway.id))]
    keyboard = telegram.InlineKeyboardMarkup([button_s])
    text = '<strong>{0}</strong>\n{1}'.format(
        giveaway.name, giveaway.description)
    if giveaway.photoId:
        bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=giveaway.photoId,
            caption=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )
    else:
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
        )


def makeGiveawayEndPost(giveaway: Giveaway, update: Update, winners: str):
    text = get_line(LANG_ID, 'post_g_finished').format(giveaway.name, winners)
    if giveaway.photoId:
        bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=giveaway.photoId,
            caption=text,
            parse_mode=ParseMode.HTML,
        )
    else:
        bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=ParseMode.HTML,
        )


def display_winners_win_rate(update: Update, giveaway: Giveaway):
    # creating current giveaway and a list of all other giveaways of a user
    other_user_giveaways = get_giveaways_of_a_user(update.effective_user.id)
    for other_giveaway in other_user_giveaways:
        if other_giveaway.id == giveaway.id:
            other_user_giveaways.remove(other_giveaway)

    giveaway_count = len(other_user_giveaways)
    text = f'Из {giveaway_count} проведенных вами конкурсов:'
    # calculating win rate of current giveaway winners
    for winner in giveaway.winners:
        user_win_count = 0
        for other_giveaway in other_user_giveaways:
            for other_giveaway_winner in other_giveaway.winners:
                if other_giveaway_winner.id == winner.id:
                    user_win_count += 1
        text += f'\n{winner.name} победил {user_win_count} раз'
    bot.sendMessage(chat_id=update.effective_user.id, text=text)


def checkGiveawayId(update: Update, giveawayId: str):
    # check params are correct
    if not giveawayId:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_id'))
        return False
    if not giveaway_exists(giveawayId):
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_exists') % giveawayId)
        return False
    return True


def start(update: Update, context: CallbackContext):
    update.message.reply_text(get_line(LANG_ID, 'cmd_start'))


def help(update: Update, context: CallbackContext):
    update.message.reply_text(get_line(LANG_ID, 'cmd_help'))


def restart(update: Update, context: CallbackContext):
    if not LOCAL:
        return
    bot.sendMessage(chat_id=update.effective_chat.id,
                    text=get_line(LANG_ID, 'cmd_restart'))
    chatFunctions.deleteOriginalMessage(update)
    restart_program()


def log_command_and_extract_params(update: Update, command: str, keyword: str, params_count: int) -> bool:
    log.info(f'processing command "{command}"')
    command_params = command.replace(keyword, '').strip().split("''")
    # check params are correct
    if len(command_params) != params_count:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=f'ожидалось {params_count} параметров, было отпралено {len(command_params)}')
        return None
    return command_params


def giveaway_create(update: Update, command: str, photo_id: str = None):
    log.info('processing command "{0}"'.format(command))
    giveawayInfo = command.replace('/g_create', '').strip().split("''")
    # check params are correct
    if len(giveawayInfo) != 3:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_wr_create_params') % len(giveawayInfo))
        return
    if not giveawayInfo[1]:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_name'))
        return
    if not giveawayInfo[2]:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_descr'))
        return
    if (not giveawayInfo[0]) or (not giveawayInfo[0].isdigit()):
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_NoW'))
        return
    if int(giveawayInfo[0]) < 1:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_wr_g_NoW'))
        return

    newGiveaway = Giveaway(
        author=update.effective_user.id,
        authorNick=update.effective_user.name,
        name=giveawayInfo[1],
        description=giveawayInfo[2],
        NumberOfWinners=int(giveawayInfo[0]),
        id=uuid4(),
        subscribers=[],
        ended=False,
        winners=[],
        photoId=photo_id
    )
    save_giveaway(newGiveaway)

    makeGiveawayPost(newGiveaway, update)
    bot.sendMessage(chat_id=newGiveaway.author,
                    text=get_line(LANG_ID, 'msg_g_created').
                    format(newGiveaway.id, update.effective_chat.id, newGiveaway.numberOfWinners, newGiveaway.name, newGiveaway.description))
    chatFunctions.deleteOriginalMessage(update)


def giveaway_Delete(update: Update, command: str):
    log.info('processing command "{0}"'.format(command))
    giveawayId = command.replace('/g_delete', '').strip()
    if not checkGiveawayId(update, giveawayId):
        return
    giveaway = load_giveaway(giveawayId)
    if giveaway.is_Author(update.effective_user.id):
        delete_giveaway(giveawayId)
        bot.sendMessage(chat_id=giveaway.author,
                        text=f'Розыгрыш {giveaway.id} успешно удален')
    else:
        chatFunctions.sendDontHavePermission(update, giveaway, LANG_ID)


def giveaway_post(update: Update, command: str):
    log.info('processing command "{0}"'.format(command))
    giveawayId = command.replace('/g_post', '').strip()
    if not checkGiveawayId(update, giveawayId):
        return
    giveaway = load_giveaway(giveawayId)

    if (not update.effective_user) or (giveaway.is_Author(update.effective_user.id)):
        makeGiveawayPost(giveaway, update)
        bot.sendMessage(chat_id=giveaway.author,
                        text=get_line(LANG_ID, 'msg_g_post_created').
                        format(giveaway.id, update.effective_chat.id))
    else:
        chatFunctions.sendDontHavePermission(update, giveaway, LANG_ID)
    chatFunctions.deleteOriginalMessage(update)


def divide_chunks(list, chunk_length: int):
    for i in range(0, len(list), chunk_length):
        yield list[i:i + chunk_length]


def parseNameHTML(user: UserInfo):
    if user.name.startswith('@'):
        return user.name
    else:
        return "<a href='tg://user?id=%s'>%s</a>" % (user.id, user.name)


def giveaway_subs(update: Update, command: str):
    log.info('processing command "{0}"'.format(command))
    giveawayId = command.replace('/g_subs', '').strip()
    if not checkGiveawayId(update, giveawayId):
        return
    giveaway = load_giveaway(giveawayId)
    if (not update.effective_user) or (update.effective_user.id == giveaway.author):

        subbedToChannel_subs = giveaway.onlySubbedToChannel(
            bot, "chat_id", giveaway.subscribers)
        bot.send_message(chat_id=update.effective_chat.id,
                         parse_mode=ParseMode.HTML,
                         text=get_line(LANG_ID, 'cmd_giveaway_subs').format(str(len(subbedToChannel_subs))))

        subs_list = [parseNameHTML(sub) for sub in subbedToChannel_subs]
        subs_chunks = divide_chunks(subs_list, 100)
        for subs_chunk in subs_chunks:
            subs_tags = '\n'.join(subs_chunk)
            print(subs_tags)
            bot.send_message(chat_id=update.effective_chat.id,
                             parse_mode=ParseMode.HTML,
                             text=subs_tags)
    else:
        chatFunctions.sendDontHavePermission(update, giveaway, LANG_ID)
    chatFunctions.deleteOriginalMessage(update)


def giveaway_finish(update: Update, command: str):
    log.info('processing command "{0}"'.format(command))
    giveawayId = command.replace('/g_finish', '').strip()
    if not checkGiveawayId(update, giveawayId):
        return
    giveaway = load_giveaway(giveawayId)
    if (not update.effective_user) or (update.effective_user.id == giveaway.author):
        if (not giveaway.ended):
            giveaway.endGiveaway(bot)
            display_winners_win_rate(update, giveaway)
        winners = '\n'.join([parseNameHTML(sub) for sub in giveaway.winners])
        makeGiveawayEndPost(giveaway, update, winners)
        save_giveaway(giveaway)
        chatFunctions.deleteOriginalMessage(update)
    else:
        chatFunctions.sendDontHavePermission(update, giveaway, LANG_ID)


def giveaway_reroll_winner(update: Update, command: str):
    command_params = log_command_and_extract_params(
        update, command, '/g_reroll', 2)
    if not command_params:
        return
    giveawayId = command_params[0]
    user_id = command_params[1]
    if not checkGiveawayId(update, giveawayId):
        return
    giveaway = load_giveaway(giveawayId)
    if (not update.effective_user) or (not update.effective_chat.id == update.effective_user.id):
        bot.send_message(chat_id=update.effective_chat.id,
                         text='Комманда доступна только в чате бота')
    elif chatFunctions.isChatWithAuthor(update, giveaway):
        giveaway.reroll_user(bot, user_id)
        winners = '\n'.join([parseNameHTML(sub) for sub in giveaway.winners])
        makeGiveawayEndPost(giveaway, update, winners)
        display_winners_win_rate(update, giveaway)
        save_giveaway(giveaway)
    else:
        chatFunctions.sendDontHavePermission(update, giveaway, LANG_ID)
    chatFunctions.deleteOriginalMessage(update)


def giveaway_edit(update: Update, command: str, photo_id: str = None):
    log.info('processing command "{0}"'.format(command))
    giveawayInfo = command.replace('/g_edit', '').strip().split("''")
    # check params are correct
    if len(giveawayInfo) != 4:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_wr_edit_params') % len(giveawayInfo))
        return
    giveawayId = giveawayInfo[0]
    newNoW = giveawayInfo[1]
    newName = giveawayInfo[2]
    newDescription = giveawayInfo[3]
    if not checkGiveawayId(update, giveawayId):
        return
    if not newName:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_name'))
        return
    if not newDescription:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_descr'))
        return
    if (not newNoW) or (not newNoW.isdigit()):
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_NoW'))
        return
    if int(newNoW) < 1:
        bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_wr_g_NoW'))
        return

    giveaway = load_giveaway(giveawayId)
    if update.effective_user.id == giveaway.author:
        giveaway.name = newName
        giveaway.description = newDescription
        giveaway.numberOfWinners = int(newNoW)
        giveaway.photoId = photo_id
        save_giveaway(giveaway)
        makeGiveawayPost(giveaway, update)
    else:
        chatFunctions.sendDontHavePermission(update, giveaway, LANG_ID)
    chatFunctions.deleteOriginalMessage(update)


def callback_query_handler(update: Update, context: CallbackContext):
    log.info('processing callback "{0}"'.format(update.callback_query.data))
    update.callback_query.answer("Вы участвуете!")
    callbackData = update.callback_query.data
    if callbackData.startswith(SUBSCRIBE_KEYWORD):
        giveawayId = callbackData.replace(SUBSCRIBE_KEYWORD, '')
        giveaway = load_giveaway(giveawayId)
        user = UserInfo(update.effective_user.id, update.effective_user.name)
        # check subscription
        isSubbedToGiveaway = giveaway.isSubbedToGiveaway(user)
        if not isSubbedToGiveaway:
            log.info('User {0}'.format(user.name))
            giveaway.subscribers.append(user)
            save_giveaway(giveaway)
        log.info(
            f'user:{user.name} alreadySubbedToGiveaway: {isSubbedToGiveaway}')


def displayGiveawayInfo(update: Update, context: CallbackContext):
    load_giveaway()


def forwarder(update: Update, context: CallbackContext):

    text: str = ''
    photoId: str = ''

    if update.effective_message.caption != None:
        text = update.effective_message.caption
    if update.effective_message.text != None:
        text = update.effective_message.text

    if len(update.effective_message.photo) > 0:
        photoId = update.effective_message.photo[0].file_id

    log.info('Processing new message\n\nText:"{0}"\n\nphotoId:"{1}"\n'.
             format(text, photoId))

    if not text:
        return

    if text.startswith('/restart'):
        log.info('launching restart')
        restart(update, context)

    if text.startswith('/start'):
        log.info('launching start')
        start(update, context)

    if text.startswith('/help'):
        log.info('launching help')
        help(update, context)

    if text.startswith('/g_create'):
        log.info('launching create')
        giveaway_create(update, text, photoId)

    if text.startswith('/g_edit'):
        log.info('launching edit')
        giveaway_edit(update, text, photoId)

    if text.startswith('/g_post'):
        log.info('launching post')
        giveaway_post(update, text)

    if text.startswith('/g_subs'):
        log.info('launching subs')
        giveaway_subs(update, text)

    if text.startswith('/g_finish'):
        log.info('launching finish')
        giveaway_finish(update, text)

    if text.startswith('/g_delete'):
        log.info('launching delete')
        giveaway_Delete(update, text)

    if text.startswith('/g_reroll'):
        log.info('launching reroll')
        giveaway_reroll_winner(update, text)

def launch_bot():

    # updater.dispatcher.add_handler(ConversationHandler(
    #         entry_points=[CallbackQueryHandler(callback_query_handler)],
    #         states={
    #             1: [MessageHandler(Filters.text, name_input_by_user)],
    #             2: [CallbackQueryHandler(button_click_handler)]
    #         },
    #         fallbacks=[CommandHandler('cancel', cancel)],
    #         per_user=True
    #     ))
    updater.dispatcher.add_handler(CallbackQueryHandler(callback_query_handler))
    updater.dispatcher.add_handler(MessageHandler(Filters.all, forwarder))

    log.info('LOCAL:%s' % LOCAL)
    if LOCAL:
        log.info('polling messages...')
        updater.start_polling()
    else:
        log.info('setting webhook on "{0}" listening on address "{1}:{2}"...'.
                format(WEBHOOK_URL, IP, PORT))
        updater.start_webhook(listen=IP,
                            port=int(PORT),
                            url_path=BOT_TOKEN,
                            webhook_url=WEBHOOK_URL)
        updater.bot.set_webhook(WEBHOOK_URL)
        bot.set_webhook(WEBHOOK_URL)
    updater.idle()
