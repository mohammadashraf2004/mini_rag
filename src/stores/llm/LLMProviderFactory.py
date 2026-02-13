from .LLMEnums import LLMEnums
from .providers import CohereProvider , OpenAIProvider

class LLMProviderFactory:
    
    def __init__(self,config: dict):
        self.config = config
        

    def create_provider(self, provider: str):
        provider_type = self.config.get("provider_type")

        if provider_type == LLMEnums.OPENAI.value:
            return OpenAIProvider(api_key=self.config.get("api_key"),
                                  api_url=self.config.get("api_url"),
                                  default_input_max_characters=self.config.get("default_input_max_characters", 1000),
                                  default_generation_max_outputs=self.config.get("default_generation_max_outputs", 1000),
                                  default_generation_temperature=self.config.get("default_generation_temperature", 0.1))
        
        elif provider_type == LLMEnums.COHERE.value:
            return CohereProvider(api_key=self.config.get("api_key"),
                                  default_input_max_characters=self.config.get("default_input_max_characters", 1000),
                                  default_generation_max_output_tokens=self.config.get("default_generation_max_output_tokens", 1000),
                                  default_generation_temperature=self.config.get("default_generation_temperature", 0.1))
        
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")