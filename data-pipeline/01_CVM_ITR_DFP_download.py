# parameters
NUM_WORKERS = 1
CVM_URLS = {
    "ITR": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/itr_cia_aberta_{year}.zip",
    "DFP": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{year}.zip"
}

# Anos para download (ajuste conforme necessário)
YEARS = [2024, 2025, 2026]

# Mapeamento de Tickers para Codigo CVM (Exemplos)
# Você pode adicionar mais empresas conforme necessário
TICKER_TO_CVM = {
    "PETR4": 9512,
    "VALE3": 4170,
    "ITUB4": 19348,
    "BBDC4": 906,
    "ABEV3": 24513
}

# dependencies
import os
import io
import httpx
import zipfile
import logging
import polars as pl
from tqdm import tqdm
from rich import print
from datetime import datetime

# set up logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
os.makedirs(os.path.join("data", "03_primary"), exist_ok=True)
handler = logging.FileHandler(
    os.path.join("data", "03_primary", "cvm_filing_fails.log"), mode="w"
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info("Program starts")

def download_and_extract_cvm(year: int, doc_type: str) -> pl.DataFrame:
    """
    Faz o download do arquivo ZIP da CVM e extrai as contas principais 
    do Balanço Patrimonial e DRE (Consolidados).
    """
    url = CVM_URLS[doc_type].format(year=year)
    logger.info(f"Downloading {url}")
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url)
            response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return pl.DataFrame()
    
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    
    # Lendo DRE (Demonstração de Resultado do Exercício) Consolidado
    dre_filename = f"{doc_type.lower()}_cia_aberta_DRE_con_{year}.csv"
    bpa_filename = f"{doc_type.lower()}_cia_aberta_BPA_con_{year}.csv"
    bpp_filename = f"{doc_type.lower()}_cia_aberta_BPP_con_{year}.csv"
    
    try:
        with zip_file.open(dre_filename) as f:
            dre_df = pl.read_csv(f.read(), separator=";", encoding="latin1")
        with zip_file.open(bpa_filename) as f:
            bpa_df = pl.read_csv(f.read(), separator=";", encoding="latin1")
        with zip_file.open(bpp_filename) as f:
            bpp_df = pl.read_csv(f.read(), separator=";", encoding="latin1")
            
        # Juntar todas as contas num único DataFrame lidando com colunas diferentes
        df = pl.concat([dre_df, bpa_df, bpp_df], how="diagonal")
        return df
    except Exception as e:
        logger.error(f"Error reading CSVs from {url}: {e}")
        return pl.DataFrame()

def process_company_data(df: pl.DataFrame, cvm_code: int, ticker: str, doc_type: str) -> pl.DataFrame:
    """
    Filtra os dados de uma empresa específica e transforma os números 
    contábeis em um formato de texto longo ('content') compreensível por uma LLM.
    """
    # Filtra empresa convertendo para inteiro para evitar bugs de string vs int
    company_df = df.filter(pl.col("CD_CVM").cast(pl.Int64, strict=False) == cvm_code)
    
    if company_df.is_empty():
        return pl.DataFrame()

    # Pega apenas os dados da data mais recente de cada entrega
    # Pega apenas os dados da data mais recente de cada entrega (ÚLTIMO ou ULTIMO)
    # Como pode haver variação de encoding ('ÚLTIMO', 'ULTIMO'), evitamos comparar a string exata
    # e focamos em remover o "PENÚLTIMO" se houver, ou apenas pegar a data mais recente depois.
    company_df = company_df.filter(~pl.col("ORDEM_EXERC").str.starts_with("PEN"))

    # Agrupa por data de entrega do documento usando uma lista para manter consistência no retorno (tupla)
    grouped = company_df.group_by(["DT_FIM_EXERC"])
    
    records = []
    
    for dt_fim, group_data in grouped:
        # Pega a string de data (dependendo da versao do polars pode ser string direto ou tupla)
        dt_fim_str = dt_fim[0] if isinstance(dt_fim, tuple) else dt_fim
        
        # Filtra as contas contábeis mais importantes para resumir
        # 1 = Ativo Total, 2 = Passivo Total, 3.01 = Receita, 3.11 = Lucro Líquido
        key_accounts = group_data.filter(
            pl.col("CD_CONTA").is_in(["1", "2", "3.01", "3.11"])
        )
        
        # Constrói o conteúdo textual
        content_lines = [f"Resumo Financeiro ({doc_type}) - Ticker: {ticker} - Data: {dt_fim_str}"]
        
        for row in key_accounts.iter_rows(named=True):
            conta_nome = row["DS_CONTA"]
            valor = row["VL_CONTA"]
            content_lines.append(f"- {conta_nome}: R$ {valor} mil")
        
        content = "\\n".join(content_lines)
        
        # Adiciona aos registros seguindo a estrutura do pipeline do FinMem
        records.append({
            "ticker": ticker,
            "cik": str(cvm_code),
            "est_timestamp": datetime.strptime(dt_fim_str, "%Y-%m-%d"),
            "document_url": f"cvm_dados_abertos_{doc_type}_{dt_fim_str}",
            "content": content,
            "type": doc_type
        })
        
    return pl.DataFrame(records)

if __name__ == "__main__":
    target_tickers = ["PETR4", "VALE3"]
    
    all_records = []
    
    for doc_type in ["ITR", "DFP"]:
        for year in YEARS:
            print(f"Buscando dados de {doc_type} para o ano {year}...")
            raw_data = download_and_extract_cvm(year, doc_type)
            
            if raw_data.is_empty():
                continue
                
            for ticker in target_tickers:
                if ticker in TICKER_TO_CVM:
                    cvm_code = TICKER_TO_CVM[ticker]
                    processed_df = process_company_data(raw_data, cvm_code, ticker, doc_type)
                    if not processed_df.is_empty():
                        all_records.append(processed_df)

    if all_records:
        final_df = pl.concat(all_records)
        # Ordena por data
        final_df = final_df.sort("est_timestamp", descending=True)
        
        output_path = os.path.join("data", "03_primary", "filing_data_br.parquet")
        final_df.write_parquet(output_path)
        print(f"Sucesso! Dados salvos em {output_path}")
    else:
        print("Nenhum dado encontrado.")

    logger.info("Program ends")
