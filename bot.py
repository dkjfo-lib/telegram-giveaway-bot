import os
import os.path
import sys
from uuid import uuid4
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CallbackQueryHandler, MessageHandler, filters, ApplicationBuilder
from database import giveaway_exists, load_giveaway, save_giveaway, delete_giveaway
from giveaway import Giveaway
from userInfo import UserInfo
from locals import get_line
from conv_create_giveaway import conv_create_giveaway_handler
from logger import logger
from chatFunc import *
from constants import *

def restart_program():
    python = sys.executable
    os.execl(python, python, * sys.argv)


async def checkGiveawayId(update: Update, context :ContextTypes.DEFAULT_TYPE, giveawayId: str):
    """check params are correct"""
    if not giveawayId:
        await context.bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_id'))
        return False
    if not giveaway_exists(giveawayId):
        await context.bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_exists') % giveawayId)
        return False
    return True


def start(update: Update, context :ContextTypes.DEFAULT_TYPE):
    update.message.reply_text(get_line(LANG_ID, 'cmd_start'))


def help(update: Update, context :ContextTypes.DEFAULT_TYPE):
    update.message.reply_text(get_line(LANG_ID, 'cmd_help'))


async def restart(update: Update, context :ContextTypes.DEFAULT_TYPE):
    if not LOCAL:
        return
    await context.bot.sendMessage(chat_id=update.effective_chat.id,
                    text=get_line(LANG_ID, 'cmd_restart'))
    await deleteOriginalMessage(update)
    restart_program()


async def log_command_and_extract_params(update: Update, context :ContextTypes.DEFAULT_TYPE, command: str, keyword: str, params_count: int) -> bool:
    logger.info(f'processing command "{command}"')
    command_params = command.replace(keyword, '').strip().split("''")
    # check params are correct
    if len(command_params) != params_count:
        await context.bot.sendMessage(chat_id=update.effective_chat.id,
                        text=f'ожидалось {params_count} параметров, было отпралено {len(command_params)}')
        return None
    return command_params


async def giveaway_Delete(update: Update, context :ContextTypes.DEFAULT_TYPE, command: str):
    logger.info('processing command "{0}"'.format(command))
    giveawayId = command.replace('/g_delete', '').strip()
    if not checkGiveawayId(update, giveawayId):
        return
    giveaway = load_giveaway(giveawayId)
    if giveaway.is_Author(update.effective_user.id):
        delete_giveaway(giveawayId)
        await context.bot.sendMessage(chat_id=giveaway.author,
                        text=f'Розыгрыш {giveaway.id} успешно удален')
    else:
        await sendDontHavePermission(update, giveaway, LANG_ID)


async def giveaway_post(update: Update, context :ContextTypes.DEFAULT_TYPE, command: str):
    logger.info('processing command "{0}"'.format(command))
    giveawayId = command.replace('/g_post', '').strip()
    if not checkGiveawayId(update, giveawayId):
        return
    giveaway = load_giveaway(giveawayId)

    if (not update.effective_user) or (giveaway.is_Author(update.effective_user.id)):
        makeGiveawayPost(giveaway, update)
        await context.bot.sendMessage(chat_id=giveaway.author,
                        text=get_line(LANG_ID, 'msg_g_post_created').
                        format(giveaway.id, update.effective_chat.id))
    else:
        await sendDontHavePermission(update, giveaway, LANG_ID)
    await deleteOriginalMessage(update)


def divide_chunks(list, chunk_length: int):
    for i in range(0, len(list), chunk_length):
        yield list[i:i + chunk_length]


def parseNameHTML(user: UserInfo):
    if user.name.startswith('@'):
        return user.name
    else:
        return "<a href='tg://user?id=%s'>%s</a>" % (user.id, user.name)


async def giveaway_subs(update: Update, context :ContextTypes.DEFAULT_TYPE, command: str):
    logger.info('processing command "{0}"'.format(command))
    giveawayId = command.replace('/g_subs', '').strip()
    if not checkGiveawayId(update, giveawayId):
        return
    giveaway = load_giveaway(giveawayId)
    if (not update.effective_user) or (update.effective_user.id == giveaway.author):

        subbedToChannel_subs = giveaway.onlySubbedToChannel(
            context.bot, "chat_id", giveaway.subscribers)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                         parse_mode=constants.ParseMode.HTML,
                         text=get_line(LANG_ID, 'cmd_giveaway_subs').format(str(len(subbedToChannel_subs))))

        subs_list = [parseNameHTML(sub) for sub in subbedToChannel_subs]
        subs_chunks = divide_chunks(subs_list, 100)
        for subs_chunk in subs_chunks:
            subs_tags = '\n'.join(subs_chunk)
            print(subs_tags)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                             parse_mode=constants.ParseMode.HTML,
                             text=subs_tags)
    else:
        await sendDontHavePermission(update, giveaway, LANG_ID)
    await deleteOriginalMessage(update)


async def giveaway_finish(update: Update, context :ContextTypes.DEFAULT_TYPE, command: str):
    logger.info('processing command "{0}"'.format(command))
    giveawayId = command.replace('/g_finish', '').strip()
    if not checkGiveawayId(update, giveawayId):
        return
    giveaway = load_giveaway(giveawayId)
    if (not update.effective_user) or (update.effective_user.id == giveaway.author):
        if (not giveaway.ended):
            giveaway.endGiveaway(context.bot)
            await display_winners_win_rate(update, giveaway)
        winners = '\n'.join([parseNameHTML(sub) for sub in giveaway.winners])
        await makeGiveawayEndPost(giveaway, update, winners)
        save_giveaway(giveaway)
        await deleteOriginalMessage(update)
    else:
        await sendDontHavePermission(update, giveaway, LANG_ID)


