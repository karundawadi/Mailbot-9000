from configparser import ConfigParser
from llm.ollamallm.available_models import AvailableModels
from requests import post
from json import dumps
from prompt.prompt import Prompt

class LLM:
    def __init__(self, config: ConfigParser, model_name: AvailableModels = AvailableModels.GEMMA_3_N):
        self.model_name: str = model_name.value
        self.ollama_url: str = config["OLLAMA"]["ollama_base_url"]
        self.think: bool = config.getboolean("OLLAMA", "think", fallback=False)
        self.stream: bool = config.getboolean("OLLAMA", "stream", fallback=False)
        self.keep_alive: int = config.getint("OLLAMA", "keep_alive", fallback=1)  # minutes
        self.headers: dict[str, str] = {
            "Content-Type": "application/json"
        }
        self.__setup()

    # Warms the LLM and performs a basic setup check by sending a test prompt.
    def __setup(self) -> None:
        try:
            self.__call_ollama_api("Hello, how are you?")
        except Exception as e:
            raise Exception(f"Failed to setup Ollama LLM: {e}")

    # Ref: https://github.com/ollama/ollama/blob/main/docs/api.md
    def __call_ollama_api(self, prompt: str) -> str:
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "think": self.think,
            "stream": self.stream,
            "keep_alive": self.keep_alive,
            "temperature": 0.3,
            "stop": ["</answer>"]
        }

        response = post(
            f"{self.ollama_url}/generate",
            headers=self.headers,
            data=dumps(data)
        )

        if response.status_code != 200:
            raise Exception(f"Error calling Ollama API: {response.text}")

        return response.json().get("response", "")

    def generate(self, prompt: Prompt) -> dict:
        response = self.__call_ollama_api(prompt.get_prompt())
        return prompt.extract_response(response)