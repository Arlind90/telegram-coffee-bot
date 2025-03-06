# Coffee Price Telegram Bot

A Telegram bot that provides daily updates on coffee futures prices. Users can subscribe to receive automatic daily price updates on weekdays and can also manually request the current coffee price at any time.

## Features

- **Daily Price Updates**: Sends coffee price updates to all subscribers automatically at 20:00 Rome time on weekdays
- **Manual Price Checks**: Users can request the current coffee price with a command
- **Subscription Management**: Users can subscribe or unsubscribe to daily updates

## Commands

- `/start` - Start the bot and subscribe to daily updates
- `/coffeeprice` - Get the current coffee price
- `/unsubscribe` - Stop receiving daily updates
- `/help` - Display available commands

## Setup Instructions

1. Clone this repository:
   ```
   git clone <repository-url>
   cd telegram-bot-coffee
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your Telegram API key:
   ```
   TELEGRAM_API_KEY=your_telegram_bot_api_key
   ```

4. Run the bot:
   ```
   python newbot.py
   ```

## How to Get a Telegram Bot API Key

1. Talk to [BotFather](https://t.me/botfather) on Telegram
2. Use the `/newbot` command and follow the instructions
3. BotFather will provide an API key which you should add to your `.env` file

## Technical Details

- The bot uses the [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) library
- Coffee price data is fetched from Yahoo Finance using the [yfinance](https://github.com/ranaroussi/yfinance) library
- APScheduler is used to schedule the daily price updates
- Subscriber data is stored in a local JSON file

## License

[MIT License](LICENSE) 