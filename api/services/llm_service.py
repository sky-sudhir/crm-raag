import os
import logging
from typing import List, Tuple
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from api.models.vector_doc import VectorDoc as VectorDocument

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model: str = "openai"):
        self._model = model
        self._llm = None
        
    @property
    def model(self):
        return self._model
        
    @model.setter
    def model(self, value):
        if self._model != value:
            self._model = value
            self._llm = None  # Reset cached LLM when model changes
    
    @property
    def llm(self):
        if self._llm is None:
            if self._model == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OpenAI API key is required")
                self._llm = ChatOpenAI(
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    openai_api_key=api_key
                )
            elif self._model == "google":
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("Google API key is required")
                self._llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-pro",
                    temperature=0.7,
                    google_api_key=api_key
                )
            else:
                raise ValueError(f"Unsupported model: {self._model}")
        return self._llm
    
    async def generate_response(
        self, 
        query: str, 
        search_results: List[Tuple[VectorDocument, float]]
    ) -> str:
        """Generate a response using the LLM based on retrieved documents."""
        try:
            if not search_results:
                return "I couldn't find any relevant information to answer your question."
            
            # Prepare context from search results
            context = "\n\n".join([
                f"Document {i+1} (relevance: {score:.3f}):\n{doc.chunk_text}"
                for i, (doc, score) in enumerate(search_results)
            ])
            
            # Create system prompt
            system_prompt = f"""You are a helpful assistant that answers questions based on the provided context. 
            Use only the information from the context to answer the question. If the context doesn't contain 
            enough information to answer the question, say so.

            Context:
            {context}

            Question: {query}

            Answer:"""
            
            # Generate response
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return f"Sorry, I encountered an error while generating a response: {str(e)}"
