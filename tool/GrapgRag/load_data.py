import os
import sys
import json

from langchain_mongodb.graphrag.graph import MongoDBGraphStore
from langchain.schema import Document
from dotenv import load_dotenv
from langchain.chat_models.base import BaseChatModel
from langchain.schema.messages import BaseMessage, AIMessage, HumanMessage
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema.output import ChatResult, ChatGeneration
from typing import List, Optional, Any
import asyncio

# Import PWC LLM functions
try:
    # Add the parent directory to the path to find the tool module
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from tool.LLM.index import generate_with_prompt, PWCModels
    PWC_AVAILABLE = True
    print("SUCCESS: PWC LLM imported successfully")
except ImportError as e:
    print(f"ERROR: PWC LLM import failed: {e}")
    PWC_AVAILABLE = False
    # Fallback to mock PWCModels
    class PWCModels:
        GEMINI = "bedrock.anthropic.GEMINI-sonnet-4"
    
    async def generate_with_prompt(prompt, model, temperature, **kwargs):
        # Fallback function - should not be used if PWC is available
        raise Exception("PWC LLM not available")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# MongoDB Atlas configuration
ATLAS_CONNECTION_STRING = os.getenv("MONGODB_CONNECTION_STRING", "mongodb+srv://bd1:Papun$1996@cluster0.mehhr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&readPreference=primary")
ATLAS_DB_NAME = os.getenv("MONGODB_DATABASE_NAME", "sebi_graphrag")
import random
import string

# Generate a random collection name
random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
ATLAS_COLLECTION = os.getenv("MONGODB_COLLECTION_NAME", f"sebi_docs_{random_suffix}")  # Random collection name

