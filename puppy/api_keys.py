import os
import time

API_KEY = os.environ.get("GEMINI_API_KEY", "")

if not API_KEY:
    raise ValueError("Nenhuma chave GEMINI_API_KEY foi encontrada ou configurada no .env!")

def get_current_api_key():
    return API_KEY

def rotate_api_key():
    # Como agora usamos uma API paga, a rotação não é necessária.
    # Caso ocorra um rate limit (excesso de requisições por segundo), 
    # a função apenas aguarda 5 segundos e tenta novamente com a mesma chave.
    print(f"\n[SISTEMA] Rate limit atingido. Aguardando 5 segundos para tentar novamente...")
    time.sleep(5)
