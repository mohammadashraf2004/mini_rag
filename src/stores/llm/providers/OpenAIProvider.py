from ..LLMinterface import LLMInterface
from openai import OpenAI
from ..LLMEnums import LLMEnums,OpenAIEnums
import logging

class OpenAIProvider(LLMInterface):

    def __init__(self, api_key: str,api_url: str = None,
                 default_input_max_characters: int = 1000,
                   default_generation_max_output_tokens: int = 1000,
                   default_generation_temperature: float = 0.1):
        
        self.api_key = api_key
        self.api_url = api_url

        self.client = OpenAI(api_key=self.api_key,
                            base_url=self.api_url if api_url and len(api_url.strip()) else None)
        
        self.generation_model = None
        self.embedding_model = None
        self.embedding_size = None

        self.default_input_max_characters = default_input_max_characters
        self.default_generation_max_output_tokens = default_generation_max_output_tokens
        self.default_generation_temperature = default_generation_temperature

        self.logger = logging.getLogger(__name__)

        self.enums = OpenAIEnums

    def set_generation_model(self, model_id: str):
        self.generation_model = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int):
        self.embedding_model = model_id
        self.embedding_size = embedding_size 

    def generate_response(self, prompt: str,chat_history: list, max_output_tokens: int = None,
                          temperature: float = None):
        if not self.client:
            self.logger.error("OpenAI client not initialized.")
        
        if not self.generation_model:
            self.logger.error("Generation model not set. Using default model.")

        max_output_tokens = max_output_tokens if max_output_tokens is not None else self.default_generation_max_output_tokens
        temperature = temperature if temperature is not None else self.default_generation_temperature

        chat_history.append(self.construct_prompt(prompt = prompt,
                                                  role = OpenAIEnums.USER.value))
        
        response = self.client.chat.completions.create(
            model=self.generation_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_output_tokens,
            temperature=temperature
        )
        if not response.choices or len(response.choices) == 0 or not response.choices[0].message or not response.choices[0].message.content:
            self.logger.error(f"Invalid response from OpenAI API")
            return None

        return response.choices[0].message.content.strip()

    def embed_text(self, text: str, document_type: str = None):
        if not self.client:
            self.logger.error("OpenAI client not initialized.")
            return None
        
        if not self.embedding_model:
            self.logger.error("Embedding model not set. Cannot generate embedding.")
            return None
                
        
        response = self.client.embeddings.create(
            input=text,
            model=self.embedding_model
        )
        if not response.data or len(response.data) == 0 or not response.data[0].embedding:
            self.logger.error(f"Invalid response from OpenAI API: {response}")
            return None
        
        return response.data[0].embedding
    
    def process_text(self, text: str):
        return text[:self.default_input_max_characters].strip()

    def construct_prompt(self, prompt: str, role: str):
        return {
            "role": role,
            "content": prompt
        }