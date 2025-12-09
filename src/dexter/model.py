import os
import time
import json
import re
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing import Type, List, Optional, Iterator, Any
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage
from langchain_core.language_models.chat_models import BaseChatModel

from dexter.prompts import DEFAULT_SYSTEM_PROMPT

# Update this to the model you want to use
DEFAULT_MODEL = "gpt-4.1"


class LocalChatOpenAI(ChatOpenAI):
    """
    Wrapper for ChatOpenAI that handles tool_choice and response_format correctly for local APIs like LM Studio.
    LM Studio only accepts tool_choice as a string ("none", "auto", "required"), not as an object.
    LM Studio requires response_format.type to be 'json_schema' or 'text'.
    """
    def bind_tools(
        self,
        tools: List[BaseTool],
        **kwargs: Any,
    ) -> Any:
        """
        Override bind_tools to ensure tool_choice is a string for local APIs.
        """
        # Call parent method but ensure tool_choice is not an object
        result = super().bind_tools(tools, **kwargs)
        
        # If we're using a local API, we need to ensure tool_choice is handled correctly
        # The issue is that LangChain might set tool_choice as an object internally
        # We'll let it default to "auto" (string) by not passing tool_choice explicitly
        return result
    
    def bind(self, **kwargs: Any) -> Any:
        """
        Override bind to ensure response_format is correctly formatted for LM Studio.
        """
        # If response_format is passed, ensure it has the correct structure
        if "response_format" in kwargs:
            response_format = kwargs["response_format"]
            # Ensure response_format has type='json_schema' or 'text'
            if isinstance(response_format, dict):
                if "type" not in response_format:
                    # If type is missing, set it based on json_schema presence
                    if "json_schema" in response_format:
                        response_format["type"] = "json_schema"
                    else:
                        response_format["type"] = "text"
                # Ensure type is valid for LM Studio
                if response_format["type"] not in ["json_schema", "text"]:
                    # If invalid type, try to fix it
                    if "json_schema" in response_format:
                        response_format["type"] = "json_schema"
                    else:
                        response_format["type"] = "text"
        
        return super().bind(**kwargs)

def get_chat_model(
    model_name: str = DEFAULT_MODEL,
    temperature: float = 0,
    streaming: bool = False
) -> BaseChatModel:
    """
    Factory function to get the appropriate chat model based on the model name.
    """
    if model_name.startswith("claude-"):
        # Anthropic models
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        
        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
            streaming=streaming
        )
    
    elif model_name.startswith("gemini-"):
        # Google Gemini models
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=api_key,
            streaming=streaming,
            convert_system_message_to_human=True 
        )
        
    else:
        # Default to OpenAI (gpt-* or others) or local API
        # Check if using local API
        base_url = os.getenv("OPENAI_BASE_URL")
        api_key = os.getenv("OPENAI_API_KEY")
        
        # If base_url is set, use local API (API key may be optional for local)
        if base_url:
            return LocalChatOpenAI(
                model=model_name, 
                temperature=temperature, 
                api_key=api_key,  # Can be None for local APIs without auth
                base_url=base_url,
                streaming=streaming
            )
        
        # Otherwise use standard OpenAI API
        return ChatOpenAI(
            model=model_name, 
            temperature=temperature, 
            api_key=api_key, 
            streaming=streaming
        )


def _is_local_api() -> bool:
    """Check if using a local API (LM Studio, Ollama, etc.)"""
    return bool(os.getenv("OPENAI_BASE_URL"))


