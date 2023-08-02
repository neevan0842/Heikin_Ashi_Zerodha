from kiteconnect import KiteTicker, KiteConnect
import pandas as pd
import os
import sqlite3
import datetime as dt
import numpy as np

access_token = open('/home/ec2-user/access_token.txt','r').read()
api_key = os.environ.get('Zerodha_API_Key')
kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

db=sqlite3.connect('/home/ec2-user/ticks.db')

#get dump of all NSE instruments
instrument_dump = kite.instruments('CDS')
instrument_df = pd.DataFrame(instrument_dump)
    
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

def insert_ticks(ticks):
    """
    Inserts ticks data into the corresponding table in the database.
    
    Args:
    ticks : list of dictionaries - Contains ticks data for various instruments
    
    Returns:
    None
    """
    c=db.cursor()
    for tick in ticks:
        try:
            tok = "TOKEN"+str(tick['instrument_token'])
            vals = [tick['exchange_timestamp'],tick['last_price'], tick['last_traded_quantity']]
            query = "INSERT INTO {}(ts,price,volume) VALUES (?,?,?)".format(tok)
            c.execute(query,vals)
        except:
            pass
    try:
        db.commit()
    except:
        db.rollback()

def instrumentLookup(instrument_df, symbol):
    """
    Looks up instrument token for a given script from instrument dump.

    Parameters:
    instrument_df (pandas.DataFrame): DataFrame containing instrument dump.
    symbol (str): Symbol of the instrument for which the token is to be looked up.

    Returns:
    int: Instrument token if found, else returns -1.
    """
    try:
        return instrument_df[instrument_df.tradingsymbol==symbol].instrument_token.values[0]
    except:
        return -1


def tokenLookup(instrument_df,symbol_list):
    """
    Looks up instrument token for a given script from instrument dump
    
    Parameters:
    instrument_df (DataFrame): DataFrame containing instrument information
    symbol_list (list): List of trading symbols for which token is to be looked up
    
    Returns:
    list: List of instrument tokens corresponding to the given trading symbols
    """
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

tickers=['USDINR','EURINR']
tickers=contracts_closest(tickers, instrument_df)

#create KiteTicker object
kws = KiteTicker(os.environ.get('Zerodha_API_Key'),kite.access_token)
tokens = tokenLookup(instrument_df,tickers)

#create table
create_tables(tokens)

def on_ticks(ws,ticks):
    insert_ticks(ticks)

def on_connect(ws,response):
    ws.subscribe(tokens)
    ws.set_mode(ws.MODE_FULL,tokens)  

while True:   
    kws.on_ticks=on_ticks
    kws.on_connect=on_connect
    kws.connect()
