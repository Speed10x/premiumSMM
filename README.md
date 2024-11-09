 # SMM Telegram Bot

Yeh Telegram bot Social Media Marketing (SMM) services provide karta hai, jo ek SMM API ke saath integrate hai.

## Features

- Service categories aur services browse karna
- Service details dekhna
- Orders place karna
- Balance check karna
- Support information provide karna

## Setup

1. Is repository ko clone karein:
   ```
   git clone https://github.com/yourusername/smm-telegram-bot.git
   cd smm-telegram-bot
   ```

2. Required packages install karein:
   ```
   pip install -r requirements.txt
   ```

3. Root directory mein ek `.env` file create karein aur usme yeh content dalein:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   SMM_API_URL=your_smm_api_url_here
   SMM_API_KEY=your_smm_api_key_here
   ```

4. Bot ko run karein:
   ```
   python bot.py
   ```

## Render par Deployment

1. Is repository ko apne GitHub account par fork karein.
2. Agar aapke paas Render account nahi hai, to [Render](https://render.com/) par sign up karein.
3. Render mein, ek naya Web Service create karein aur use apne GitHub repository se connect karein.
4. Web Service ko configure karein:
   - Environment: Docker
   - Build Command: (khali chhodein)
   - Start Command: (khali chhodein)
5. Environment variables add karein:
   - `TELEGRAM_BOT_TOKEN` apke bot token ke saath
   - `SMM_API_URL` apke SMM API URL ke saath
   - `SMM_API_KEY` apke SMM API key ke saath
6. Bot ko deploy karein.

## Usage

1. Telegram par apne bot se chat start karein.
2. Shuru karne ke liye /start command ka use karein.
3. Services browse karne, balance check karne, ya support information dekhne ke liye buttons ka use karein.
4. Service order karne ke liye, /order command ka use karein is format mein:
   /order <service_id> <quantity> <link>

## Contributing

Contributions ka swagat hai! Kripya Pull Request submit karne mein sankoch na karein.

## License

Is project ko MIT License ke tahat license kiya gaya hai.
