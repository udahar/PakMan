"""
Example Alfred Router Integration
Shows how to route tasks between Ollama and LoRA engines
"""

import os
# In actual implementation, you would import your Ollama client
# and the LoRA functions from inference_lora.py


# Pseudo-code for Alfred router
class AlfredRouter:
    def __init__(self):
        # Configuration
        self.base_model = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        self.lora_modules_dir = "./lora_modules"

        # Define which lanes use LoRA engine vs Ollama
        self.lora_lanes = {
            "coding",
            "sql",
            "seo",
            "pakman",
            "zolapress",
            "python",
            "javascript",
            "analysis",
            "reasoning",
        }

        # Cache for loaded models to avoid reloading
        self.loaded_models = {}  # lane -> (model, tokenizer)

        # Default Ollama model for general tasks
        self.ollama_default_model = "llama3:8b"  # Example

    def _get_lora_model(self, lane):
        """Get or load LoRA model for a lane"""
        if lane in self.loaded_models:
            return self.loaded_models[lane]

        adapter_path = os.path.join(self.lora_modules_dir, f"{lane}_lora")
        if not os.path.exists(adapter_path):
            raise ValueError(f"No LoRA adapter found for lane: {lane}")

        # Load the model (this would be done once per lane)
        from inference_lora import load_lora_engine

        model, tokenizer = load_lora_engine(
            self.base_model,
            adapter_path,
            use_8bit=True,  # Use 8-bit for small GPU
        )

        self.loaded_models[lane] = (model, tokenizer)
        return model, tokenizer

    def route_task(self, task_prompt, task_lane):
        """
        Route task to appropriate engine based on lane

        In actual Alfred implementation, this would be called by your
        harness/task dispatcher

        Args:
            task_prompt: The user's input/prompt
            task_lane: Category from your harness (coding, sql, seo, etc.)

        Returns:
            Generated response string
        """
        # Determine which engine to use
        if task_lane in self.lora_lanes:
            # Use LoRA engine for specialized lanes
            try:
                model, tokenizer = self._get_lora_model(task_lane)
                from inference_lora import generate_response

                response = generate_response(model, tokenizer, task_prompt)
                return f"[LoRA:{task_lane}] {response}"
            except Exception as e:
                # Fallback to Ollama if LoRA fails
                return self._call_ollama(task_prompt, task_lane, fallback=True)
        else:
            # Use Ollama engine for general/other lanes
            return self._call_ollama(task_prompt, task_lane)

    def _call_ollama(self, prompt, lane, fallback=False):
        """
        Placeholder for actual Ollama integration
        In real implementation, this would call your Ollama client
        """
        engine_type = "LoRA (fallback)" if fallback else "Ollama"
        return f"[{engine_type}:{lane}] [Ollama response would go here for: '{prompt}']"

    def clear_cache(self):
        """Clear loaded models to free VRAM"""
        self.loaded_models.clear()
        # In practice, you might also call torch.cuda.empty_cache()


# Example usage
if __name__ == "__main__":
    # Initialize router
    router = AlfredRouter()

    # Example tasks
    test_cases = [
        ("Write a Python function to check if a number is prime", "coding"),
        ("How do I optimize a SQL query with multiple joins?", "sql"),
        ("What are current SEO best practices for 2024?", "seo"),
        ("Tell me a joke about programming", "general"),  # Would use Ollama
        (
            "Explain the theory of relativity",
            "reasoning",
        ),  # Would use LoRA if available
    ]

    for prompt, lane in test_cases:
        print(f"\nTask: {prompt}")
        print(f"Lane: {lane}")
        try:
            response = router.route_task(prompt, lane)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {e}")
