import os
import pandas as pd
from tqdm import tqdm
import threading
import concurrent.futures

# We need to import our Gemini Model Wrapper
import sys
import importlib.util
spec = importlib.util.spec_from_file_location("model_wrapper", os.path.join(os.path.dirname(os.path.abspath(__file__)), "03-model_wrapper.py"))
model_wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model_wrapper)
Model_Factory = model_wrapper.Model_Factory

# API Key passed from environment
api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyA4KsJN9jLeq2zddE593xNDzDaHKEK4DEQ")
model = Model_Factory.create_model('gemini', key=api_key, model_name="gemini-flash-latest")

def process_row(row, lock, df):
    text_to_summarize = row['body'] if pd.notna(row.get('body')) and row['body'] != '' else ''
    if not text_to_summarize:
        result = "No news"
    else:
        try:
            result = model.summarize(text_to_summarize)
        except Exception as e:
            print(f"Failed to summarize: {e}")
            result = text_to_summarize[:200]
            
    with lock:
        df.at[row.name, 'summary'] = result

def parallel_summary(df):
    lock = threading.Lock()
    df_copy = df.copy()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_row, row, lock, df_copy) for _, row in df.iterrows()]
        concurrent.futures.wait(futures)
    return df_copy

def main():
    source_file = "data/temp/TSLA_fake.csv"
    if not os.path.exists(source_file):
        print(f"Error: {source_file} not found.")
        return
        
    print(f"Processing {source_file}")
    df = pd.read_csv(source_file)
    
    df['date'] = pd.to_datetime(df['date'])
    mask = (df['date'] >= '2016-01-15') & (df['date'] <= '2016-02-15')
    df = df.loc[mask].copy()
    
    # We want to output: date, symbols, summary
    
    # Limit number of news items per day to avoid hitting rate limits too hard (optional, let's take up to 3 per day)
    df = df.groupby(['date', 'symbols']).head(3).reset_index(drop=True)
    
    print(f"Total rows to summarize: {len(df)}")
    df['summary'] = None
    
    ret_df = parallel_summary(df)
    
    # Keep only required columns
    final_df = ret_df[['date', 'symbols', 'summary']]
    
    out_dir = "data/temp"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cleaned_TSLA.csv")
    final_df.to_csv(out_path, index=False)
    print(f"New DF dumped to {out_path}")

if __name__ == "__main__":
    main()