from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, constants
from telegram.ext import ContextTypes
from database import get_giveaways_of_a_user
from giveaway import Giveaway
from locals import get_line
from constants import *

async def sendMessage(update: Update, message: str):
    await update.get_bot().send_message(chat_id=update.effective_chat.id,
                            text=message)

async def deleteOriginalMessage(update: Update):
    if not update.message:
        await update.get_bot().delete_message(chat_id=update.channel_post.chat_id,
                                message_id=update.channel_post.message_id
                                )
        return
    await update.get_bot().deleteMessage(chat_id=update.message.chat_id,
                            message_id=update.message.message_id
                            )

async def sendDontHavePermission(update: Update, giveaway: Giveaway, langId: int):
    await update.get_bot().sendMessage(chat_id=update.effective_chat.id,
                            text=get_line(langId, 'err_no_access') % giveaway.authorNick)

def isChatWithAuthor(update: Update, giveaway: Giveaway):
    return (update.effective_user.id == giveaway.author) & (update.effective_chat.id == giveaway.author)


async def makeGiveawayPost(update: Update, context :ContextTypes.DEFAULT_TYPE, giveaway: Giveaway):
    button_s = [InlineKeyboardButton(
        text=get_line(LANG_ID, 'btn_sub_txt'), callback_data=SUBSCRIBE_KEYWORD + str(giveaway.id))]
    keyboard = InlineKeyboardMarkup([button_s])
    text = '<strong>{0}</strong>\n{1}'.format(
        giveaway.name, giveaway.description)
    if giveaway.photoId:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=giveaway.photoId,
            caption=text,
            parse_mode=constants.ParseMode.HTML,
            reply_markup=keyboard,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=constants.ParseMode.HTML,
            reply_markup=keyboard,
        )


async def makeGiveawayEndPost(update: Update, context :ContextTypes.DEFAULT_TYPE, giveaway: Giveaway, winners: str):
    text = get_line(LANG_ID, 'post_g_finished').format(giveaway.name, winners)
    if giveaway.photoId:
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=giveaway.photoId,
            caption=text,
            parse_mode=constants.ParseMode.HTML,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode=constants.ParseMode.HTML,
        )


async def display_winners_win_rate(update: Update, context :ContextTypes.DEFAULT_TYPE, giveaway: Giveaway):
    """creating current giveaway and a list of all other giveaways of a user"""
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
    await context.bot.sendMessage(chat_id=update.effective_user.id, text=text)
