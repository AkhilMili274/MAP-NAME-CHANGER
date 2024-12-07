import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatAction

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = "7570195316:AAGU9gazYk9JYeet90Ne5FIe0OP-R5kQOiM"  # Replace with your bot token

# Temporary file storage
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Conversation states
ASK_NAME, ASK_COLOR, ASK_TITLE = range(3)

# Hex code mappings
color_codes = {
    "Red": "[FF0000]",
    "Blue": "[0000FF]",
    "Green": "[00FF00]",
    "Yellow": "[FFFF00]",
    "NO Name": None,
}

hex_values = {
    "50×50": "88 01 19",
    "100×100": "88 01 0a",
    "BERMUDA": "88 01 01",
    "NEXTERA": "88 01 16",
    "NO LAND": "88 01 20",
}

# Hex converter API
HEX_CONVERTER_API = "https://hex-sooty.vercel.app/protobuf_to_hex"

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Please send me a meta file to start processing."
    )

# Info command handler
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    info_message = (
        "THIS BOT WAS MADE BY @I_SHOW_AKIRU\n\n"
        "THIS METHOD IS FOUND BY @ShahGCreator\n\n"
        "HOSTING BY @Garena420"
    )
    await update.message.reply_text(info_message)

# File handling function
async def handle_file(update: Update, context):
    file = update.message.document
    if not file:
        await update.message.reply_text("Please send a valid meta file.")
        return

    file_path = os.path.join(UPLOAD_DIR, file.file_name)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT)
    new_file = await file.get_file()
    await new_file.download_to_drive(file_path)

    context.user_data["file_path"] = file_path
    context.user_data["file_name"] = file.file_name

    keyboard = [
        [InlineKeyboardButton("Map Name Changer", callback_data="map_name_changer")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Choose an option to proceed:", reply_markup=reply_markup
    )

# Ask for map name
async def ask_name(update: Update, context):
    context.user_data["map_name"] = update.message.text
    keyboard = [
        [InlineKeyboardButton(color, callback_data=color) for color in color_codes.keys()],
        [InlineKeyboardButton("Skip Color", callback_data="no_color")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose a color for the map name or select 'Skip Color':", reply_markup=reply_markup)
    return ASK_COLOR

# Ask for title
async def ask_title(update: Update, context):
    query = update.callback_query
    await query.answer()
    context.user_data["color"] = query.data if query.data != "no_color" else None
    await query.edit_message_text("Please provide the title for the map (Map Title):")
    return ASK_TITLE

# Process the name change
async def process_name_change(update: Update, context):
    context.user_data["map_title"] = update.message.text
    map_name = context.user_data["map_name"]
    color_code = color_codes.get(context.user_data["color"], "")
    map_title = context.user_data["map_title"]

    response = requests.get(
        HEX_CONVERTER_API, params={"title": f"{color_code} {map_name}".strip(), "desc": map_title}
    )
    if response.status_code == 200:
        hex_result = response.text

        file_path = context.user_data.get("file_path")
        file_name = context.user_data.get("file_name")
        with open(file_path, "rb") as file:
            file_data = file.read()

        file_data = file_data.replace(
            bytes.fromhex("12 08 46 69 72 65 5A 6F 6E 65 1A 1C 41 6E 20 65 78 63 69 74 69 6E 67 20 6D 61 70 20 69 6E 20 43 72 61 66 74 6C 61 6E 64"), 
            bytes.fromhex(hex_result.replace(" ", ""))
        )
        
        modified_file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(modified_file_path, "wb") as modified_file:
            modified_file.write(file_data)

        await update.message.reply_text("Map name and title updated successfully!")
        await context.bot.send_document(chat_id=update.message.chat.id, document=open(modified_file_path, "rb"))
    else:
        await update.message.reply_text("Failed to update map. Please try again later.")

    return ConversationHandler.END

# Button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "map_name_changer":
        await query.edit_message_text("Please provide the new name for the map:")
        return ASK_NAME

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_COLOR: [CallbackQueryHandler(ask_title)],
            ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_name_change)],
        },
        fallbacks=[],
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
