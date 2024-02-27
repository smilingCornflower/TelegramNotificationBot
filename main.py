from binance.client import Client
from binance.exceptions import BinanceAPIException
from datetime import datetime, timedelta
from pprint import pprint
import keys
import csv
import time
import telebot
import my_token
import threading


client = Client(keys.API_KEY, keys.SECRET_KEY)
bot = telebot.TeleBot(my_token.bot_token)
my_id = my_token.my_id
daniyar_id = my_token.daniyar_id

DT_MODES = {'hour': datetime.utcnow() - timedelta(hours=1),
            'day': datetime.utcnow() - timedelta(days=1),
            'month': datetime.utcnow() - timedelta(days=31),
            'year': datetime.utcnow() - timedelta(days=365)}

ASSET = 'BTCUSDT'
BUY_LIMIT = 0.005
HOUR = client.KLINE_INTERVAL_1HOUR

def get_candles(currency, candle_date, interval=HOUR, candle_limit=1) -> dict:
    candle_date = int(candle_date.timestamp() * 1000)
    end_date = int(datetime.utcnow().timestamp() * 1000)
    try:
        if candle_limit > 1:
            klines = client.get_klines(symbol=currency, startTime=candle_date, endTime=end_date, interval=interval, limit=candle_limit)
            return klines
        else:
            klines = client.get_klines(symbol=currency, startTime=candle_date, interval=interval, limit=1)
            stamp, open_price, high_price, low_price, close_price, volume = [round(float(i), 3) for i in klines[0][:6]]
            dt_info = datetime.fromtimestamp(stamp / 1_000)
            result = {"time": dt_info, "open": open_price, "high": high_price, "low": low_price, "close": close_price, "volume": volume}
            return result
    except BinanceAPIException as api_err:
        print(f"{api_err=}")
    except ConnectionError as connection_err:
        print(f"{connection_err=}")
    except TimeoutError as time_err:
        print(f"{time_err=}")
    except ValueError as val_err:
        print(f"{val_err=}")
    return False


def get_info(currency, mode='hour') -> str:
    try:
        
        previous_price = get_candles(currency, DT_MODES[mode])['close']
        current_price = get_candles(currency, datetime.utcnow())['close']
        price_diff = round((current_price - previous_price) / previous_price * 100, 3)
        if price_diff >= 0:
            text = (
                f"current price is higher for {price_diff}%\n"
                f"current price is {current_price}\n"
                f"{mode} agо price is {previous_price}"
            )
        else:
            text = (
                f"current price is lower for {abs(price_diff)}%\n"
                f"current price is {current_price}\n"
                f"{mode} ago price is {previous_price}\n"
            )
        return text
    except BinanceAPIException as api_err:
        print(f"{api_err=}")
    except ConnectionError as connection_err:
        print(f"{connection_err=}")
    except TimeoutError as time_err:
        print(f"{time_err=}")
    except ValueError as val_err:
        print(f"{val_err=}")
    return False


def create_csv(currency, mode, filename='data.csv') -> str:
    with open(filename, 'w', encoding='utf-8', newline='') as data_file:
        writer = csv.writer(data_file, delimiter=';')
        writer.writerow(['Time', 'Open Price', 'Close Price', 'Low Price', 'High Price', 'Volume'])
        
        if mode == 'year':
            candle_date = datetime.utcnow() - timedelta(days=405)
            for i in range(10):
                candle_date += timedelta(days=40)
                candles = get_candles(currency, candle_date, candle_limit=959)
                for kline in candles:
                    stamp, open_price, high_price, low_price, close_price, volume = [round(float(i), 3) for i in kline[:6]]
                    dt_info = datetime.fromtimestamp(stamp / 1_000)
                    data_line = [dt_info.strftime('%d.%m.%Y %H:%M'), open_price, close_price, low_price, high_price, volume]
                    writer.writerow(data_line)
        else:
            candles = get_candles(currency, DT_MODES[mode], candle_limit=750)


        for kline in candles:
            stamp, open_price, high_price, low_price, close_price, volume = [round(float(i), 3) for i in kline[:6]]
            dt_info = datetime.fromtimestamp(stamp / 1_000)
            data_line = [dt_info.strftime('%d.%m.%Y %H:%M'), open_price, close_price, low_price, high_price, volume]
            writer.writerow(data_line)
    return filename


def analyze(currency, buy_limit=0.005) -> bool:
    try:
        current_price = get_candles(currency, datetime.utcnow())['close']
        previous_price = get_candles(currency, DT_MODES['hour'])['close']
           
        if previous_price * (1 - buy_limit) >= current_price:
            return True
        return False

    except ValueError as val_err:
        print(f"{val_err=}")
    

def start_analyze(currency=ASSET):
    while True:
        while datetime.utcnow().minute not in (29, 59):
            time.sleep(60)
        while datetime.utcnow().second != 0:
            time.sleep(1)
    
        analyze_response = analyze(currency)    
        info_text = get_info(currency)
        if analyze_response:
            if info_text:
                bot.send_message(chat_id=my_id, text='analyze_response = True')
                bot.send_message(chat_id=my_id, text=info_text)
                bot.send_message(chat_id=daniyar_id, text=info_text)
            else:
                bot.send_message(chat_id=my_id, text='Exeption in analyze_response')
        else:
            bot.send_message(chat_id=my_id, text='analyze_response = False')
            bot.send_message(chat_id=my_id, text=info_text)



# handlers
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(chat_id=message.chat.id, text='Program has started.')
    

@bot.message_handler(commands=['get_info_hour'])
def get_hour_info(message):
    info_text = get_info(ASSET)
    if info_text:
        bot.send_message(message.chat.id, text=info_text, parse_mode='html')
    else:
        bot.send_message(chat_id=my_id, text='Exeption in info_text')


@bot.message_handler(commands=['get_info_month'])
def get_month_info(message):
    info_text = get_info(ASSET, mode='month')
    if info_text:
        bot.send_message(message.chat.id, text=info_text, parse_mode='html')
    else:
        bot.send_message(chat_id=my_id, text='Exeption in info_text')

@bot.message_handler(commands=['get_info_year'])
def get_year_info(message):
    info_text = get_info(ASSET, mode='year')
    if info_text:
        bot.send_message(message.chat.id, text=info_text, parse_mode='html')
    else:
        bot.send_message(chat_id=my_id, text='Exeption in info_text')

@bot.message_handler(commands=['get_csv_month'])
def get_csv_month(message):
    file_path = create_csv(ASSET, 'month', 'csv/data_month.csv')
    with open(file_path, 'r', encoding='utf8') as data_csv:
        bot.send_document(message.chat.id, data_csv)

@bot.message_handler(commands=['get_csv_year'])
def get_csv_year(message):
    file_path = create_csv(ASSET, 'year', 'csv/data_year.csv')
    with open(file_path, 'r', encoding='utf8') as data_csv:
        bot.send_document(message.chat.id, data_csv)

        
analyze_thread = threading.Thread(target=start_analyze)
analyze_thread.start()

bot.infinity_polling()    

# print(get_info(ASSET, 'hour'))
# print(get_info(ASSET, 'day'))
# print(get_info(ASSET, 'month'))
# print(get_info(ASSET, 'year'))
# create_csv(ASSET, 'year', 'data_year.csv')
# create_csv(ASSET, 'month', 'data_month.csv')
# create_csv(ASSET, 'day', 'data_day.csv')
    