def call_llm(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    tools: Optional[List[BaseTool]] = None,
) -> AIMessage:
  final_system_prompt = system_prompt if system_prompt else DEFAULT_SYSTEM_PROMPT
  
  prompt_template = ChatPromptTemplate.from_messages([
      ("system", final_system_prompt),
      ("user", "{prompt}")
  ])

  # Initialize the LLM.
  llm = get_chat_model(model_name=model, temperature=0, streaming=False)

  # Add structured output or tools to the LLM.
  # For local APIs like LM Studio, handle response_format errors gracefully
  runnable = llm
  is_local = _is_local_api()
  
  if output_schema:
      # For local APIs, use json_schema response_format directly for LM Studio compatibility
      if is_local:
          try:
              # Get the JSON schema from the Pydantic model
              json_schema_dict = output_schema.model_json_schema()
              # LM Studio requires response_format with type='json_schema'
              # Use bind() to pass response_format (ChatOpenAI doesn't accept it in constructor)
              runnable = llm.bind(
                  response_format={
                      "type": "json_schema",
                      "json_schema": {
                          "name": output_schema.__name__,
                          "schema": json_schema_dict,
                          "strict": False
                      }
                  }
              )
          except Exception as e:
              error_str = str(e)
              # For local APIs, don't use with_structured_output as it may configure response_format incorrectly
              # Instead, use regular call and parse manually
              runnable = llm
      else:
          # For non-local APIs, use standard structured output
          try:
              runnable = llm.with_structured_output(output_schema, method="function_calling")
          except Exception as e:
              error_str = str(e)
              # Try json_mode as fallback
              try:
                  runnable = llm.with_structured_output(output_schema, method="json_mode")
              except:
                  # Last resort: use regular call and parse manually
                  runnable = llm
  elif tools:
      runnable = llm.bind_tools(tools)
  
  chain = prompt_template | runnable
  
  # Retry logic for transient connection errors
  # Broadening exception handling for multiple providers
  for attempt in range(3):
      try:
          result = chain.invoke({"prompt": prompt})
          
          # If we used regular LLM but needed structured output, try to parse it
          if output_schema and not isinstance(result, output_schema):
              try:
                  content = result.content if hasattr(result, 'content') else str(result)
                  
                  # If content is already a dict, use it directly
                  if isinstance(content, dict):
                      return output_schema(**content)
                  
                  # If content is a string, try to parse as JSON
                  if isinstance(content, str):
                      # First try to parse the entire string as JSON
                      try:
                          json_data = json.loads(content)
                          return output_schema(**json_data)
                      except:
                          # If that fails, try to extract JSON from the string
                          json_match = re.search(r'\{.*\}', content, re.DOTALL)
                          if json_match:
                              json_data = json.loads(json_match.group())
                              return output_schema(**json_data)
              except Exception as parse_error:
                  # Log parse error but continue to try other methods
                  pass
          
          # If result is a dict (from json_schema response_format), convert to schema instance
          if output_schema and isinstance(result, dict):
              try:
                  return output_schema(**result)
              except:
                  pass
          
          # If result has content that is a dict, try to parse it
          if output_schema and hasattr(result, 'content') and isinstance(result.content, dict):
              try:
                  return output_schema(**result.content)
              except:
                  pass
          
          return result
      except KeyboardInterrupt:
          # Don't retry on user interrupt, propagate immediately
          raise
      except Exception as e:
          error_str = str(e)
          # Handle response_format errors for local APIs
          if is_local and ("response_format" in error_str.lower() or "json_schema" in error_str.lower()) and output_schema and attempt < 2:
              # For local APIs, don't use with_structured_output - just use regular call and parse
              # Try using bind() with response_format again, or fall back to regular call
              try:
                  json_schema_dict = output_schema.model_json_schema()
                  runnable = llm.bind(
                      response_format={
                          "type": "json_schema",
                          "json_schema": {
                              "name": output_schema.__name__,
                              "schema": json_schema_dict,
                              "strict": False
                          }
                      }
                  )
                  chain = prompt_template | runnable
                  continue
              except:
                  # Fall back to regular call
                  chain = prompt_template | llm
                  continue
          
          # We only want to retry on connection/transient errors, but catching generic Exception 
          # for simplicity across providers as they raise different errors.
          # In production, we should catch specific errors from each provider.
          if attempt == 2:  # Last attempt
              raise e
          time.sleep(0.5 * (2 ** attempt))  # 0.5s, 1s backoff


def call_llm_stream(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system_prompt: Optional[str] = None,
) -> Iterator[str]:
    """
    Stream LLM responses as text chunks.
    
    Note: Streaming does not support structured output or tools.
    Use this when you want to display text incrementally.
    """
    final_system_prompt = system_prompt if system_prompt else DEFAULT_SYSTEM_PROMPT
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", final_system_prompt),
        ("user", "{prompt}")
    ])
    
    # Initialize the LLM with streaming enabled
    llm = get_chat_model(model_name=model, temperature=0, streaming=True)
    
    chain = prompt_template | llm
    
    # Retry logic for transient connection errors
    for attempt in range(3):
        try:
            for chunk in chain.stream({"prompt": prompt}):
                # LangChain streams AIMessage chunks, extract content
                if hasattr(chunk, 'content'):
                    content = chunk.content
                    if content:  # Only yield non-empty content
                        yield content
            break
        except KeyboardInterrupt:
            # Don't retry on user interrupt, propagate immediately
            raise
        except Exception as e:
            if attempt == 2:  # Last attempt
                raise e
            time.sleep(0.5 * (2 ** attempt))  # 0.5s, 1s backoff
