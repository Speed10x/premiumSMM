import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import aiohttp
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token and API details (stored in .env file)
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
SMM_API_URL = os.getenv('SMM_API_URL')
SMM_API_KEY = os.getenv('SMM_API_KEY')

# User session storage
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("Services", callback_data='services')],
        [InlineKeyboardButton("Balance", callback_data='balance')],
        [InlineKeyboardButton("Support", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Welcome to our SMM Bot! What would you like to do?', reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    if query.data == 'services':
        await show_categories(update, context)
    elif query.data == 'balance':
        await show_balance(update, context)
    elif query.data == 'support':
        await show_support(update, context)
    elif query.data.startswith('category_'):
        category_id = query.data.split('_')[1]
        await show_services(update, context, category_id)
    elif query.data.startswith('service_'):
        service_id = query.data.split('_')[1]
        await show_service_details(update, context, service_id)

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show service categories."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SMM_API_URL}/api/v2", json={
            "key": SMM_API_KEY,
            "action": "services"
        }) as response:
            data = await response.json()
    
    categories = set(service['category'] for service in data)
    keyboard = [[InlineKeyboardButton(category, callback_data=f'category_{category}')] for category in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text('Choose a category:', reply_markup=reply_markup)

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    """Show services for a specific category."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SMM_API_URL}/api/v2", json={
            "key": SMM_API_KEY,
            "action": "services"
        }) as response:
            data = await response.json()
    
    services = [service for service in data if service['category'] == category]
    keyboard = [[InlineKeyboardButton(service['name'], callback_data=f'service_{service["service"]}')] for service in services]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(f'Services in {category}:', reply_markup=reply_markup)

async def show_service_details(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id: str) -> None:
    """Show details for a specific service."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SMM_API_URL}/api/v2", json={
            "key": SMM_API_KEY,
            "action": "services"
        }) as response:
            data = await response.json()
    
    service = next((s for s in data if s['service'] == service_id), None)
    if service:
        message = f"Service: {service['name']}\n"
        message += f"Price: ${service['rate']} per 1000\n"
        message += f"Min order: {service['min']}\n"
        message += f"Max order: {service['max']}\n"
        message += f"\nTo order, use the /order command with the following format:\n"
        message += f"/order {service_id} <quantity> <link>"
        await update.callback_query.edit_message_text(message)
    else:
        await update.callback_query.edit_message_text("Service not found.")

async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user balance."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{SMM_API_URL}/api/v2", json={
            "key": SMM_API_KEY,
            "action": "balance"
        }) as response:
            data = await response.json()
    
    balance = data.get('balance', 'N/A')
    currency = data.get('currency', 'USD')
    await update.callback_query.edit_message_text(f"Your current balance is: {balance} {currency}")

async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show support information."""
    support_message = "For support, please contact us at support@example.com or visit our website www.example.com"
    await update.callback_query.edit_message_text(support_message)

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle order command."""
    try:
        _, service_id, quantity, link = update.message.text.split(' ', 3)
        quantity = int(quantity)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{SMM_API_URL}/api/v2", json={
                "key": SMM_API_KEY,
                "action": "add",
                "service": service_id,
                "link": link,
                "quantity": quantity
            }) as response:
                data = await response.json()
        
        if 'order' in data:
            await update.message.reply_text(f"Order placed successfully. Order ID: {data['order']}")
        else:
            await update.message.reply_text(f"Error placing order: {data.get('error', 'Unknown error')}")
    except ValueError:
        await update.message.reply_text("Invalid order format. Please use: /order <service_id> <quantity> <link>")

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(CommandHandler("order", handle_order))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()