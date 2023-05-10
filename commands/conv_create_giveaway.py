import json
from uuid import uuid4
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes, filters, ConversationHandler, CommandHandler, MessageHandler
from commands.chatFunc import *
from database import save_giveaway


WAIT_FOR_NAME, WAIT_FOR_DESCRIPTION, WAIT_FOR_PHOTO, WAIT_FOR_NOW = range(4)


async def start_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await sendMessage(update, "\nLets create a new giveaway!\nPlease enter the name of your giveaway.\n\nAt any stage send \"/cancel\" to stop the process.")
    return WAIT_FOR_NAME


async def start_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    with open(f'tmp_giveaway_name_id_{update.effective_user.id}', 'w') as out_file:
        json.dump({
            'name': update.message.text
        }, out_file)
    await sendMessage(
        update, f"Excellent! the name is \"{update.message.text}\"\nNow please enter description of your giveaway")
    return WAIT_FOR_DESCRIPTION


async def start_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    with open(f'tmp_giveaway_description_id_{update.effective_user.id}', 'w') as out_file:
        json.dump({
            'description': update.message.text
        }, out_file)
    await sendMessage(
        update, f"Excellent!\nNow send the image for your giveaway or send \"/skip\"")
    return WAIT_FOR_PHOTO


async def start_NOW(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    with open(f'tmp_giveaway_photo_id_{update.effective_user.id}', 'w') as out_file:
        json.dump({
            'photo_id': update.effective_message.photo[0].file_id
        }, out_file)
    await sendMessage(
        update, f"Excellent!\nNow tell me how many winners there will be?")
    return WAIT_FOR_NOW


async def skip_start_NOW(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    with open(f'tmp_giveaway_photo_id_{update.effective_user.id}', 'w') as out_file:
        json.dump({
            'photo_id': ''
        }, out_file)
    await sendMessage(
        update, f"Excellent!\nNow tell me how many winners there will be?")
    return WAIT_FOR_NOW


async def create_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    with open(f'tmp_giveaway_name_id_{update.effective_user.id}', 'r') as open_file:
        giveaway_name = json.load(open_file)
    with open(f'tmp_giveaway_description_id_{update.effective_user.id}', 'r') as open_file:
        giveaway_description = json.load(open_file)
    with open(f'tmp_giveaway_photo_id_{update.effective_user.id}', 'r') as open_file:
        giveaway_photo_id = json.load(open_file)
    os.remove(f'tmp_giveaway_name_id_{update.effective_user.id}')
    os.remove(f'tmp_giveaway_description_id_{update.effective_user.id}')
    os.remove(f'tmp_giveaway_photo_id_{update.effective_user.id}')
    giveaway_now = update.message.text
    newGiveaway = Giveaway(
        author=update.effective_user.id,
        authorNick=update.effective_user.name,
        name=giveaway_name['name'],
        description=giveaway_description['description'],
        NumberOfWinners=int(giveaway_now),
        id=uuid4(),
        subscribers=[],
        ended=False,
        winners=[],
        photoId=giveaway_photo_id['photo_id']
    )
    save_giveaway(newGiveaway)
    await sendMessage(update, f"Excellent! Your giveaway is now created!")
    await makeGiveawayPost(update, context, newGiveaway)
    await context.bot.sendMessage(chat_id=newGiveaway.author,
                                  text=get_line(LANG_ID, 'msg_g_created').
                                  format(newGiveaway.id, update.effective_chat.id, newGiveaway.numberOfWinners, newGiveaway.name, newGiveaway.description))
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Creation of a giveaway is canceled", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


conv_create_giveaway_handler = ConversationHandler(
    entry_points=[CommandHandler("g_create", start_name)],
    states={
        WAIT_FOR_NAME: [MessageHandler(filters.Regex('^(?!/cancel)'), start_description)],
        WAIT_FOR_DESCRIPTION: [MessageHandler(filters.Regex('^(?!/cancel)'), start_photo)],
        WAIT_FOR_PHOTO: [
            MessageHandler(filters.PHOTO, start_NOW),
            CommandHandler("skip", skip_start_NOW),
        ],
        WAIT_FOR_NOW: [MessageHandler(filters.Regex("[0-9]+$"), create_giveaway)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
