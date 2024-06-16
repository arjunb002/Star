import json
import numpy as np
import yfinance as yf
import pandas as pd
import pickle
import pandas_ta as ta
import datetime
import requests
from time import sleep

API = "https://app.threeten.in/sorcery/remote.php"


print("Initializing REST Client...")

def isEndPointAlive():
    url = API
    response = requests.get(url)
    return response.status_code == 200
if __name__ == '__main__':
    print("Checking endpoint status...")
    # response = requests.post("{0}?mannual-ssu".format(API), data={"data": "test"})
    # print("Data sent to endpoint...")
    # print(response)
    # print(response.text)
    # exit()
    try:
        if isEndPointAlive():
            print("Endpoint is UP!");
            sleep(1)
            print("\nStarting processing data\n\n\n")
            sleep(1)
            with open("./data/stock_list_500.py", "rb") as file:
                stock_dict_500 = pickle.load(file)
            def signal_ind(sticker, stock_name):

                lookback = 100
                demand_threshold = 2

                symbol = '{}.NS'.format(sticker)

                _df = yf.download(symbol) 
                df = _df.tail(365)
                
                df['demand'] = df['High'].rolling(window=lookback).max() - df['Low']
                df['supply'] = df['Low'] - df['Low'].rolling(window=lookback).min()

                df['long_signal'] = False
                df['short_signal'] = False

                df.loc[(df['demand'] > demand_threshold) & (df['supply'] < df['demand']), 'long_signal'] = True
                df.loc[(df['supply'] > df['demand']) & (df['demand'] < demand_threshold), 'short_signal'] = True
                
                all_time_high_365 = df.tail(365)['Close'].max()
                max_drawdown = all_time_high_365 * 0.9
                min_drawdown = all_time_high_365 * 0.7
                
                df_new = df.iloc[[-1]]
                
                if (df.iloc[-1]['long_signal'] == True) and (df.iloc[-1]['Close'] >= min_drawdown) and (df.iloc[-1]['Close'] <= max_drawdown):
                    df_new['Filter_1'] = 'Yes'
                else:
                    df_new['Filter_1'] = 'No'


                all_time_high = df['High'].max()
                current_price = df['Close'].iloc[-1]

                if current_price >= (0.95 * all_time_high) and current_price <= (1.05 * all_time_high):
                    df_new['Filter_2'] = 'Yes'
                else:
                    df_new['Filter_2'] = 'No'

                    
                last_30_days_data = df.iloc[-30:]
                min_price = current_price * 0.90  # 5% below the all-time high
                max_price = current_price * 1.05  # 1% above the all-time high
                within_range = all(
                    min_price <= price <= max_price
                    for price in last_30_days_data['Close']
                )

                if within_range:
                    df_new['Filter_3'] = 'Yes'
                else:
                    df_new['Filter_3'] = 'No'
                    
                return df_new
            
            buy_df1 = pd.DataFrame()
            buy_df2 = pd.DataFrame()
            buy_df3 = pd.DataFrame()
            for i in stock_dict_500.keys():
                symbol = stock_dict_500[i]
                try:
                    df_new = signal_ind(symbol, i)
                    if df_new.iloc[-1]['Filter_1'] == 'Yes':
                        buy_df1 = pd.concat([buy_df1, pd.DataFrame([{'Stock Name':i, 'Current Price' : df_new.iloc[-1]['Close']}])])
                    if df_new.iloc[-1]['Filter_2'] == 'Yes':
                        buy_df2 = pd.concat([buy_df2, pd.DataFrame([{'Stock Name':i, 'Current Price' : df_new.iloc[-1]['Close']}])])
                    if df_new.iloc[-1]['Filter_3'] == 'Yes':
                        buy_df3 = pd.concat([buy_df3, pd.DataFrame([{'Stock Name':i, 'Current Price' : df_new.iloc[-1]['Close']}])])
                except:
                    pass
            try:
                buy_df1.reset_index(inplace=True, drop=True)
                common_stocks = pd.merge(buy_df2[['Stock Name','Current Price']], buy_df3[['Stock Name']], on='Stock Name', how='inner')
                print(buy_df1.head(2))
                print(common_stocks.head(2))
                # col1.dataframe(buy_df1.sort_index())
                # col2.dataframe(common_stocks.sort_index())
                col1_data = buy_df1.sort_index().to_dict(orient='records')
                col2_data = common_stocks.sort_index().to_dict(orient='records')
            except:
                pass
            data = json.dumps({
                "buy_df1": col1_data,
                "common_stocks": col2_data
            })
            print("Data prepared for sending...")
            print(data)
            print("Sending data to endpoint...")
            response = requests.post("{0}?mannual-ssu".format(API), data={
                "data": data
            })
            print("Data sent to endpoint...")
            print(response)
            print(response.text)
            print("Script execution completed!\nSee you soon :)")
        else:
            print("Cannot connect to endpoint! Aborting...")
    except Exception as e:
        print("Something went wrong\n{}".format(e))