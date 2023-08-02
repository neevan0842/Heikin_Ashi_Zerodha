from kiteconnect import KiteConnect
import pandas as pd
import sqlite3
import datetime as dt
import os
import numpy as np

access_token = open('/home/ec2-user/access_token.txt','r').read()
api_key = os.environ.get('Zerodha_API_Key')
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

#get dump of all NSE instruments
instrument_dump = kite.instruments('CDS')
instrument_df = pd.DataFrame(instrument_dump)

# Database file path
db=sqlite3.connect('/home/ec2-user/ticks.db')
c=db.cursor()

def create_tables(tokens):
    """
    Creates a table for each given token in the database, if it does not already exist.

    Parameters:
    tokens (list): A list of token symbols for which to create tables in the database.

    Returns:
    None

    """
    c = db.cursor()  # Get a cursor to execute SQL statements
    for i in tokens:
        # Create a table for each token symbol if it does not already exist
        c.execute("CREATE TABLE IF NOT EXISTS TOKEN{} (ts datetime primary key,price real(15,5), volume integer)".format(i))
    try:
        db.commit()  # Commit changes to the database
    except:
        db.rollback()  # Rollback changes if an error occurs

def instrumentLookup(instrument_df,symbol):
    """Looks up instrument token for a given script from instrument dump"""
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1
    
def tokenLookup(instrument_df,symbol_list):
    """Looks up instrument token for a given script from instrument dump"""
    token_list = []
    for symbol in symbol_list:
        token_list.append(int(instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]))
    return token_list

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

def fetchOHLC(ticker,interval,duration):
    """extracts historical data and outputs in the form of dataframe"""
    instrument = instrumentLookup(instrument_df,ticker)
    data = pd.DataFrame(kite.historical_data(instrument,dt.date.today()-dt.timedelta(duration), dt.date.today(),interval,oi=True))
    return data

tickers=['USDINR','EURINR']
tickers=contracts_closest(tickers, instrument_df)
tokens = tokenLookup(instrument_df,tickers)

#create table
create_tables(tokens)

for ticker in tickers:
    token=instrumentLookup(instrument_df, ticker)
    
    data=fetchOHLC(ticker, 'minute', 20)
    data=data[['date','close','volume']]
    data=data.rename(columns={'date':'ts','close':'price'})
    data = data.set_index(['ts'])
    data.index = data.index.tz_convert('UTC')
    data.index = data.index.strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute("DELETE FROM TOKEN{}".format(token))
    data.to_sql('TOKEN{}'.format(token), db, if_exists='append', index=True)

    db.commit()
    
db.close()
