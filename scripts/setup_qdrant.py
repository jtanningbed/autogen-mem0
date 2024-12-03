"""Script to set up Qdrant collections for memory."""

import os
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

from anthropic_autogen.core.config.manager import ConfigManager

def setup_qdrant_collection(
    collection_name: str,
    url: str = None,
    host: str = None,
    port: int = None,
    api_key: str = None,
    size: int = 1536,  # OpenAI's text-embedding-3-small dimension
):
    """Set up Qdrant collection with specified configuration.
    
    Args:
        collection_name: Name of collection to create
        url: Complete Qdrant URL (alternative to host/port)
        host: Qdrant host (if not using url)
        port: Qdrant port (if not using url)
        api_key: Qdrant API key
        size: Vector dimension size (default: 1536 for OpenAI embeddings)
    """
    # Initialize Qdrant client
    client_kwargs = {
        "api_key": api_key,
        "prefer_grpc": False,
        "timeout": 20.0
    }
    
    if url:
        client = QdrantClient(url=url, **client_kwargs)
    else:
        client = QdrantClient(host=host, port=port, **client_kwargs)
    
    try:
        # Create collection if it doesn't exist
        collections = client.get_collections().collections
        exists = any(collection.name == collection_name for collection in collections)
        
        if not exists:
            print(f"Creating collection: {collection_name}")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=size,
                    distance=models.Distance.COSINE,
                ),
            )
            print(f"Collection {collection_name} created successfully!")
        else:
            print(f"Collection {collection_name} already exists.")
            
    except Exception as e:
        print(f"Error connecting to Qdrant: {str(e)}")
        print("\nDebug information:")
        print(f"URL: {url if url else 'Not used'}")
        print(f"Host: {host if host else 'Not used'}")
        print(f"Port: {port if port else 'Not used'}")
        print(f"API Key present: {'Yes' if api_key else 'No'}")
        if api_key and api_key.startswith("${"):
            print("Warning: API key contains environment variable that wasn't substituted!")
        elif api_key:
            print(f"API Key value: {api_key[:8]}... (first 8 chars)")
        raise

def main():
    """Set up Qdrant collections for all environments."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Load configuration
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    config_manager = ConfigManager(config_path)
    
    # Get all environment configs
    for env_name, env_config in config_manager.config.environments.items():
        memory_config = env_config.memory
        
        # Only process environments with Qdrant vector store
        if (
            memory_config.get("vector_store", {}).get("provider") == "qdrant" and
            memory_config["vector_store"].get("config")
        ):
            vs_config = memory_config["vector_store"]["config"]
            print(f"\nSetting up Qdrant for environment: {env_name}")
            
            # Use configuration from config.yaml
            setup_qdrant_collection(
                collection_name=vs_config["collection_name"],
                url=vs_config.get("url"),
                host=vs_config.get("host"),
                port=vs_config.get("port"),
                api_key=vs_config.get("api_key"),
            )

if __name__ == "__main__":
    main()
