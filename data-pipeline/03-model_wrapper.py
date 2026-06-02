from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_fixed
import httpx

MAX_ATTEMPTS = 5
WAIT_TIME = 10

class Model_Wrapper(ABC):
    @retry(stop=stop_after_attempt(MAX_ATTEMPTS), wait=wait_fixed(WAIT_TIME))
    def summarize(self, text, summary_token_size = 200):
        return self._summarize(text, summary_token_size)
    
    @abstractmethod
    def _summarize(self, text, summary_token_size):
        pass

class Gemini(Model_Wrapper):
    def __init__(self, key, model_name):
        self.__key = key
        self.model_name = model_name
        self.httpx_client = httpx.Client()
    
    def _summarize(self, text, summary_token_size):
        prompt = f"Summarize the following news within {summary_token_size} tokens:\n{text}\nSummary:"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": summary_token_size}
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.__key}"
        response = self.httpx_client.post(url, headers=headers, json=payload, timeout=60.0)
        
        # Handle 429 Too Many Requests (or 500) so Tenacity will retry
        if response.status_code != 200:
            print(f"Gemini API Error {response.status_code}: {response.text}")
            response.raise_for_status()
            
        result = response.json()
        try:
            summary = result['candidates'][0]['content']['parts'][0]['text']
            return summary
        except KeyError:
            print("Gemini response parsing error:", result)
            raise Exception("Parsing Error")
    
class Dummy(Model_Wrapper):
    '''
    For test only
    '''
    import random
    import time
    def __init__(self, *args, **kwargs) -> None:
        print("Initializing a dummy model!")
    
    def _summarize(self, text, summary_token_size):
        self.time.sleep(self.random.randint(1, 5))
        if self.random.random() < 0.1:
            print("attempt", summary_token_size)
            raise Exception("Dummy Error")
        else:
            return text[:summary_token_size]
    
class Model_Factory:
    registered_model_class = ("gemini", 'dummy')
    @classmethod
    def create_model(cls, model_class:str, key:str = None, model_name:str = None, *args, **kwargs):
        assert model_class in cls.registered_model_class, f"Invalid model class name: choose one from {cls.registered_model_class}"
        match model_class:
            case "gemini":
                return Gemini(key, model_name)
            case "dummy":
                return Dummy()
            case _:
                raise