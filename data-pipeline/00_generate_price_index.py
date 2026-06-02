import os
import pandas as pd
import yfinance as yf

TICKER = "PETR4.SA"
START_DATE = "2025-11-22"
END_DATE = "2026-05-22" 

def main():
    print(f"Downloading price index for {TICKER} from {START_DATE} to {END_DATE}")
    df = yf.download(TICKER, start=START_DATE, end=END_DATE)
    df = df.reset_index()
    date_col = df.iloc[:, 0]
    
    new_df = pd.DataFrame({"est_time": date_col, "equity": TICKER})
    
    out_dir = os.path.join("data", "03_primary")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "price_data.parquet")
    new_df.to_parquet(out_path, index=False)
    print(f"Saved {len(new_df)} records to {out_path}")

if __name__ == "__main__":
    main()
