from llm.hugginfacellm.available_models import AvailableModels
from configparser import ConfigParser
from torch import cuda, device as torch_device, backends, bfloat16
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from loguru import logger

class LLM:
    def __init__(self, config: ConfigParser, model_name: AvailableModels = AvailableModels.GOOGLE_GEMMA_2_B_IT):
        self.model_name: str = model_name.value
        self.huggingface_token: str = config["HUGGINGFACE"]["token"]
        self.max_new_tokens: int = int(config["HUGGINGFACE"]["max_new_tokens"])
        self.device: torch_device = None
        self.auto_tokenizer: AutoTokenizer = None
        self.casual_llm_model: AutoModelForCausalLM = None
        self.generator: pipeline = None
    
    def __set_torch_device(self) -> None:
        if cuda.is_available():
            device = torch_device("cuda")
            logger.info(f"Using NVIDIA CUDA (GPU) for acceleration.")
        elif backends.mps.is_available():
            device = torch_device("mps")
            logger.info(f"Using Apple MPS (GPU) for acceleration.")
        else:
            device = torch_device("cpu")
            logger.info(f"Neither CUDA nor MPS (GPU) available. Falling back to CPU. Performance will be slower.")

        logger.info(f"Current device: {device}")
        self.device: torch_device  = device
    
    def __create_tokenizer(self) -> None:
        if not self.huggingface_token:
            raise ValueError("Hugging Face token is required to access the model.")
        self.auto_tokenizer: AutoTokenizer = AutoTokenizer.from_pretrained(self.model_name, token=self.huggingface_token)
    
    def __create_model(self) -> None:
        if not self.huggingface_token:
            raise ValueError("Hugging Face token is required to access the model.")
        if not self.device:
            raise ValueError("Torch device must be set before creating the model.")
        self.casual_llm_model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            token=self.huggingface_token,
            torch_dtype=bfloat16,
        ).to(self.device)
    
    def __create_generator(self) -> None:
        if not hasattr(self, 'casual_llm_model') or not hasattr(self, 'auto_tokenizer'):
            raise ValueError("Model and tokenizer must be created before creating the generator.")
        self.generator: pipeline = pipeline(
            "text-generation",
            model=self.casual_llm_model,
            tokenizer=self.auto_tokenizer,
            device=self.device.index if self.device.type != 'cpu' else -1,
            return_full_text=False,
        )

    def setup(self):
        try:
            self.__set_torch_device()
            self.__create_tokenizer()
            self.__create_model()
            self.__create_generator()
        except Exception as e:
            logger.info(f"Unable to setup llm package: {e}")
            raise

    def generate(self, prompt: str) -> str:
        if not hasattr(self, 'generator'):
            raise ValueError("Generator is not set up. Call setup() first.")
        output = self.generator(prompt, max_new_tokens=self.max_new_tokens)
        logger.info(output)
        return output[0]['generated_text'] if output else ""
    
    def tear_down(self):
        cuda.empty_cache()
        if hasattr(self, 'generator'):
            del self.generator
            self.generator = None
        if hasattr(self, 'casual_llm_model'):
            del self.casual_llm_model
            self.casual_llm_model = None
        if hasattr(self, 'auto_tokenizer'):
            del self.auto_tokenizer
            self.auto_tokenizer = None
        if hasattr(self, 'device'):
            del self.device
            self.device = None        
        logger.info("Garbage collection complete.")