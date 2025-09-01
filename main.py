
import datetime, pytz
from all_functions import *
import requests
import pandas as pd

BOT_TOKEN = "8399617678:AAEUihlkQe_P4JGTo88gLr9sf-_4rDCijHg"
CHAT_ID = "1893008354"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=data)

def run_task():
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata")).time()
    start = datetime.time(9, 15)
    end = datetime.time(15, 45)

    if start <= now <= end:
        print("Checking for time :", end="")
        print(datetime.datetime.now())
        messages = []
        for stock in stocks:
            stock_data = get_data(stock)
            stock_data = all_indicators(stock_data)
            message = signal_catcher(stock_data[:-1])
            message['Stock'] = stock
            if len(message) > 1:
                if message['Pattern'] != None or message['MACD_Crossover'] != False or message['EMA_Crossover'] != False:
                    messages.append(message)

                    telegram_message = f"Stock :{stock} \nDatetime :{message['Datetime']}\nSignal :{message['Signal']}\nRSI :{message['RSI']}\nMACD_Crossover :{message['MACD_Crossover']}\nEMA_Crossover{message['EMA_Crossover']}\nPattern :{message['Pattern']}"
                    
                    send_telegram_message(telegram_message)

        print(messages)

run_task()