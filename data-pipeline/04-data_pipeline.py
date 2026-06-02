# !pip install yfinance
# !pip install pyarrow
# !pip install fastparquet
# You may need a VPN to connect to Yahoo Finance

import glob
import pickle
import datetime
import pandas as pd
import yfinance as yf
from typing import List

def download_data(path: str, start_day: str, end_day: str, tickers: List[str]) -> List[pd.DataFrame]:
    """Downloads adjusted close price data for given tickers within a date range."""
    df_list = []
    for ticker in tickers:
        print(f'Downloading data for {ticker}')
        data = yf.download(ticker, start=start_day, end=end_day)
        data = data.reset_index()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
        data['Date'] = data['Date'].dt.date
        data = data[['Date', 'Close']]
        data = data.rename(columns={'Date': 'date', 'Close': ticker})
        df_list.append(data)
    return df_list

def combine_dataframes(df_list: List[pd.DataFrame], path: str, tickers: List[str]) -> dict:
    """Combines dataframes of different tickers into a single dictionary and saves it as a pickle file."""
    df_dicts = [dict(zip(df['date'], df[ticker])) for df, ticker in zip(df_list, tickers)]
    combined_dict = {date: {'price': {}} for df_dict in df_dicts for date in df_dict}
    for i, df_dict in enumerate(df_dicts):
        for date, price in df_dict.items():
            combined_dict[date]['price'][tickers[i]] = price
    pkl_filename = path + 'price.pkl'
    with open(pkl_filename, 'wb') as file:
        pickle.dump(combined_dict, file)
    print(f'Price data saved to: {pkl_filename}')
    return combined_dict

def create_news_dict(news_path: str, csv_pattern: str, col_name: str) -> dict:
    """Creates a dictionary from news CSV files and saves it as a pickle file."""
    full_csv_pattern = news_path + csv_pattern
    csv_files = glob.glob(full_csv_pattern)
    combined_dict = {}
    for file in csv_files:
        df = pd.read_csv(file)
        df['date'] = pd.to_datetime(df['date']).dt.date
        symbol = df.at[0, 'symbols']
        for date, summary in df.groupby('date')[col_name].apply(list).items():
            if date not in combined_dict:
                combined_dict[date] = {'news': {}}
            combined_dict[date]['news'][symbol] = summary
    
    # Make sure the directory exists
    if not os.path.exists(news_path):
        os.makedirs(news_path)
    
    pkl_filename = news_path + 'news.pkl'
    with open(pkl_filename, 'wb') as file:
        pickle.dump(combined_dict, file)
    print(f'News data saved to: {pkl_filename}')
    return combined_dict

def process_filing_data(start_day: str, end_day: str, kq_path: str, filing_data: str, tickers: List[str]) -> (dict, dict):
    """Processes ITR/DFP data from parquet file."""
    import polars as pl
    import datetime
    
    nested_10q, nested_10k = {}, {}
    
    try:
        if os.path.exists(filing_data):
            df = pl.read_parquet(filing_data)
            start_date = datetime.datetime.strptime(start_day, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_day, "%Y-%m-%d")
            
            df_filtered = df.filter(
                (pl.col("est_timestamp") >= start_date) & 
                (pl.col("est_timestamp") <= end_date)
            )
            
            for row in df_filtered.iter_rows(named=True):
                # O price e news usam datetime.date como chaves, entao o filing tbm deve usar
                date_obj = row["est_timestamp"].date()
                content = row["content"]
                doc_type = row["type"]
                ticker_in_db = row["ticker"]
                
                # O ticker no DB é "PETR4", e no yahoo é "PETR4.SA"
                matched_ticker = next((t for t in tickers if t.startswith(ticker_in_db)), None)
                        
                if not matched_ticker:
                    continue
                    
                if doc_type in ["ITR", "10-Q"]:
                    if date_obj not in nested_10q:
                        nested_10q[date_obj] = {'filing_q': {}}
                    nested_10q[date_obj]['filing_q'][matched_ticker] = content
                elif doc_type in ["DFP", "10-K"]:
                    if date_obj not in nested_10k:
                        nested_10k[date_obj] = {'filing_k': {}}
                    nested_10k[date_obj]['filing_k'][matched_ticker] = content
        else:
            print(f"File {filing_data} not found. Skipping filings.")
    except Exception as e:
        print(f"Error loading filing data: {e}")
    
    q_filename = kq_path + 'filing_q.pkl'
    k_filename = kq_path + 'filing_k.pkl'
    
    with open(q_filename, 'wb') as file:
        pickle.dump(nested_10q, file)
    with open(k_filename, 'wb') as file:
        pickle.dump(nested_10k, file)
    print(f'10-K/DFP data saved to: {k_filename}')
    print(f'10-Q/ITR data saved to: {q_filename}')
    return nested_10q, nested_10k
    
if __name__ == '__main__':
    import os
    base_path = 'data/05_env_data'
    price_path = 'data/temp/'
    news_path = 'data/temp/'
    kq_path = 'data/temp/'
    filing_data = 'data/03_primary/filing_data_br.parquet'
    start_day = '2025-11-24'
    end_day = '2026-05-22'
    tickers = ['PETR3.SA', 'PETR4.SA']
    csv_files_pattern = 'cleaned_*.csv'
    col_name = 'summary'
    
    os.makedirs(base_path, exist_ok=True)
    os.makedirs(price_path, exist_ok=True)
    os.makedirs(news_path, exist_ok=True)
    os.makedirs(kq_path, exist_ok=True)

    df_list = download_data(price_path, start_day, end_day, tickers)
    price = combine_dataframes(df_list, price_path, tickers)
    news = create_news_dict(news_path, csv_files_pattern, col_name)
    q, k = process_filing_data(start_day, end_day, kq_path, filing_data, tickers)


    # Update dictionaries
    for date in price.keys():
        q.setdefault(date, {'filing_q': {}})
        k.setdefault(date, {'filing_k': {}})
        news.setdefault(date, {'news': {ticker: [] for ticker in tickers}})


    # Update news dictionary
    for date, data in news.items():
        if 'news' in data:
            missing_tickers = [ticker for ticker in tickers if ticker not in data['news']]
            for ticker in missing_tickers:
                news[date]['news'][ticker] = []
        if len(list(news[date]['news'].keys())) != len(tickers):
            print('ERROR on:',date)

    # Sorting dictionaries
    filled_q = dict(sorted(q.items()))
    filled_k = dict(sorted(k.items()))

    # Combining data
    env_data = {
        key: {
            'price': price.get(key, {}).get('price', {}),
            'news': news.get(key, {}).get('news', {}),
            'filing_q': filled_q.get(key, {}).get('filing_q', {}),
            'filing_k': filled_k.get(key, {}).get('filing_k', {})
        }
        for key in price.keys()
    }
    # Save the combined data
    output_path = f'{base_path}/env_data.pkl'
    with open(output_path, 'wb') as file:
        pickle.dump(env_data, file)

    print(f'Environment data saved to: {output_path}')


