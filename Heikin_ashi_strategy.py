from kiteconnect import KiteConnect
import numpy as np
import pandas as pd
import sqlite3
import datetime as dt
import time
import os
import talib

access_token = open('/home/ec2-user/access_token.txt','r').read()
api_key = os.environ.get('Zerodha_API_Key')
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

db=sqlite3.connect('/home/ec2-user/ticks.db')

#get dump of all NSE instruments
instrument_dump = kite.instruments('CDS')
instrument_df = pd.DataFrame(instrument_dump)

def tokenLookup(instrument_df,symbol_list):
    """Looks up instrument token for a given script from instrument dump"""
    token_list = []
    for symbol in symbol_list:
        token_list.append(int(instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]))
    return token_list

def tickerLookup(token):
    global instrument_df
    return instrument_df[instrument_df.instrument_token==token].tradingsymbol.values[0] 

def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1
    
def contracts_closest(tickers, instrument_df, duration=0, option_type='FUT', exchange='CDS'):
    data=pd.DataFrame()
    for ticker in tickers:
        conditions = (instrument_df['name'] == ticker) & (instrument_df['instrument_type'] == option_type) & (instrument_df['exchange'] == exchange)
        df = instrument_df.loc[conditions]
        df = df[df['tradingsymbol'].str.contains(r'{}\d{{2}}[A-Z]+FUT'.format(ticker))]
        df["time_to_expiry"] = (pd.to_datetime(df["expiry"]) - dt.datetime.now()).dt.days
        min_day_count = np.sort(df["time_to_expiry"].unique())[duration]
        df=df[df["time_to_expiry"] == min_day_count].reset_index(drop=True)
        data=pd.concat([data,df],axis=0)
    return data['tradingsymbol'].tolist()

def get_df_from_sql(ticker, db):
    """
    Retrieves historical price data for a given ticker from the specified database 
    and resamples the data to the specified time interval.
    
    Args:
    - ticker (str): the trading symbol of the instrument
    - db: the database connection object
    - interval (str): the time interval to which the data should be resampled (e.g. '1H', '1D')
    
    Returns:
    - df (pandas.DataFrame): a dataframe containing the resampled historical price data
    """
    token = instrumentLookup(instrument_df, ticker)
    start_date = dt.datetime.now() - dt.timedelta(days=20)
    start_date_str = start_date.strftime('%Y-%m-%d')
    data = pd.read_sql("SELECT * FROM TOKEN{} WHERE ts >= '{}';".format(token,start_date_str), con=db)                
    data = data.set_index(['ts'])
    data.index = pd.to_datetime(data.index)
    df = data.loc[:, ['price']]   
    return df

def heikin_ashi(df):
    '''
    Given a DataFrame `df` with a Pandas.DatetimeIndex and (at least the following)
    columns "Open", "High", "Low", and "Close", this function will construct and return a
    DataFrame of Heikin Ashi candles  w/columns "HAOpen", "HAHigh", "HALow", and "HAClose" 
    '''
    ha_close = (df['open'] + df['high'] + df['low'] + df['close'])/4
    ha_df = pd.DataFrame(dict(HAClose=ha_close))
    ha_df['HAOpen']  = [0.0]*len(df)
    # "seed" the first open:
    prekey = df.index[0]
    ha_df.at[prekey,'HAOpen'] = df.at[prekey,'open']
    # calculate the rest  
    for key in df.index[1:]:
        ha_df.at[key,'HAOpen'] = (ha_df.at[prekey,'HAOpen'] + ha_df.at[prekey,'HAClose']) / 2.0
        prekey = key
    ha_df['HAHigh']  = pd.concat([ha_df.HAOpen,df.high],axis=1).max(axis=1)
    ha_df['HALow']   = pd.concat([ha_df.HAOpen,df.low ],axis=1).min(axis=1)      
    return ha_df

def round_to_tick(number,tick_size):
    rounded_number = round(number / tick_size) * tick_size
    return rounded_number

def df_4(ticker):
    df=get_df_from_sql(ticker, db)
    df=df['price'].resample('D').ohlc().dropna()
    df['SAR']=talib.SAR(df['high'], df['low'])
    df['SAR_pos']=np.where(df['SAR']>df['high'],-1,np.where(df['SAR']<df['low'],1,0))
    return df
    
