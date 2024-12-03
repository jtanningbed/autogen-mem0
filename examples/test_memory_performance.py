"""Test memory performance with both vector and graph stores."""
import asyncio
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from mem0 import Memory
from mem0.configs.base import MemoryConfig
import logging
import json
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_debug(title: str, data: any, timing: float = None):
    """Helper to pretty print debug info with timing"""
    print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2, default=str))
    if timing:
        print(f"Time taken: {timing:.2f} seconds")
    print("=" * (len(title) + 8))

def generate_test_data(num_entries: int = 1000) -> List[Dict[str, str]]:
    """Generate test messages for memory operations."""
    messages = []
    for i in range(num_entries):
        # Create messages with relationships and facts
        if i % 3 == 0:
            content = f"User_{i} enjoys playing Tennis and Basketball. They practice twice a week."
        elif i % 3 == 1:
            content = f"User_{i} works at Company_{i//10} as a Software Engineer. They specialize in Python and JavaScript."
        else:
            content = f"User_{i} lives in City_{i//20} and frequently visits Restaurant_{i//5} for dinner."
        
        messages.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": content
        })
    return messages

async def test_memory_performance():
    """Test memory performance with both vector and graph stores."""
    load_dotenv()
    
    # Load configuration from config.yaml
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    
    # Initialize memory with both stores
    memory = Memory()  # This will use the config.yaml settings
    user_id = "perf_test_user"
    
    try:
        # Generate test data
        num_entries = 1000  # Adjust this for different scales
        messages = generate_test_data(num_entries)
        
        # Test 1: Measure memory building performance
        print(f"\nBuilding memory with {num_entries} entries...")
        start_time = time.time()
        
        # Add messages in batches
        batch_size = 10
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i+batch_size]
            try:
                result = memory.add(
                    messages=batch,
                    user_id=user_id,
                    agent_id="perf_test_agent"
                )
                if (i + batch_size) % 100 == 0:
                    print(f"Processed {i + batch_size} entries...")
            except Exception as e:
                print(f"Error adding batch {i//batch_size}: {str(e)}")
                continue
                
        build_time = time.time() - start_time
        print_debug("Memory Build Complete", {
            "entries": num_entries,
            "batch_size": batch_size
        }, build_time)
        
        # Test 2: Measure search performance
        print("\nTesting search performance...")
        search_queries = [
            "Tell me about tennis players",
            "Who are the software engineers?",
            "What restaurants do people visit?",
            "Find people in the same city",
            "List all companies"
        ]
        
        search_times = []
        for query in search_queries:
            start_time = time.time()
            try:
                results = memory.search(
                    query=query,
                    user_id=user_id,
                    limit=5
                )
                query_time = time.time() - start_time
                search_times.append(query_time)
                
                print_debug(f"Search Results for: {query}", 
                          results, query_time)
            except Exception as e:
                print(f"Search error for query '{query}': {str(e)}")
        
        # Print aggregate statistics
        print_debug("Search Performance Summary", {
            "avg_search_time": sum(search_times) / len(search_times),
            "min_search_time": min(search_times),
            "max_search_time": max(search_times),
            "total_queries": len(search_queries)
        })
        
    except Exception as e:
        print(f"\nOperation failed with error: {str(e)}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
    finally:
        # Clean up
        try:
            print("\nCleaning up test data...")
            memory.delete_all(user_id=user_id)
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_memory_performance())
