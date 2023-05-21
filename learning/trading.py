from pyalgotrade import strategy
from pyalgotrade.broker import backtesting
from pyalgotrade.technical import ma
# from pyalgotrade.technical import rsi
from pyalgotrade.technical import cross
import datetime

class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, brk):
        super(MyStrategy, self).__init__(feed, brk)
        self.__long_sma_period = ma.SMA(feed[instrument].getCloseDataSeries(), 27)
        self.__short_sma_period = ma.SMA(feed[instrument].getCloseDataSeries(), 3)
        self.__instrument = instrument
        self.__position = None
        self.__buy_signals = []
        self.__sell_signals = []


    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        print("BUY at $%.2f" % (execInfo.getPrice()))
        # Get the current equity (cash + holdings value)
        equity = self.getBroker().getEquity()
        print(f"Equity: {equity}")
        print(f'Cash: {self.getBroker().getCash()}') 
        print('--------')     

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        print("SELL at $%.2f" % (execInfo.getPrice()))
        self.__position = None
        equity = self.getBroker().getEquity()
        print(f"Equity: {equity}")
        print(f'Cash: {self.getBroker().getCash()}') 
        print('--------')

    def getBuySignals(self):
        return self.__buy_signals

    def getSellSignals(self):
        return self.__sell_signals
    
    def onBars(self, bars):
        bar = bars[self.__instrument]
        if self.__short_sma_period is None or self.__long_sma_period is None:
            return

        if self.__position is None:
            if cross.cross_above(self.__short_sma_period, self.__long_sma_period):
                print(f'Buy now!! Closing price: {bar.getDateTime().strftime("%Y-%m-%d")} {bar.getClose()} {self.__long_sma_period[-1]} {self.__short_sma_period[-1]} {self.getBroker().getEquity()}')
                cash = self.getBroker().getCash()
                # shares = cash / bars[self.__instrument].getPrice()
                shares = 1 # amout of MATIC
                self.__position = self.enterLong(self.__instrument, shares, True)   

                price = bars[self.__instrument].getPrice()
                self.__buy_signals.append((bars.getDateTime(), price))

        elif cross.cross_below(self.__short_sma_period, self.__long_sma_period) and bar.getPrice() > self.__position.getEntryOrder().getExecutionInfo().getPrice():
            print(f'Sell now!! Closing price: {bar.getDateTime().strftime("%Y-%m-%d")} {bar.getClose()} {self.__long_sma_period[-1]} {self.__short_sma_period[-1]} {self.getBroker().getEquity()}')
            self.__position.exitMarket()

            price = bars[self.__instrument].getPrice()
            self.__sell_signals.append((bars.getDateTime(), price))



        # print(f'{cross.cross_below(self.__short_sma_period, self.__long_sma_period)}')
        # Get the current equity (cash + holdings value)
        # equity = self.getBroker().getEquity()
        # self.info(f"Equity: {equity}")