import pandas as pd
import sqlite3
import datetime as dt

# Database file path
db=sqlite3.connect('/home/ec2-user/ticks.db')
c=db.cursor()

tables=[]
c.execute('SELECT name from sqlite_master where type= "table"')
for a in c.fetchall():
    tables.append(a[0])

for table in tables:
     
    start_date = dt.datetime.now() - dt.timedelta(days=20)
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    data = pd.read_sql("SELECT * FROM {} WHERE ts >= '{}';".format(table,start_date_str), con=db)                
    data = data.set_index(['ts'])
    data.index = pd.to_datetime(data.index)

    data=data.resample('1T').last().dropna() 
    
    c.execute('DELETE FROM {}'.format(table))
    data.to_sql('{}'.format(table), db, if_exists='append', index=True)
    
    db.commit()  
    
db.close()