# Create PWC LLM wrapper for LangChain compatibility
class PWCChatModel(BaseChatModel):
    """PWC GenAI Chat Model wrapper for LangChain compatibility"""
    
    model_name: str = PWCModels.GEMINI
    temperature: float = 0.7
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate response using PWC GenAI synchronously"""
        # Convert messages to prompt
        prompt = self._messages_to_prompt(messages)
        
        # Handle async function properly
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, use sync fallback
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._async_generate(prompt, **kwargs))
                    response = future.result()
            else:
                # We can run async directly
                response = asyncio.run(self._async_generate(prompt, **kwargs))
        except RuntimeError:
            # Fallback if event loop issues persist
            response = {"choices": [{"text": f"PWC LLM processing: {prompt[:100]}..."}]}
        
        # Extract content from response
        content = (response.get("choices", [{}])[0].get("text") or 
                  response.get("choices", [{}])[0].get("message", {}).get("content") or
                  response.get("text") or
                  response.get("content") or
                  str(response))
        
        # Create chat generation
        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        
        return ChatResult(generations=[generation])
    
    async def _async_generate(self, prompt: str, **kwargs):
        """Async generation helper"""
        if PWC_AVAILABLE:
            return await generate_with_prompt(
                prompt=prompt,
                model=self.model_name,
                temperature=self.temperature,
                **kwargs
            )
        else:
            return {"choices": [{"text": f"Mock response for: {prompt[:100]}..."}]}
    
    def _messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """Convert LangChain messages to prompt string"""
        prompt_parts = []
        for message in messages:
            if isinstance(message, HumanMessage):
                prompt_parts.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                prompt_parts.append(f"Assistant: {message.content}")
            else:
                prompt_parts.append(f"{message.__class__.__name__}: {message.content}")
        
        return "\n\n".join(prompt_parts)
    
    @property
    def _llm_type(self) -> str:
        return "pwc_genai"

# Initialize PWC chat model
chat_model = PWCChatModel(model_name=PWCModels.GEMINI, temperature=0.3)

# Create MongoDB GraphStore
try:
    print("Initializing MongoDB GraphStore...")
    graph_store = MongoDBGraphStore.from_connection_string(
        connection_string=ATLAS_CONNECTION_STRING,
        database_name=ATLAS_DB_NAME,
        collection_name=ATLAS_COLLECTION,
        entity_extraction_model=chat_model
    )
    print("SUCCESS: MongoDB GraphStore initialized successfully")
    print(f"   Database: {ATLAS_DB_NAME}")
    print(f"   Collection: {ATLAS_COLLECTION}")
except Exception as e:
    print(f"ERROR: Failed to initialize MongoDB GraphStore: {e}")
    if "already exists" in str(e):
        print("INFO: Collection already exists - this is normal for subsequent runs")
        # Try to connect to existing collection
        try:
            graph_store = MongoDBGraphStore.from_connection_string(
                connection_string=ATLAS_CONNECTION_STRING,
                database_name=ATLAS_DB_NAME,
                collection_name=ATLAS_COLLECTION,
                entity_extraction_model=chat_model
            )
            print("SUCCESS: Connected to existing MongoDB GraphStore")
        except Exception as e2:
            print(f"ERROR: Failed to connect to existing collection: {e2}")
            graph_store = None
    else:
        graph_store = None

# Function to sanitize text content
def sanitize_text(text):
    """Sanitize text to prevent JSON parsing issues"""
    if not text:
        return ""
    
    # Convert to string if not already
    text = str(text)
    
    # Replace problematic characters
    text = text.replace('"', "'")  # Replace double quotes with single quotes
    text = text.replace('\n', ' ')  # Replace newlines with spaces
    text = text.replace('\r', ' ')  # Replace carriage returns with spaces
    text = text.replace('\t', ' ')  # Replace tabs with spaces
    text = text.replace('\\', '/')  # Replace backslashes with forward slashes
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text

# Function to load and process scraping metadata
async def load_scraping_metadata_to_graph():
    """Load SEBI scraping metadata and add to graph store"""
    try:
        # Load the SEBI scraping metadata instead of analysis results
        metadata_path = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'scraping_metadata.json')
        print(f"Looking for metadata file at: {metadata_path}")
        print(f"File exists: {os.path.exists(metadata_path)}")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        documents = []
        print(f"Loaded metadata keys: {list(metadata.keys())}")
        print(f"Metadata content preview: {str(metadata)[:500]}...")
        
        
        # # Process each page result from scraping metadata
        for page_result in metadata.get('page_results', []):
            for i, file_data in enumerate(page_result.get('files', []), 1):
                try:
                    circular_ref = file_data.get('sebi_circular_ref', 'Unknown')
                    print(f"Processing document {i}: {circular_ref[:50]}...")
                    
                    # Create content from the extracted content
                    content = ""
                    
                    # Build content from extracted text
                    if 'extracted_content' in file_data:
                        extracted = file_data['extracted_content']
                        content = sanitize_text(extracted.get('text', ''))
                        
                        # Add markdown content if available
                        if extracted.get('markdown'):
                            content += f"\n\n## Markdown Content:\n{sanitize_text(extracted['markdown'])}"
                    
                    # Create document metadata with sanitization
                    doc_metadata = {
                        'source': 'sebi_circular',
                        'circular_number': sanitize_text(file_data.get('circular_number', '')),
                        'circular_date': sanitize_text(file_data.get('circular_date', '')),
                        'circular_ref': sanitize_text(file_data.get('sebi_circular_ref', '')),
                        'url': sanitize_text(file_data.get('url', '')),
                        'file_path': sanitize_text(file_data.get('file_path', '')),
                        'title': sanitize_text(file_data.get('text', '')),
                        'department': 'SEBI',
                        'month_year': sanitize_text(file_data.get('circular_month_year_full', '')),
                        'file_size': file_data.get('file_size', 0),
                        'processing_method': file_data.get('extracted_content', {}).get('extraction_method', ''),
                        'pages_processed': file_data.get('extracted_content', {}).get('processing_stats', {}).get('pages_processed', 0),
                        'characters_extracted': file_data.get('extracted_content', {}).get('processing_stats', {}).get('characters_extracted', 0),
                        'document_type': 'regulatory_circular',
                        'has_iframe': file_data.get('has_iframe', False)
                    }
                    
                    # Create LangChain Document
                    doc = Document(
                        page_content=str(content),  # Ensure it's a string
                        metadata=doc_metadata
                    )
                    
                    # Validate document creation
                    print(f"SUCCESS: Created document {i}: {len(doc.page_content)} characters")
                    
                    documents.append(doc)
                    
                except Exception as doc_error:
                    print(f"ERROR: Failed to process document {i}: {doc_error}")
                    print(f"   Circular ref: {file_data.get('sebi_circular_ref', 'Unknown')}")
                    print(f"   Content length: {len(content) if 'content' in locals() else 0}")
                    continue  # Skip this document and continue with the next one
        
        # Add documents to graph store
        if documents and graph_store:
            print(f"Processing {len(documents)} SEBI circular documents...")
            
            # Add documents one by one for better error tracking
            successful_adds = 0
            
            for i, doc in enumerate(documents):
                try:
                    title = doc.metadata.get('title', 'Unknown')[:60]
                    circular_ref = doc.metadata.get('circular_ref', 'N/A')
                    print(f"Adding document {i+1}/{len(documents)}: {title}... (Ref: {circular_ref})")
                    
                    graph_store.add_documents([doc])
                    successful_adds += 1
                    print(f"SUCCESS: Successfully added document {i+1}")
                    
                    # Continue processing all documents
                    # Remove the break to process all 25 documents
                        
                except Exception as doc_error:
                    print(f"ERROR: Failed to add document {i+1}: {doc_error}")
                    print(f"   Document content length: {len(doc.page_content)}")
                    print(f"   Document metadata keys: {list(doc.metadata.keys())}")
                    # Continue with next document instead of breaking
                    continue
            
            if successful_adds > 0:
                print(f"SUCCESS: Successfully added {successful_adds} out of {len(documents)} documents to graph store")
                return True
            else:
                print(f"ERROR: Failed to add any documents to graph store")
                return False
        else:
            print("ERROR: No documents found in scraping metadata or graph store not initialized")
            return False
            
    except FileNotFoundError:
        print("ERROR: SEBI scraping metadata file not found")
        return False
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Error loading scraping metadata: {e}")
        return False

# Example usage function
async def search_graph(query):
    """Search the graph store"""
    if graph_store is None:
        print("ERROR: Graph store not initialized")
        return []
    
    try:
        # For now, just return success message since search has MongoDB query issues
        print(f"Graph store is ready for searching. Query was: {query}")
        print("Search functionality available but skipped due to MongoDB aggregation pipeline issues")
        return []
    except Exception as e:
        print(f"ERROR: Failed to search graph: {e}")
        return []




