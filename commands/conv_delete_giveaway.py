from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, filters, ConversationHandler, CommandHandler, MessageHandler
from commands.chatFunc import *
from database import delete_giveaway, giveaway_exists, save_giveaway

WAIT_FOR_GIVEAWAY_ID, CONFIRM = range(2)


async def display_all_giveaways(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    giveaways = get_giveaways_of_a_user(update.effective_user.id)
    giveaways_names_ids = list(map(lambda x: f'{x.name}:\n{x.id}\n', giveaways))
    giveaways_names_ids_str = "\n".join(giveaways_names_ids)
    text = f'Send me an ID of the giveaway to delete from the list below\n{giveaways_names_ids_str}\nSend \"/cancel\" to cancel the operation.'
    await sendMessage(update, text)
    return WAIT_FOR_GIVEAWAY_ID


async def read_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    giveaway_id_str = update.message.text.strip()
    if not giveaway_exists(giveaway_id_str, update.effective_user.id):
        await sendMessage(update, f'there is no giveaway with the id  of \"{giveaway_id_str}\"\nPlease try again.')
        return WAIT_FOR_GIVEAWAY_ID
    
    reply_keyboard = [[giveaway_id_str], ['/cancel']]
    await update.message.reply_text(
        text= "Please send the id again to confirm deletion\nSend \"/cancel\" to cancel the operation.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True
        ),
    )
    return CONFIRM


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    giveaway_id_str = update.message.text.strip()
    if not giveaway_exists(giveaway_id_str, update.effective_user.id):
        await sendMessage(update, f'there is no giveaway with the id  of \"{giveaway_id_str}\"\nPlease try again.')
        return WAIT_FOR_GIVEAWAY_ID
    
    delete_giveaway(giveaway_id_str)
    await sendMessage(update, f'giveaway \"{giveaway_id_str}\" was deleted!')
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Deletion of a giveaway is canceled", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

conv_delete_giveaway_handler = ConversationHandler(
    entry_points=[CommandHandler("g_delete", display_all_giveaways)],
    states={
        WAIT_FOR_GIVEAWAY_ID: [MessageHandler(filters.Regex('^(?!/cancel)'), read_id)],
        CONFIRM: [MessageHandler(filters.Regex('^(?!/cancel)'), delete)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
