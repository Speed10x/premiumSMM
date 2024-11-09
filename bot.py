import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
import aiohttp
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token and API details
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
LOLSMM_API_URL = os.getenv('LOLSMM_API_URL')
LOLSMM_API_KEY = os.getenv('LOLSMM_API_KEY')
LOG_CHANNEL_ID = os.getenv('LOG_CHANNEL_ID')

# Conversation states
PLATFORM, SERVICE, QUANTITY, LINK, PAYMENT = range(5)

# Platform and service options
PLATFORMS = {
    'Instagram': ['Followers', 'Likes', 'Views', 'Comments'],
    'YouTube': ['Likes', 'Subscribers', 'Watch Time'],
    'Twitter': ['Followers', 'Retweets', 'Likes'],
    'Telegram': ['Group Members', 'Channel Subscribers']
}

# User session storage
user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    keyboard = [[InlineKeyboardButton(platform, callback_data=f'platform_{platform}')] for platform in PLATFORMS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome to our SMM Bot! Please select a platform:', reply_markup=reply_markup)
    return PLATFORM

async def platform_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle platform selection."""
    query = update.callback_query
    await query.answer()
    platform = query.data.split('_')[1]
    user_data[query.from_user.id] = {'platform': platform}

    keyboard = [[InlineKeyboardButton(service, callback_data=f'service_{service}')] for service in PLATFORMS[platform]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f'You selected {platform}. Now choose a service:', reply_markup=reply_markup)
    return SERVICE

async def service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle service selection."""
    query = update.callback_query
    await query.answer()
    service = query.data.split('_')[1]
    user_data[query.from_user.id]['service'] = service

    await query.edit_message_text(f'You selected {service}. Please enter the quantity (50-20,000):')
    return QUANTITY

async def quantity_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input."""
    try:
        quantity = int(update.message.text)
        if 50 <= quantity <= 20000:
            user_data[update.effective_user.id]['quantity'] = quantity
            await update.message.reply_text('Great! Now please enter the username, ID, or share the link of the account:')
            return LINK
        else:
            await update.message.reply_text('Please enter a quantity between 50 and 20,000.')
            return QUANTITY
    except ValueError:
        await update.message.reply_text('Please enter a valid number.')
        return QUANTITY

async def link_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle link input and show payment information."""
    user_data[update.effective_user.id]['link'] = update.message.text
    
    # Here you would typically fetch the price from the LOLSMM API
    # For demonstration, we'll use a placeholder price
    price = 10  # Replace with actual API call to get price
    
    user_data[update.effective_user.id]['price'] = price
    
    await update.message.reply_text(f'Great! The total price is ${price}. Please make the payment to UPI ID: your_upi_id@upi\n\nAfter payment, please upload a screenshot of the transaction.')
    return PAYMENT

async def payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment screenshot and process the order."""
    user_id = update.effective_user.id
    user_info = user_data[user_id]

    if update.message.document or update.message.photo:
        # Log the order details
        log_message = (f"New order:\n"
                       f"User ID: {user_id}\n"
                       f"Platform: {user_info['platform']}\n"
                       f"Service: {user_info['service']}\n"
                       f"Quantity: {user_info['quantity']}\n"
                       f"Link: {user_info['link']}\n"
                       f"Price: ${user_info['price']}")
        
        await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_message)
        
        # Send the payment screenshot to the log channel
        if update.message.document:
            await context.bot.send_document(chat_id=LOG_CHANNEL_ID, document=update.message.document.file_id, caption="Payment Screenshot")
        else:
            await context.bot.send_photo(chat_id=LOG_CHANNEL_ID, photo=update.message.photo[-1].file_id, caption="Payment Screenshot")

        # Here you would typically process the order through the LOLSMM API
        # For demonstration, we'll just send a confirmation message
        await update.message.reply_text("Your request has been processed. I will notify you once it is completed.")
        
        # Clear user data
        del user_data[user_id]
        return ConversationHandler.END
    else:
        await update.message.reply_text("Please upload a screenshot of your payment.")
        return PAYMENT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text('Order cancelled. Use /start to begin a new order.')
    return ConversationHandler.END

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PLATFORM: [CallbackQueryHandler(platform_callback, pattern='^platform_')],
            SERVICE: [CallbackQueryHandler(service_callback, pattern='^service_')],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_input)],
            LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, link_input)],
            PAYMENT: [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.TEXT & ~filters.COMMAND, payment_confirmation)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
