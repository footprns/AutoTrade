import json
import requests
import logging
from binance.spot import Spot as Client
from binance.lib.utils import config_logging
import datetime
import tempfile
import csv
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.bar import Frequency
from pyalgotrade.broker import backtesting
import trading
import aws_secretsmanager
import matplotlib.pyplot as plt
from pyalgotrade import plotter

spot_client = Client(api_key=aws_secretsmanager.get_secret()['Binance API key'], api_secret=aws_secretsmanager.get_secret()['Binance API secret'], base_url="https://api.binance.com")
config_logging(logging, logging.INFO)

def download(pair):
    # Define the date range to download
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)
    delta = datetime.timedelta(days=1)
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    kwargs = {
        'startTime': int(start_date.strftime("%s")) * 1000,
        'endTime': int(end_date.strftime("%s")) * 1000
    }

    # logging.info(spot_client.klines(pair, "1d", **kwargs))
    data = spot_client.klines(pair, "1d", **kwargs)

    header = ['Date Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
    filename = f'{temp_dir}/{pair}.csv'
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for row in data:
            timestamp = int(row[0]/1000)
            timestamp_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ')
            row[0] = timestamp_str
            row[6] = row[4]
            row = [row[0], row[1], row[2], row[3], row[4], row[5], row[6]]
            writer.writerow(row) 
    return filename

def lambda_handler(event, context):

    # Create a plotter
    plt.figure(figsize=(12, 6))
    plt.title("Backtesting Results")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True)

    csv_file = download(event['pair'])
    print(csv_file)

    # Load the bar feed from the CSV file
    feed = csvfeed.GenericBarFeed(Frequency.DAY) # 5 minutes
    feed.setDateTimeFormat("%Y-%m-%dT%H:%M:%SZ")
    feed.addBarsFromCSV(event['pair'], csv_file)

    # Instantiate the broker
    broker = backtesting.Broker(10, feed, backtesting.NoCommission())
    # Evaluate the strategy with the feed.
    myStrategy = trading.MyStrategy(feed, event['pair'], broker)
    myStrategy.run()

    # Get the price data and strategy signals
    price_data = myStrategy.getFeed()[event['pair']].getPriceDataSeries()
    buy_signals = myStrategy.getBuySignals()
    sell_signals = myStrategy.getSellSignals()

    # Plot the price data
    plt.plot(price_data.getDateTimes(), price_data[:], 'b-', label="Price")

    # Plot the buy signals
    for date, price in buy_signals:
        plt.plot(date, price, 'g^', markersize=8, label="Buy")

    # Plot the sell signals
    for date, price in sell_signals:
        plt.plot(date, price, 'rv', markersize=8, label="Sell")

    # Add a legend and display the plot
    plt.legend()
    plt.show()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world"
        }),
    }

lambda_handler(context=None, event={'pair': 'MATICUSDT'})
