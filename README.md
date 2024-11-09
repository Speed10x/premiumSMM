# SMM Telegram Bot

This Telegram bot provides Social Media Marketing (SMM) services using the LOLSMM API. It allows users to order various services for YouTube, Instagram, Telegram, and Twitter.

## Features

- Multi-platform support (YouTube, Instagram, Telegram, Twitter)
- Various services for each platform (likes, followers, subscribers, etc.)
- User-friendly conversation flow
- Payment processing via UPI
- Order logging in a private channel with admin approval system
- Notification system for order status updates

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/smm-telegram-bot.git
   cd smm-telegram-bot
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory with the following content:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   LOLSMM_API_URL=your_lolsmm_api_url_here
   LOLSMM_API_KEY=your_lolsmm_api_key_here
   LOG_CHANNEL_ID=your_log_channel_id_here
   WEBHOOK_URL=https://your-app-name.onrender.com/your_bot_token
   ```

4. Run the bot:
   ```
   python bot.py
   ```

## Deployment on Render

1. Fork this repository to your GitHub account.
2. Sign up for a [Render](https://render.com/) account if you haven't already.
3. In Render, create a new Web Service and connect it to your GitHub repository.
4. Configure the Web Service:
   - Environment: Docker
   - Build Command: (leave empty)
   - Start Command: (leave empty)
5. Add the environment variables:
   - `TELEGRAM_BOT_TOKEN`
   - `LOLSMM_API_URL`
   - `LOLSMM_API_KEY`
   - `LOG_CHANNEL_ID`
   - `WEBHOOK_URL`
6. Deploy the bot.

## Usage

1. Start a chat with your bot on Telegram.
2. Use the /start command to begin.
3. Follow the prompts to select a platform, service, quantity, and provide account details.
4. Make the payment and upload a screenshot.
5. Wait for confirmation of your order.

## Admin Features

- Approve, reject, or mark orders as pending from the log channel.
- Automated notifications sent to users based on order status.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