async def giveaway_reroll_winner(update: Update, context :ContextTypes.DEFAULT_TYPE, command: str):
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
        await context.bot.send_message(chat_id=update.effective_chat.id,
                         text='Комманда доступна только в чате бота')
    elif isChatWithAuthor(update, giveaway):
        giveaway.reroll_user(context.bot, user_id)
        winners = '\n'.join([parseNameHTML(sub) for sub in giveaway.winners])
        await makeGiveawayEndPost(giveaway, update, winners)
        await display_winners_win_rate(update, giveaway)
        save_giveaway(giveaway)
    else:
        await sendDontHavePermission(update, giveaway, LANG_ID)
    await deleteOriginalMessage(update)


async def giveaway_edit(update: Update, context :ContextTypes.DEFAULT_TYPE, command: str, photo_id: str = None):
    logger.info('processing command "{0}"'.format(command))
    giveawayInfo = command.replace('/g_edit', '').strip().split("''")
    # check params are correct
    if len(giveawayInfo) != 4:
        await context.bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_wr_edit_params') % len(giveawayInfo))
        return
    giveawayId = giveawayInfo[0]
    newNoW = giveawayInfo[1]
    newName = giveawayInfo[2]
    newDescription = giveawayInfo[3]
    if not checkGiveawayId(update, giveawayId):
        return
    if not newName:
        await context.bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_name'))
        return
    if not newDescription:
        await context.bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_descr'))
        return
    if (not newNoW) or (not newNoW.isdigit()):
        await context.bot.sendMessage(chat_id=update.effective_chat.id,
                        text=get_line(LANG_ID, 'err_no_g_NoW'))
        return
    if int(newNoW) < 1:
        await context.bot.sendMessage(chat_id=update.effective_chat.id,
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
        await sendDontHavePermission(update, giveaway, LANG_ID)
    await deleteOriginalMessage(update)


def callback_query_handler(update: Update, context :ContextTypes.DEFAULT_TYPE):
    logger.info('processing callback "{0}"'.format(update.callback_query.data))
    update.callback_query.answer("Вы участвуете!")
    callbackData = update.callback_query.data
    if callbackData.startswith(SUBSCRIBE_KEYWORD):
        giveawayId = callbackData.replace(SUBSCRIBE_KEYWORD, '')
        giveaway = load_giveaway(giveawayId)
        user = UserInfo(update.effective_user.id, update.effective_user.name)
        # check subscription
        isSubbedToGiveaway = giveaway.isSubbedToGiveaway(user)
        if not isSubbedToGiveaway:
            logger.info('User {0}'.format(user.name))
            giveaway.subscribers.append(user)
            save_giveaway(giveaway)
        logger.info(
            f'user:{user.name} alreadySubbedToGiveaway: {isSubbedToGiveaway}')


def displayGiveawayInfo(update: Update, context :ContextTypes.DEFAULT_TYPE):
    load_giveaway()


async def forwarder(update: Update, context :ContextTypes.DEFAULT_TYPE):

    text: str = ''
    photoId: str = ''

    if update.effective_message.caption != None:
        text = update.effective_message.caption
    if update.effective_message.text != None:
        text = update.effective_message.text

    if len(update.effective_message.photo) > 0:
        photoId = update.effective_message.photo[0].file_id

    logger.info('Processing new message\n\nText:"{0}"\n\nphotoId:"{1}"\n'.
             format(text, photoId))

    if not text:
        return

    if text.startswith('/restart'):
        logger.info('launching restart')
        restart(update, context)

    if text.startswith('/start'):
        logger.info('launching start')
        await start(update, context)

    if text.startswith('/help'):
        logger.info('launching help')
        await help(update, context)

    # if text.startswith('/g_create'):
    #     logger.info('launching create')
    #     await giveaway_create(update, context, text, photoId)

    if text.startswith('/g_edit'):
        logger.info('launching edit')
        await giveaway_edit(update, context, text, photoId)

    if text.startswith('/g_post'):
        logger.info('launching post')
        await giveaway_post(update, context, text)

    if text.startswith('/g_subs'):
        logger.info('launching subs')
        await giveaway_subs(update, context, text)

    if text.startswith('/g_finish'):
        logger.info('launching finish')
        await giveaway_finish(update, context, text)

    if text.startswith('/g_delete'):
        logger.info('launching delete')
        await giveaway_Delete(update, context, text)

    if text.startswith('/g_reroll'):
        logger.info('launching reroll')
        await giveaway_reroll_winner(update, context, text)

def launch_bot():
    logger.info(f'creating bot with token:"{BOT_TOKEN}"...')
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CallbackQueryHandler(callback_query_handler))
    application.add_handler(MessageHandler(filters.Regex("^(/start|/g_edit|/g_post|/g_subs|/g_finish|/g_delete|/g_reroll)$"), forwarder))
    application.add_handler(conv_create_giveaway_handler)
    logger.info(f'bot successfully created.')

    if LOCAL:
        logger.info('polling messages...')
        application.run_polling()
    else:
        logger.info(
            f'setting webhook on "{WEBHOOK_URL}" listening on address "{IP}:{PORT}"...')
        application.run_webhook(
            listen=IP,
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=WEBHOOK_URL)
        logger.info(f'Webhook deployed!')