def df_1(ticker):
    df=get_df_from_sql(ticker, db)
    df=df['price'].resample('3H').ohlc().dropna()
    df['ema10']=talib.EMA(df['close'],10)
    df['ema30']=talib.EMA(df['close'],30)
    ha_df=heikin_ashi(df)
    df=pd.concat([df,ha_df],axis=1)
    con1=(df['HAOpen']==df['HALow']) & (df['HAClose']>df['HAOpen'])
    con2=(df['HAOpen']==df['HAHigh']) & (df['HAOpen']>df['HAClose'])
    df['candle_type']=np.where(con1,1,np.where(con2,-1,0))
    return df

def current_pos(ticker):
    a = 0
    while a < 10:
        try:
            pos_df = pd.DataFrame(kite.positions()["net"])   #net or day
            break
        except:
            a += 1
    if len(pos_df.columns) == 0:
        return 0
    if len(pos_df.columns) != 0 and ticker not in pos_df["tradingsymbol"].tolist():
        return 0
    if len(pos_df.columns) != 0 and ticker in pos_df["tradingsymbol"].tolist():
        quantity = pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0]
        if quantity == 0:
            return 0
        elif quantity > 0:
            return 1
        else:
            return -1
        
def get_pos_details(ticker):
    dic = dict()
    a, b = 0, 0
    while a < 10:
        try:
            pos_df = pd.DataFrame(kite.positions()["net"])  #net or day
            break
        except:
            print("Can't extract position data... retrying")
            a += 1
    while b < 10:
        try:
            ord_df = pd.DataFrame(kite.orders())
            break
        except:
            print("Can't extract order data... retrying")
            b += 1
    dic["quantity"] = pos_df[pos_df["tradingsymbol"] == ticker]["quantity"].values[0]
    dic['trigger_price'] = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING", "OPEN"]))]["trigger_price"].values[0]
    dic['last_price'] = pos_df[pos_df["tradingsymbol"] == ticker]["last_price"].values[0]
    dic['order_id'] = ord_df.loc[(ord_df['tradingsymbol'] == ticker) & (ord_df['status'].isin(["TRIGGER PENDING", "OPEN"]))]["order_id"].values[0]
    return dic

def check_exit(pos, ticker):
    df1 = df_1(ticker)
    if (pos == 1) and (df1['candle_type'][-1] == -1):
        return True
    elif (pos == -1) and (df1['candle_type'][-1] == 1):
        return True
    else:
        return False
    
def placeSLOrder(symbol,buy_sell,quantity,sl_price):    
    # Place an stop loss order on NSE
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
        t_type_sl=kite.TRANSACTION_TYPE_SELL
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
        t_type_sl=kite.TRANSACTION_TYPE_BUY
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_CDS,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_NRML,
                    variety=kite.VARIETY_REGULAR)
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_CDS,
                    transaction_type=t_type_sl,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_SLM,
                    trigger_price = round_to_tick(sl_price,0.0025),
                    product=kite.PRODUCT_NRML,
                    variety=kite.VARIETY_REGULAR)
    
def placeMarketOrder(symbol,buy_sell,quantity):    
    # Place an market order on NSE
    if buy_sell == "buy":
        t_type=kite.TRANSACTION_TYPE_BUY
    elif buy_sell == "sell":
        t_type=kite.TRANSACTION_TYPE_SELL
    kite.place_order(tradingsymbol=symbol,
                    exchange=kite.EXCHANGE_CDS,
                    transaction_type=t_type,
                    quantity=quantity,
                    order_type=kite.ORDER_TYPE_MARKET,
                    product=kite.PRODUCT_NRML,
                    variety=kite.VARIETY_REGULAR)

def CancelOrder(order_id):    
    kite.cancel_order(order_id=order_id,
                    variety=kite.VARIETY_REGULAR)  

def ModifyOrder(order_id,price):    
    # Modify order given order id
    kite.modify_order(order_id=order_id,
                    trigger_price=round_to_tick(price, 0.0025),
                    order_type=kite.ORDER_TYPE_SLM,
                    variety=kite.VARIETY_REGULAR) 
    
