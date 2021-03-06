from pyalgotrade import strategy
#from pyalgotrade.barfeed import yahoofeed
#from pyalgotrade.barfeed import googlefeed
from pyalgotrade.barfeed import ibfeed
from pyalgotrade.technical import ma
from pyalgotrade import broker
import datetime
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade import plotter


class MyStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument1,instrument2, smaPeriod):
        super(MyStrategy, self).__init__(feed, 1000)
        self.__position = None
        self.__option = None
        self.__instrument1 = instrument1
        self.__instrument2 = instrument2
        
        # We'll use adjusted close values instead of regular close values.
        #self.setUseAdjustedValues(True)
        self.__sma = ma.SMA(feed[instrument1].getPriceDataSeries(), smaPeriod)

    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY at $%.2f" % (execInfo.getPrice()))
    
    def isExpired(self, bar, position):
        ret=False
        time = position.getExpiryDate()
        year = position.getExpiryDate().year
        month = position.getExpiryDate().month
        day = position.getExpiryDate().day
        ####### Si la date de la bar est egale ou superieure a la date d'expiration, on annule les part et empeche les order sur cet instrument
#        currentdatetime= datetime.strptime(instrument[-8:], '%Y%m%d')
        if datetime.datetime.strptime(self.__instrument2[-8:], '%Y%m%d') <= datetime(year, month, day):
            self.__logger.debug("POSITION EST EXPIREE")
            ret=True
        return ret            
        
        
    def getSMA(self):
        return self.__sma
        
    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at $%.2f" % (execInfo.getPrice()))
        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate a SMA.
        if bars.getBar(self.__instrument1) and bars.getBar(self.__instrument2) and self.__sma[-1] is None:
            return

#        self.info("current bar price: $%.2f and current sma: $%.2f" % (bar.getPrice(), self.__sma[-1]))
        # If a position was not opened, check if we should enter a long position.
#        if self.__option is None and not self.__optionAlreadyExecuted:
        if bars.getBar(self.__instrument1) and bars.getBar(self.__instrument2) and self.__position is None and self.__option is None: 
            
            if bars.getBar(self.__instrument1).getPrice() > self.__sma[-1]:
                right = broker.OptionOrder.Right.PUT
                strike = bars.getBar(self.__instrument2).getPrice()-3
                bars.getBar(self.__instrument2).getDateTime()
                expiry = datetime.datetime(2016, 8, 19, 16, 30)
                
                #if bar.getPrice() > self.__sma[-1]:
                    # Enter a buy market order for 10 shares. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument1, 2, True)
                self.__option = self.enterOptionLong(self.__instrument2, 2, right, strike, expiry, True)
                
                #self.__optionAlreadyExecuted = True
                
#                print "Option executed for: $%.2f" % (bar.getPrice())
        # Check if we have to exit the position.
        #elif bar.getPrice() < self.__sma[-1] and not self.__position.exitActive():
            #self.__position.exitMarket()
        
        elif bars.getBar(self.__instrument1).getPrice() < self.__sma[-1] and not self.__position.exitActive() and not self.__option.exitActive():
            self.__position.exitMarket()
            self.__option.exitMarket()
                
#            print "Option exited at: $%.2f" % bar.getPrice()
        
        

        
        #### l'ordre devrait etre generer a partir de la position de l'option avec le strike price si expiry n'est pas depasse
#        elif self.__position is None and self.__option.getAge().days == 25 :
#            self.__position = self.enterLong(self.__option.getInstrument(), 10, True)
#            print "Order executed at: $%.2f" % bar.getPrice()
        
#        elif self.__position is not None and self.__position.getAge().days == 60 :
#            self.__position.exitMarket()
#            print "Order exited at: $%.2f" % bar.getPrice()

def run_strategy(smaPeriod):
    # Load the yahoo feed from the CSV file
#    feed = yahoofeed.Feed()
#    feed.addBarsFromCSV("orcl", "orcl-2000.csv")
    feed = ibfeed.Feed()
    feed.addBarsFromCSV("bac", "samples/bac_2mois_7-9.csv")
    feed.addBarsFromCSV("bac20p20160819", "samples/bac_2000-p20160819.csv")

    # Evaluate the strategy with the feed.
#    myStrategy = MyStrategy(feed, "orcl", smaPeriod)
    myStrategy = MyStrategy(feed, "bac","bac20p20160819", smaPeriod)
    
    # Attach a returns analyzers to the strategy.
    returnsAnalyzer = returns.Returns()
    drawdownAnalyzer = drawdown.DrawDown()
    myStrategy.attachAnalyzer(returnsAnalyzer)
    myStrategy.attachAnalyzer(drawdownAnalyzer)
    
    
    # Attach the plotter to the strategy.
    plt = plotter.StrategyPlotter(myStrategy)
#    plt.getOrCreateSubplot("cash").addCallback("Cash", lambda x: myStrategy.getBroker().getCash())
    # Include the SMA in the instrument's subplot to get it displayed along with the closing prices.
    plt.getInstrumentSubplot("bac").addDataSeries("SMA", myStrategy.getSMA())
    # Plot the simple returns on each bar.
    plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", returnsAnalyzer.getReturns())

    myStrategy.run()
    print "Final portfolio value: $%.2f" % myStrategy.getBroker().getEquity()
    print "Final portfolio value: $%.2f" % myStrategy.getBroker().getEquity()
    print "Final mlonguest drawdown duration: %s" % str(drawdownAnalyzer.getLongestDrawDownDuration())

    plt.plot()
    
run_strategy(10)
