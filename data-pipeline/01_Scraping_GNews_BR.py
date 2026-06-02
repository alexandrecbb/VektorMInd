import os
import pandas as pd
import datetime
from gnews import GNews
from time import sleep

# Tickers e mapeamento
TICKERS = ['PETR3.SA', 'PETR4.SA']
SEARCH_TERMS = {
    'PETR3.SA': 'Petrobras',
    'PETR4.SA': 'Petrobras'
}

START_DATE = datetime.date(2025, 11, 24)
END_DATE = datetime.date(2026, 5, 22)

def fetch_news_for_date(search_term, target_date):
    """
    Busca notícias usando gnews para uma data específica.
    """
    # GNews aceita tuplas (ano, mes, dia)
    start = (target_date.year, target_date.month, target_date.day)
    
    # Para forçar a busca em um dia específico, o end_date é o dia seguinte
    next_day = target_date + datetime.timedelta(days=1)
    end = (next_day.year, next_day.month, next_day.day)
    
    google_news = GNews(language='pt', country='BR', start_date=start, end_date=end, max_results=5)
    news_items = google_news.get_news(search_term)
    
    summaries = []
    if news_items:
        for item in news_items:
            # Pegamos o titulo como resumo principal
            summaries.append(item.get('title', ''))
    
    return summaries

def generate_gnews_csv(ticker, start_date, end_date):
    print(f"Iniciando raspagem de notícias para {ticker} ({SEARCH_TERMS[ticker]})...")
    
    # Lista de dias úteis
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    data = []
    
    for dt in dates:
        date_obj = dt.date()
        summaries = fetch_news_for_date(SEARCH_TERMS[ticker], date_obj)
        
        if not summaries:
            # Adiciona uma string vazia para manter a consistência se não houver notícias
            data.append({'date': date_obj, 'symbols': ticker, 'summary': "Sem notícias relevantes."})
        else:
            for s in summaries:
                data.append({'date': date_obj, 'symbols': ticker, 'summary': s})
                
        # Pausa para não sobrecarregar o Google
        sleep(0.5)

    df = pd.DataFrame(data)
    
    out_dir = os.path.join("data", "temp")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"cleaned_{ticker}.csv")
    df.to_csv(out_path, index=False)
    print(f"Salvo: {out_path} com {len(df)} notícias.")

if __name__ == "__main__":
    for ticker in TICKERS:
        generate_gnews_csv(ticker, START_DATE, END_DATE)