def param_refresh(ticker):
    global param
    df1 = df_1(ticker)
    df4 = df_4(ticker)
    
    if df1['ema10'][-1] > df1['ema30'][-1]:
        param[ticker]['EMA_xover'] = 1
    elif df1['ema10'][-1] < df1['ema30'][-1]:
        param[ticker]['EMA_xover'] = -1
    
    param[ticker]['SAR'] = df4['SAR_pos'][-1]
    param[ticker]['candle_type'] = df1['candle_type'][-1]
    param[ticker]['current_pos'] = current_pos(ticker)
    
def main():
    
    for ticker in tickers:
        try:
            param_refresh(ticker)
            a = instrumentLookup(instrument_df, ticker)
            b = kite.ltp(a)[str(a)]['last_price']
            quantity = 1    #int(capital / b )
            
            if param[ticker]['current_pos'] == 0:
                if (param[ticker]['SAR'] == 1) and (param[ticker]['candle_type'] == 1) and (param[ticker]['EMA_xover'] == 1):
                    print('buy {} at {}'.format(ticker,dt.datetime.now()))
                    placeSLOrder(ticker, 'buy', quantity, (b - param[ticker]['sl_price']))
                if (param[ticker]['SAR'] == -1) and (param[ticker]['candle_type'] == -1) and (param[ticker]['EMA_xover'] == -1):
                    print('sell {} at {}'.format(ticker,dt.datetime.now()))
                    placeSLOrder(ticker, 'sell', quantity, (b + param[ticker]['sl_price']))
        except Exception as e:
            print("API error for ticker:", ticker)
            print(e)  
    
    n = 0 
    while n <= 2:
        for ticker in tickers:
            try:
                param_refresh(ticker)
                
                if param[ticker]['current_pos'] != 0:
                    pos_dict = get_pos_details(ticker)
                    
                    if param[ticker]['current_pos'] == 1:
                        if check_exit(1, ticker):
                            print('exit {} '.format(ticker))
                            placeMarketOrder(ticker, 'sell', pos_dict['quantity'])
                            CancelOrder(pos_dict['order_id'])
                        elif ((pos_dict['last_price'] - pos_dict['trigger_price']) > (param[ticker]['sl_price'] * 1.1)):
                            print('modify {}'.format(ticker))
                            ModifyOrder(pos_dict['order_id'], (pos_dict['last_price'] - param[ticker]['sl_price']))
                    
                    if param[ticker]['current_pos'] == -1:
                        if check_exit(-1, ticker):
                            print('exit {}'.format(ticker))
                            placeMarketOrder(ticker, 'buy', pos_dict['quantity'])
                            CancelOrder(pos_dict['order_id'])
                        elif ((pos_dict['trigger_price'] - pos_dict['last_price']) > (param[ticker]['sl_price'] * 1.1)):
                            print('modify {}'.format(ticker))
                            ModifyOrder(pos_dict['order_id'], (pos_dict['last_price'] + param[ticker]['sl_price']))
            except Exception as e:
                print("API error for ticker:", ticker)
                print(e)  
                
        time.sleep(3595)     # 3600 seconds (1 hour) interval between each execution 
        n += 1


tickers=['USDINR','EURINR']
tickers=contracts_closest(tickers, instrument_df)
capital = 10000
param = {}

for ticker in tickers:
    df1 = df_1(ticker)
    df4 = df_4(ticker)
    atr = talib.ATR(df1['high'], df1['low'], df1['close'], 14)[-1]
    
    param[ticker] = {
        'SAR': df4['SAR_pos'][-1],
        'EMA_xover': None,
        'candle_type': df1['candle_type'][-1],
        'current_pos': current_pos(ticker),
        'sl_price': round_to_tick((atr), 0.0025)
    }

# Continuous execution
starttime = time.time()
end_time = time.mktime(time.strptime(time.strftime('%Y-%m-%d 17:00:00'), '%Y-%m-%d %H:%M:%S'))

while time.time() <= end_time:
    try:
        main()
        time.sleep(10800 - ((time.time() - starttime) % 10800))  # 10800 seconds (3 hour) interval between each execution
    except KeyboardInterrupt:
        exit('end')

