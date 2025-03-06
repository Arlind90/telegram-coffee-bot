import asyncio
import logging
import json
import yfinance as yf
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler
import os
from dotenv import load_dotenv
import time
import requests
from random import uniform
import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram API details
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
if not TELEGRAM_API_KEY:
    raise ValueError("TELEGRAM_API_KEY environment variable is not set!")

# Initialize empty set for subscribers and define file path
SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    """Load subscribers from file."""
    try:
        with open(SUBSCRIBERS_FILE, 'r') as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_subscribers(subs):
    """Save subscribers to file."""
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(list(subs), f)

# Load existing subscribers
subscribers = load_subscribers()

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_API_KEY)

async def get_coffee_price():
    """Fetches the latest coffee price from Yahoo Finance with retries and fallback."""
    MAX_RETRIES = 3
    ticker_symbols = ["KC=F", "COFFEE_F", "JO"]  # Multiple tickers to try
    
    # User agent to mimic a regular browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for ticker in ticker_symbols:
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Attempting to fetch coffee price with ticker {ticker}, attempt {attempt+1}")
                
                # Add a small delay with random component to avoid rate limiting
                time.sleep(uniform(1, 3))
                
                # Configure yfinance session with headers
                session = requests.Session()
                session.headers.update(headers)
                coffee = yf.Ticker(ticker, session=session)
                
                # Get data for the last 7 days to ensure we have the last trading day
                data = coffee.history(period="7d")
                
                if not data.empty:
                    # Check if we have valid price data
                    if "Close" in data.columns and len(data["Close"]) > 0:
                        price_per_pound = data["Close"].iloc[-1]
                        
                        # Handle different price formats for different tickers
                        if ticker == "KC=F":
                            price_per_pound = price_per_pound / 100  # Convert cents to dollars
                        
                        price_per_kg = price_per_pound * 2.20462  # Convert price from per pound to per kg
                        last_date = data.index[-1].strftime("%Y-%m-%d")
                        
                        logger.info(f"Successfully fetched coffee price: ${price_per_kg:.3f} per kg")
                        return f"☕ Coffee Price (as of {last_date}): ${price_per_kg:.3f} per kg"
            
            except Exception as e:
                logger.error(f"Error fetching coffee price with ticker {ticker}: {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    # Wait longer between retries
                    time.sleep(uniform(2, 5))
                continue
    
    # Fallback to fetch data directly using requests if yfinance fails
    try:
        logger.info("Attempting to fetch coffee price directly as fallback")
        url = "https://query1.finance.yahoo.com/v8/finance/chart/KC=F"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if "chart" in data and "result" in data["chart"] and data["chart"]["result"]:
                result = data["chart"]["result"][0]
                if "meta" in result and "regularMarketPrice" in result["meta"]:
                    price = result["meta"]["regularMarketPrice"]
                    price_per_pound = price / 100  # Convert cents to dollars
                    price_per_kg = price_per_pound * 2.20462
                    
                    # Get timestamp
                    timestamp = result["meta"].get("regularMarketTime", int(time.time()))
                    last_date = time.strftime("%Y-%m-%d", time.localtime(timestamp))
                    
                    logger.info(f"Successfully fetched coffee price via fallback: ${price_per_kg:.3f} per kg")
                    return f"☕ Coffee Price (as of {last_date}): ${price_per_kg:.3f} per kg"
    except Exception as e:
        logger.error(f"Fallback method also failed: {str(e)}")
    
    return "Could not fetch coffee price. Please try again later."

async def send_daily_price():
    """Fetches coffee price and sends it to all subscribers daily."""
    message = await get_coffee_price()
    for chat_id in subscribers:
        await bot.send_message(chat_id=chat_id, text=message)
    logger.info(f"Daily price update sent to {len(subscribers)} subscribers.")

def job():
    """Wrapper function to run send_daily_price() asynchronously."""
    asyncio.run(send_daily_price())

# Telegram Command Handlers
async def start(update: Update, context):
    """Handles the /start command."""
    chat_id = update.message.chat_id
    subscribers.add(chat_id)
    save_subscribers(subscribers)
    await update.message.reply_text("Welcome! You've been subscribed to daily coffee price updates. Use /coffeeprice to get the latest coffee price.\nUse /unsubscribe to stop receiving daily updates.")

async def price(update: Update, context):
    """Handles the /coffeeprice command."""
    await update.message.reply_text("Fetching latest coffee price. This may take a moment...")
    message = await get_coffee_price()
    await update.message.reply_text(message)

async def unsubscribe(update: Update, context):
    """Handles the /unsubscribe command."""
    chat_id = update.message.chat_id
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers(subscribers)
        await update.message.reply_text("You've been unsubscribed from daily updates.")
    else:
        await update.message.reply_text("You're not currently subscribed to updates.")

async def help_command(update: Update, context):
    """Handles the /help command."""
    help_text = "Available commands:\n/start - Start the bot and subscribe to updates\n/coffeeprice - Get coffee price\n/unsubscribe - Stop receiving daily updates\n/help - Show this help message"
    await update.message.reply_text(help_text)

# Initialize the Telegram bot application
def main():
    app = Application.builder().token(TELEGRAM_API_KEY).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("coffeeprice", price))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Start APScheduler
    scheduler = BackgroundScheduler()
    # Schedule for 20:00 Rome time (2:00 PM ET + 6 hours)
    scheduler.add_job(job, "cron", 
                     day_of_week='0-4',  # Monday through Friday
                     hour=20,            # 8:00 PM Rome time (after US market close)
                     minute=0,
                     timezone='Europe/Rome')
    scheduler.start()
    logger.info("Scheduler started for daily updates (weekdays at 20:00 Rome time)")

    # Run the bot
    app.run_polling()

if __name__ == "__main__":
    main()