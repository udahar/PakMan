"""
LLM Node - Large Language Model interactions.
"""

import logging
from typing import Optional

from toolcomposer.base_node import BaseNode
from toolcomposer.models import NodeConfig

try:
    from langchain_ollama import ChatOllama
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class LLMNode(BaseNode):
    """
    Node for interacting with LLM models via Ollama.

    Inputs:
        - prompt: The prompt to send to the LLM

    Outputs:
        - response: The LLM's response text
    """

    node_type = "llm"
    category = "llm"
    inputs = ["prompt"]
    outputs = ["response"]
    description = "Interact with LLM models via Ollama"

    def __init__(self, config: NodeConfig):
        super().__init__(config)
        self._llm: Optional[ChatOllama] = None

    def initialize(self) -> bool:
        """Initialize the LLM connection."""
        if not LANGCHAIN_AVAILABLE:
            self.logger.error("langchain_ollama not available")
            return False

        try:
            model = self.config.parameters.get("model", "qwen2.5:7b")
            base_url = self.config.parameters.get(
                "base_url", "http://127.0.0.1:11434"
            )
            temperature = self.config.parameters.get("temperature", 0.7)

            self._llm = ChatOllama(
                model=model,
                base_url=base_url,
                temperature=temperature,
            )

            self.logger.info(f"LLM initialized: {model}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            return False

    def process(self, inputs: dict) -> dict:
        """
        Send prompt to LLM and get response.

        Args:
            inputs: Dictionary containing 'prompt' key

        Returns:
            Dictionary with 'response' key
        """
        if not self._llm:
            if not self.initialize():
                return {"response": "Error: LLM not available"}

        prompt = inputs.get("prompt", "")

        # Add system prompt if configured
        system_prompt = self.config.parameters.get("system_prompt")
        if system_prompt:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        else:
            messages = [{"role": "user", "content": prompt}]

        try:
            response = self._llm.invoke(messages)
            return {"response": response.content}
        except Exception as e:
            self.logger.error(f"LLM invocation failed: {e}")
            return {"response": f"Error: {str(e)}"}
