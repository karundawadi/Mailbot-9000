from enum import Enum

# You can run ollama list
class AvailableModels(Enum):
    DEEPSEEK_R1_1_5_B = "deepseek-r1:1.5b"
    DEEPSEEK_R1_7_B = "deepseek-r1:7b"
    GEMMA_3_1_B = "gemma3:1b"
    GEMMA_3_4_B = "gemma3:4b"
    DEEPSEEK_R1_8_B = "deepseek-r1:8b"
    GEMMA_3_N = "gemma3n:latest"