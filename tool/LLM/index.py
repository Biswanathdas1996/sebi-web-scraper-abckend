import os
import json
import aiohttp
import asyncio
from typing import Dict, List, Optional, Union, Literal, Callable
from dataclasses import dataclass
import re

# Type definitions
@dataclass
class ConversationTheme:
    title: str
    priority: str
    description: str
    talkingPoints: List[str]
    iconColor: str

@dataclass
class IndustryMetric:
    name: str
    icon: str
    clientValue: float
    industryAverage: float
    unit: str
    trend: str
    percentageAbove: float

# Model configuration
class PWCModels:
    CLAUDE = "bedrock.anthropic.claude-sonnet-4"
    GEMINI = "vertex_ai.gemini-2.0-flash"
    GPT4 = "azure.gpt-4o"

PWCModel = Literal["bedrock.anthropic.claude-sonnet-4", "vertex_ai.gemini-2.0-flash", "azure.gpt-4o"]

async def call_pwc_genai(model: str, prompt: str, options: Dict = None) -> Dict:
    """
    Make an API call to PwC GenAI service.
    
    It's crucial to manage API keys securely.
    DO NOT hardcode API keys in production code.
    Use environment variables or a secure configuration management system.
    For demonstration, a placeholder is used.
    """
    if options is None:
        options = {}
        
    api_key = "sk-SxXiWpNEB1MCA_yxD3eHiQ"
    url = "https://genai-sharedservice-americas.pwc.com/completions"
    
    headers = {
        "accept": "application/json",
        "API-Key": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    default_body = {
        "model": model,
        "prompt": prompt,
        "presence_penalty": 0,
        "seed": 25,
        "stop": None,
        "stream": False,
        "stream_options": None,
        "temperature": 1,
        "top_p": 1,
    }
    
    # Merge default body with any provided options, allowing overrides
    body = {**default_body, **options}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=body) as response:
                if not response.ok:
                    try:
                        error_data = await response.json()
                        error_message = error_data.get("message", "Unknown error")
                    except Exception:
                        # Handle cases where the response body isn't JSON
                        error_message = await response.text() or "Unknown error"
                        
                    raise Exception(f"HTTP error! status: {response.status}, message: {error_message}")
                
                data = await response.json()
                return data
        
    except Exception as error:
        print(f"Error making API call to PwC GenAI: {error}")
        raise error

async def generate_with_prompt(
    prompt: str,
    model: str = "bedrock.anthropic.claude-sonnet-4",
    temperature: float = 0.7,
    top_p: float = 1.0,
    **kwargs
) -> Dict:
    """
    Generic function to generate content using PWC GenAI with custom prompt.
    
    Args:
        prompt: The custom prompt to send to the AI model
        model: The AI model to use (can be any valid model string)
        temperature: Controls randomness (0.0 to 1.0)
        top_p: Controls nucleus sampling (0.0 to 1.0)
        **kwargs: Additional options for the API call
    
    Returns:
        Dict: Raw response from PWC GenAI
    """
    options = {
        "temperature": temperature,
        "top_p": top_p,
        **kwargs
    }
    
    response = await call_pwc_genai(model, prompt, options)
    return response

async def generate_with_custom_parser(
    prompt: str,
    parser_func: Callable = None,
    model: str = "bedrock.anthropic.claude-sonnet-4",
    temperature: float = 0.7,
    top_p: float = 1.0,
    **kwargs
):
    """
    Most generic function to generate content with custom prompt and parser.
    
    Args:
        prompt: The custom prompt to send to the AI model
        parser_func: Optional custom parser function to process the response
        model: The AI model to use (can be any valid model string)
        temperature: Controls randomness (0.0 to 1.0)
        top_p: Controls nucleus sampling (0.0 to 1.0)
        **kwargs: Additional options for the API call and parser function
    
    Returns:
        Raw response if no parser_func provided, otherwise parsed result
    """
    response = await generate_with_prompt(prompt, model, temperature, top_p, **kwargs)
    
    if parser_func is None:
        return response
    
    # Extract parser-specific kwargs if provided
    parser_kwargs = kwargs.get('parser_kwargs', {})
    return parser_func(response, **parser_kwargs)

def parse_json_response(response: Dict, key: str = None) -> Union[Dict, List]:
    """
    Generic JSON parser for PWC GenAI responses.
    
    Args:
        response: Raw response from PWC GenAI
        key: Optional key to extract from parsed JSON (e.g., 'themes', 'posts', 'metrics')
    
    Returns:
        Parsed JSON data or specific key value
    """
    try:
        # Extract content from various possible response structures
        content = (response.get("choices", [{}])[0].get("text") or 
                  response.get("choices", [{}])[0].get("message", {}).get("content") or
                  response.get("text") or
                  response.get("content") or
                  json.dumps(response))
        
        # Remove markdown code blocks if present
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # Additional cleaning for malformed JSON
        content = content.strip()
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        
        # Handle unterminated strings
        if not content.endswith("}"):
            last_complete_object = content.rfind("}")
            if last_complete_object > 0:
                content = content[:last_complete_object + 1]
        
        parsed = json.loads(content)
        
        if key:
            return parsed.get(key, [])
        return parsed
        
    except Exception as error:
        print(f"Failed to parse JSON response: {error}")
        raise Exception(f"Unable to parse PWC GenAI JSON response: {error}")

# Main exported functions
__all__ = [
    'call_pwc_genai',
    'generate_with_prompt',
    'generate_with_custom_parser',
    'parse_json_response',
    'PWCModels',
    'PWCModel',
    'ConversationTheme',
    'IndustryMetric'
]
