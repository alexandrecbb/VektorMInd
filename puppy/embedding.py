import os
import httpx
import numpy as np
from typing import List, Union

class OpenAILongerThanContextEmb:
    """
    Embedding function with Gemini as embedding backend.
    Maintains the original class name for compatibility with other files.
    """

    def __init__(
        self,
        openai_api_key: Union[str, None] = None,
        embedding_model: str = "text-embedding-004",
        chunk_size: int = 2000,
        verbose: bool = False,
    ) -> None:
        """
        Initializes the Embedding object.

        Args:
            openai_api_key (str): Unused, kept for backwards compatibility. Uses GEMINI_API_KEY from env.
            embedding_model (str, optional): The model to use for embedding. Defaults to "text-embedding-004".
            chunk_size (int, optional): The maximum number of tokens. Defaults to 2000.
            verbose (bool, optional): Whether to show progress bar during embedding. Defaults to False.

        Returns:
            None
        """
        self.model = embedding_model
        self.chunk_size = chunk_size

    def _emb(self, text: Union[List[str], str]) -> List[List[float]]:
        """
        Performs embedding on a list of text using Gemini API via HTTP.

        Args:
            text (List[str]): A list of text to be embedded.

        Returns:
            List[List[float]]: The embeddings of the input text as a list of lists of floats.
        """
        if isinstance(text, str):
            text = [text]
            
        embeddings = []
        headers = {"Content-Type": "application/json"}
        
        for t in text:
            # Simple chunking: 1 token ~ 4 chars for safety
            chunk_char_size = max(1, self.chunk_size * 4)
            chunked_text = [t[i:i + chunk_char_size] for i in range(0, len(t), chunk_char_size)] 
            
            chunk_embs = []
            for chunk in chunked_text:
                payload = {
                    "model": f"models/{self.model}",
                    "content": {
                        "parts": [{"text": chunk}]
                    }
                }
                
                while True:
                    from .api_keys import get_current_api_key, rotate_api_key
                    current_key = get_current_api_key()
                    end_point = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={current_key}"
                    
                    response = httpx.post(end_point, headers=headers, json=payload, timeout=60.0)
                    
                    if response.status_code == 429:
                        rotate_api_key()
                        continue
                        
                    try:
                        response.raise_for_status()
                    except httpx.HTTPStatusError as e:
                        print(f"Gemini API Embedding Error: {response.text}")
                        raise e
                    break
                    
                emb = response.json()["embedding"]["values"]
                chunk_embs.append(emb)
            
            # average chunks
            avg_emb = np.mean(chunk_embs, axis=0).tolist()
            embeddings.append(avg_emb)
            
        return embeddings

    def __call__(self, text: Union[List[str], str]) -> np.ndarray:
        """
        Performs embedding on a list of text.

        Args:
            text (List[str]): A list of text to be embedded.

        Returns:
            np.array: The embedding of the input text as a NumPy array.

        """
        return np.array(self._emb(text)).astype("float32")

    def get_embedding_dimension(self):
        """
        Returns the dimension of the embedding.

        Returns:
            int: The dimension of the embedding.

        Raises:
            NotImplementedError: Raised when the embedding dimension for the specified model is not implemented.

        """
        match self.model:
            case "text-embedding-ada-002":
                return 1536
            case "gemini-embedding-2":
                return 3072
            case _:
                raise NotImplementedError(
                    f"Embedding dimension for model {self.model} not implemented"
                )
