from enum import Enum

# You can run ollama list
class AvailableModels(Enum):
    DEEPSEEK_R1_1_5_B = "deepseek-r1:1.5b"
    DEEPSEEK_R1_LATEST = "deepseek-r1:latest"
    DEEPSEEK_R1_8_B = "deepseek-r1:8b"
    DEEPSEEK_R1_14_B = "deepseek-r1:14b"
    DEEPSEEK_R1_32_B = "deepseek-r1:32b"
    GEMMA_3_1_B = "gemma3:1b"
    GEMMA_3_4_B = "gemma3n:e4b"
    GEMMA_3_N = "gemma3n:latest"
    LLAMA_INSTRUCT = "llama3:instruct"
    GPT_OSS = "gpt-oss:20b"
    MISTRAL_SMALL = "mistral-small3.2:latest"