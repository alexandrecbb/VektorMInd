import pickle
import sys
from pprint import pprint

def view_pickle(file_path):
    try:
        with open(file_path, "rb") as f:
            data = pickle.load(f)
            
            print(f"=== Visualizando: {file_path} ===")
            print(f"Tipo do objeto: {type(data)}")
            print("-" * 40)
            
            # Se for um dicionário ou lista, usa pprint para formatar melhor
            if isinstance(data, (dict, list)):
                pprint(data)
            # Se for um objeto customizado (como o MarketEnvironment)
            elif hasattr(data, '__dict__'):
                print("Atributos do Objeto:")
                pprint(vars(data))
            else:
                print(data)
                
    except Exception as e:
        print(f"Erro ao ler o arquivo pickle: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python view_pkl.py <caminho_para_o_arquivo.pkl>")
    else:
        view_pickle(sys.argv[1])
