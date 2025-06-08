import abc

class Prompt(abc.ABC):
    """
    Abstract base class for prompts
    """
    @abc.abstractmethod
    def _get_instruction(self) -> str:
        """
        Returns the instruction for the prompt.
        """
        pass

    @abc.abstractmethod
    def _get_few_shot_example(self) -> str:
        """
        Returns a few shot example for the prompt.
        """
        pass

    @abc.abstractmethod
    def _get_response_format(self) -> str:
        """
        Returns the response format for the prompt.
        """
        pass

    @abc.abstractmethod
    def get_prompt(self) -> str:
        """
        Returns the complete prompt string.
        """
        pass

    @abc.abstractmethod
    def extract_response(self, response: str) -> dict:
        """
        Extracts the response from the LLM output.
        """
        pass