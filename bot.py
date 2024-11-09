import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
import aiohttp
from flask import Flask, request

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
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Flask app for webhook
app = Flask(__name__)

# Conversation states
PLATFORM, SERVICE, QUANTITY, ACCOUNT, PAYMENT = range(5)

# Platform and service options
PLATFORMS = {
    'YouTube': ['Likes', 'Subscribers', 'Watch Time'],
    'Instagram': ['Followers', 'Likes', 'Views', 'Comments'],
    'Telegram': ['Group Members', 'Channel Subscribers'],
    'Twitter': ['Followers', 'Retweets', 'Likes']
}

PRICE_CHART = {
    'Instagram': {
        'Views': 5,  # 5 rupees per 1000
        'Followers': 200,  # 200 rupees per 1000
        'Likes': 10,  # 10 rupees per 1000
        'Comments': 10  # 10 rupees per comment
    },
    'YouTube': {
        'Subscribers': 750,  # 750 rupees per 1000
        'Views': 200,  # 200 rupees per 1000
        'Watch Time': 1100  # 1,100 rupees per 1000 hours
    },
    'Telegram': {
        'Group Members': 250,  # 250 rupees per 1000
        'Channel Subscribers': 260  # 260 rupees per 1000
    },
    'Twitter': {
        'Followers': 2300,  # 2,300 rupees per 1000
        'Retweets': 900,  # 900 rupees per 1000
        'Likes': 300  # 300 rupees per 1000
    }
}

# User session storage
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    keyboard = [[InlineKeyboardButton(platform, callback_data=f'platform_{platform}')] for platform in PLATFORMS.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome! Please choose a platform:', reply_markup=reply_markup)
    return PLATFORM

async def platform_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle platform selection."""
    query = update.callback_query
    await query.answer()
    platform = query.data.split('_')[1]
    user_sessions[query.from_user.id] = {'platform': platform}
    
    keyboard = [[InlineKeyboardButton(service, callback_data=f'service_{service}')] for service in PLATFORMS[platform]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f'You selected {platform}. Now choose a service:', reply_markup=reply_markup)
    return SERVICE

async def service_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle service selection."""
    query = update.callback_query
    await query.answer()
    service = query.data.split('_')[1]
    user_sessions[query.from_user.id]['service'] = service
    await query.edit_message_text(f'You selected {service}. Please enter the quantity (50-20,000):')
    return QUANTITY

async def quantity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle quantity input."""
    try:
        quantity = int(update.message.text)
        if 50 <= quantity <= 20000:
            user_sessions[update.effective_user.id]['quantity'] = quantity
            await update.message.reply_text('Great! Now please enter the username, ID, or share the link of the account:')
            return ACCOUNT
        else:
            await update.message.reply_text('Please enter a quantity between 50 and 20,000.')
            return QUANTITY
    except ValueError:
        await update.message.reply_text('Please enter a valid number.')
        return QUANTITY

async def account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle account input and show payment information."""
    user_data = user_sessions[update.effective_user.id]
    user_data['account'] = update.message.text
    
    platform = user_data['platform']
    service = user_data['service']
    quantity = user_data['quantity']
    
    # Calculate price based on the price chart
    if service == 'Comments':  # Special case for Instagram comments
        price = PRICE_CHART[platform][service] * quantity
    elif service == 'Watch Time':  # Special case for YouTube watch time
        price = PRICE_CHART[platform][service] * (quantity / 1000)  # Price per 1000 hours
    else:
        price = PRICE_CHART[platform][service] * (quantity / 1000)  # Price per 1000 for other services
    
    # Round to 2 decimal places and store in user_data
    user_data['price'] = round(price, 2)
    
    await update.message.reply_text(f'Great! The total price is ₹{user_data["price"]}. Please make the payment to UPI ID: your_upi_id@upi\n\nAfter payment, please upload a screenshot of the transaction.')
    return PAYMENT

async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle payment screenshot and process the order."""
    if update.message.document or update.message.photo:
        user_data = user_sessions[update.effective_user.id]
        
        # Log the order
        log_message = f"New order:\nUser ID: {update.effective_user.id}\nPlatform: {user_data['platform']}\nService: {user_data['service']}\nQuantity: {user_data['quantity']}\nAccount: {user_data['account']}\nPrice: ₹{user_data['price']}"
        message = await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_message)
        
        if update.message.document:
            await context.bot.send_document(chat_id=LOG_CHANNEL_ID, document=update.message.document.file_id, caption="Payment Screenshot")
        else:
            await context.bot.send_photo(chat_id=LOG_CHANNEL_ID, photo=update.message.photo[-1].file_id, caption="Payment Screenshot")
        
        # Add buttons to the log message
        keyboard = [
            [InlineKeyboardButton("Approve", callback_data=f"approve_{update.effective_user.id}_{message.message_id}")],
            [InlineKeyboardButton("Reject", callback_data=f"reject_{update.effective_user.id}_{message.message_id}")],
            [InlineKeyboardButton("Pending", callback_data=f"pending_{update.effective_user.id}_{message.message_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.edit_reply_markup(reply_markup=reply_markup)
        
        # Here you would typically process the order through the LOLSMM API
        await update.message.reply_text("Your request has been received and is being processed. I will notify you once it is completed.")
        del user_sessions[update.effective_user.id]
        return ConversationHandler.END
    else:
        await update.message.reply_text("Please upload a screenshot of your payment.")
        return PAYMENT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text('Order cancelled. Use /start to begin a new order.')
    return ConversationHandler.END

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin actions on log messages."""
    query = update.callback_query
    await query.answer()
    action, user_id, message_id = query.data.split('_')
    user_id = int(user_id)
    message_id = int(message_id)

    if action == 'approve':
        await context.bot.send_message(chat_id=user_id, text="Your service request has been completed!")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=f"{query.message.text}\n\nStatus: Approved")
    elif action == 'reject':
        await context.bot.send_message(chat_id=user_id, text="Your service request has been rejected due to an incorrect transaction screenshot. Please contact support for assistance.")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=f"{query.message.text}\n\nStatus: Rejected")
    elif action == 'pending':
        await context.bot.send_message(chat_id=user_id, text="Your service request is pending. We're experiencing some issues and will contact you directly. Thank you for your patience.")
        await query.edit_message_reply_markup(reply_markup=None)
        await query.edit_message_text(text=f"{query.message.text}\n\nStatus: Pending")

def main() -> None:
    """Set up and run the bot."""
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PLATFORM: [CallbackQueryHandler(platform_callback, pattern='^platform_')],
            SERVICE: [CallbackQueryHandler(service_callback, pattern='^service_')],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, quantity_handler)],
            ACCOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, account_handler)],
            PAYMENT: [MessageHandler(filters.PHOTO | filters.Document.ALL | filters.TEXT & ~filters.COMMAND, payment_handler)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_admin_action, pattern='^(approve|reject|pending)_'))

    # Set up webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get('PORT', 5000)),
        webhook_url=WEBHOOK_URL
    )

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    """Handle incoming updates via webhook."""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return 'OK'

if __name__ == '__main__':
    main()
