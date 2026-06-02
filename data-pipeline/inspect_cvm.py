import polars as pl
import httpx
import zipfile
import io

url = 'https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_2023.zip'
r = httpx.get(url, timeout=60.0)
z = zipfile.ZipFile(io.BytesIO(r.content))

# Lendo o CSV e tratando erros de codificacao na leitura
df = pl.read_csv(z.open('dfp_cia_aberta_DRE_con_2023.csv').read(), separator=';', encoding='latin1')

print("Colunas encontradas:")
print(df.columns)

# Lendo o CSV BPA
df_bpa = pl.read_csv(z.open('dfp_cia_aberta_BPA_con_2023.csv').read(), separator=';', encoding='latin1')
p_bpa = df_bpa.filter(pl.col('CD_CVM') == 9512).filter(~pl.col("ORDEM_EXERC").str.starts_with("PEN"))
print("BPA Contas:")
print(p_bpa.select(["CD_CONTA", "DS_CONTA", "VL_CONTA"]).head(10))

# Lendo o CSV DRE
df_dre = pl.read_csv(z.open('dfp_cia_aberta_DRE_con_2023.csv').read(), separator=';', encoding='latin1')
p_dre = df_dre.filter(pl.col('CD_CVM') == 9512).filter(~pl.col("ORDEM_EXERC").str.starts_with("PEN"))
print("DRE Contas:")
print(p_dre.select(["CD_CONTA", "DS_CONTA", "VL_CONTA"]).head(10))
