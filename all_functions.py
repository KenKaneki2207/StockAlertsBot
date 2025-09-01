import yfinance as yf
import talib
import numpy as np

def all_indicators(data):
    data['Pricedown'] = data['Close'] < data['Close'].shift(1)
    data['Priceup'] = data['Close'] > data['Close'].shift(1)

    data['Ema5'] = talib.EMA(data['Close'], timeperiod=5)
    data['Ema10'] = talib.EMA(data['Close'], timeperiod=10)
    data['EMA_Crossover'] = np.where(
        (data['Ema5'] > data['Ema10']) & (data['Ema5'].shift(1) <= data['Ema10'].shift(1)), 1,
        np.where(
            (data['Ema5'] < data['Ema10']) & (data['Ema5'].shift(1) >= data['Ema10'].shift(1)), -1,
            0
        )
    )

    macd_line, macd_signal, macd_hist = talib.MACD(
        data['Close'],
        fastperiod=5,
        slowperiod=13,
        signalperiod=6
    )

    data['MACD_Line'] = macd_line
    data['MACD_Signal'] = macd_signal

    data['MACD_Crossover'] = np.where(
        (data['MACD_Line'] > data['MACD_Signal']) & (data['MACD_Line'].shift(1) <= data['MACD_Signal'].shift(1)), 1,
        np.where(
            (data['MACD_Line'] < data['MACD_Signal']) & (data['MACD_Line'].shift(1) >= data['MACD_Signal'].shift(1)), -1,
            0
        )
    )

    rsi = talib.RSI(data['Close'], 9)
    data['RSI'] = rsi
    data['RSIup'] = data['RSI'] > data['RSI'].shift(1)
    data['RSIdown'] = data['RSI'] < data['RSI'].shift(1)

    data.reset_index(inplace=True)
    data['Datetime'] = data['Datetime'].apply(lambda x: x.strftime('%Y-%m-%d %H:%M:%S'))
    return data

stocks = ['ADANIPOWER', 'UNIONBANK', 'BHEL', 'OIL', 'RVNL', 'SUZLON', 'PNB', 'GAIL', 
          'ETERNAL', 'HINDALCO', 'BEL', 'NTPC', 'BPCL', 'TATAMOTORS', 'ONGC']

def get_data(stock):
    data = yf.Ticker(f'{stock}.NS').history(period="5d", interval="5m")
    return data

def analyse_candles(df, rsi , signal):
    message = {
        'Stock': '',
        'Datetime': df.iloc[-1]['Datetime'],
        'Signal': signal,
        'EMA_Crossover': False,
        'RSI': rsi,
        'MACD_Crossover': False, 
    }

    c1,c2,c3 = Candle(df.iloc[-1]), Candle(df.iloc[-2]), Candle(df.iloc[-3])
    message['Pattern'] = c1.detect_pattern(prev=c2, prev_prev=c3)
    last_row = df.iloc[-1]

    if signal == "Bull":
        if last_row['MACD_Crossover'] == 1:
            message['MACD_Crossover'] = True
        
        elif last_row['EMA_Crossover'] == 1:
            message['EMA_Crossover'] = True

    else:
        if last_row['MACD_Crossover'] == -1:
            message['MACD_Crossover'] = True
        
        elif last_row['EMA_Crossover'] == -1:
            message['EMA_Crossover'] = True
    
    return message

            
def signal_catcher(stock_data):
    row =  stock_data.iloc[-5:]

    message = {}
    
    if row['RSI'].min() < 25:
        message = analyse_candles(row, row['RSI'].min(), 'Bull')
    elif row['RSI'].max() > 75:
        message = analyse_candles(row, row['RSI'].max(), 'Bear')

    if message != {}:
        c1,c2,c3 = Candle(stock_data.iloc[-1]), Candle(stock_data.iloc[-2]), Candle(stock_data.iloc[-3])
        message['Pattern'] = c1.detect_pattern(prev=c2, prev_prev=c3)

    return message

class Candle:
    def __init__(self, candle):
        self.open = candle['Open']
        self.high = candle['High']
        self.low = candle['Low']
        self.close = candle['Close']

        self.full = self.high - self.low  # total candle range

        body_size = abs(self.close - self.open)
        top_wick = self.high - max(self.open, self.close)
        bottom_wick = min(self.open, self.close) - self.low

        # % relative to full candle
        self.top = (top_wick / self.full) * 100 if self.full else 0
        self.bottom = (bottom_wick / self.full) * 100 if self.full else 0
        self.body = (body_size / self.full) * 100 if self.full else 0

        # bullish or bearish
        self.is_bullish = self.close > self.open
        self.is_bearish = self.open > self.close

    # ---------- Single Candle Patterns ----------
    def is_doji(self, threshold=10): return self.body <= threshold
    def is_hammer(self): return (self.bottom >= 60 and self.top <= 20 and self.body <= 30)
    def is_inverted_hammer(self): return (self.top >= 60 and self.bottom <= 20 and self.body <= 30)
    def is_shooting_star(self): return (self.top >= 60 and self.body <= 30)
    def is_marubozu(self): return (self.top <= 5 and self.bottom <= 5)

    # ---------- Double Candle Patterns ----------
    def is_bullish_engulfing(self, prev): 
        return (prev.is_bearish and self.is_bullish and self.close > prev.open and self.open < prev.close)
    def is_bearish_engulfing(self, prev): 
        return (prev.is_bullish and self.is_bearish and self.close < prev.open and self.open > prev.close)
    def is_piercing_line(self, prev): 
        midpoint = (prev.open + prev.close) / 2
        return (prev.is_bearish and self.is_bullish and self.open < prev.low and self.close > midpoint)
    def is_dark_cloud_cover(self, prev): 
        midpoint = (prev.open + prev.close) / 2
        return (prev.is_bullish and self.is_bearish and self.open > prev.high and self.close < midpoint)

    # ---------- Triple Candle Patterns ----------
    def is_morning_star(self, prev, prev_prev): 
        return (prev_prev.is_bearish and prev.is_doji() and self.is_bullish and 
                self.close > (prev_prev.open + prev_prev.close) / 2)
    def is_evening_star(self, prev, prev_prev): 
        return (prev_prev.is_bullish and prev.is_doji() and self.is_bearish and 
                self.close < (prev_prev.open + prev_prev.close) / 2)

    # ---------- Pattern Detector ----------
    def detect_pattern(self, prev=None, prev_prev=None):
        """Detects the candlestick pattern and returns name as string"""

        # Single candle
        if self.is_doji(): return "Doji"
        if self.is_hammer(): return "Hammer"
        if self.is_inverted_hammer(): return "Inverted Hammer"
        if self.is_shooting_star(): return "Shooting Star"
        if self.is_marubozu(): return "Marubozu"

        # Double candle
        if prev:
            if self.is_bullish_engulfing(prev): return "Bullish Engulfing"
            if self.is_bearish_engulfing(prev): return "Bearish Engulfing"
            if self.is_piercing_line(prev): return "Piercing Line"
            if self.is_dark_cloud_cover(prev): return "Dark Cloud Cover"

        # Triple candle
        if prev and prev_prev:
            if self.is_morning_star(prev, prev_prev): return "Morning Star"
            if self.is_evening_star(prev, prev_prev): return "Evening Star"

        return None