import json
from pyalgotrade import strategy
from pyalgotrade.barfeed import csvfeed
from pyalgotrade.bar import Frequency
from pyalgotrade.technical import ma
from pyalgotrade.technical import rsi
from pyalgotrade.technical import cross
import boto3, tempfile, logging
import datetime

# Initialize S3 client
s3 = boto3.client('s3', region_name='ap-southeast-1')

# Set bucket name and file name
bucket_name = 'imank-pyalgotrade'
file_name = 'LINKUSDT-1d-all.csv'

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    # Get CSV file from S3
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    data = obj['Body'].read().decode('utf-8')

    # Write the CSV content to a temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    temp_file.write(data)
    temp_file.close()
except Exception as e:
    logging.info(e)
class TwoMovingAverageStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, entrySMA, exitSMA, rsiPeriod, overBoughtThreshold):
        # super(MyStrategy, self).__init__(feed, 1000)
        super(TwoMovingAverageStrategy, self).__init__(feed, 1000)
        self.__instrument = instrument
        self.__rsiPeriod = rsiPeriod
        self.__entrySMA = ma.SMA(feed[instrument].getCloseDataSeries(), entrySMA)
        self.__exitSMA = ma.SMA(feed[instrument].getCloseDataSeries(), exitSMA)
        self.__rsi = rsi.RSI(feed[instrument].getCloseDataSeries(), rsiPeriod)
        self.__overBoughtThreshold = overBoughtThreshold
        self.__position = None

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY at %.2f" % (execInfo.getPrice()))
        if datetime.date.today() == execInfo.getDateTime().date():
            logger.info('Buy now')

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at %.2f" % (execInfo.getPrice()))
        self.__position = None
        if datetime.date.today() == execInfo.getDateTime().date():
            logger.info('Sell now')

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate SMA
        if self.__entrySMA[-1] is None or self.__exitSMA[-1] is None:
            return

        bar = bars[self.__instrument]

        # If not already in a position, check for a buy signal
        if self.__position is None:
            if cross.cross_above(self.__entrySMA, self.__exitSMA) and self.__rsi[-1] < 30 and self.__rsi[-1] < 50:
                self.__position = self.enterLong(self.__instrument, 50, True)
        # If already in a position, check for a sell signal
        elif cross.cross_below(self.__entrySMA, self.__exitSMA) and self.__rsi[-1] > 70 and self.__rsi[-1] > self.__overBoughtThreshold:
            self.__position.exitMarket()

def lambda_handler(event, context):
    # Load the bar feed from the CSV file
    feed = csvfeed.GenericBarFeed(Frequency.DAY) # 5 minutes
    feed.setDateTimeFormat("%Y-%m-%dT%H:%M:%SZ")
    feed.addBarsFromCSV("LINKUSDT", temp_file.name)

    # Evaluate the strategy with the feed.
    # myStrategy = MyStrategy(feed, "LINKUSDT", 20, 4)
    myStrategy = TwoMovingAverageStrategy(feed, "LINKUSDT", entrySMA=5, exitSMA=4, rsiPeriod=2, overBoughtThreshold=75)
    myStrategy.run()
    logger.info("Final portfolio value: $%.2f" % myStrategy.getBroker().getEquity())
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
