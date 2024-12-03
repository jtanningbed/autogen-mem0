"""Test memory tools with Neo4j graph store."""
import asyncio
import os
from dotenv import load_dotenv
from mem0 import Memory
from mem0.configs.base import MemoryConfig
from mem0.graphs.configs import GraphStoreConfig
import logging
import json
from neo4j import GraphDatabase

# Configure logging with more verbose output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("neo4j")

def setup_neo4j_schema(uri, username, password):
    """Setup Neo4j schema for vector operations"""
    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    with driver.session() as session:
        # Clear existing data
        print("Clearing existing data...")
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create first node
        print("Creating Person node...")
        session.run("""
        CREATE (john:Person {
            name: 'john',
            user_id: 'test_user',
            embedding: [0.1, 0.2, 0.3]
        })
        """)
        
        # Create second node
        print("Creating Sport node...")
        session.run("""
        CREATE (tennis:Sport {
            name: 'tennis',
            user_id: 'test_user',
            embedding: [0.4, 0.5, 0.6]
        })
        """)
        
        # Create relationship
        print("Creating relationship...")
        session.run("""
        MATCH (john:Person {name: 'john'}), (tennis:Sport {name: 'tennis'})
        CREATE (john)-[:LIKES_PLAYING]->(tennis)
        """)
        
        # Verify nodes
        print("\nVerifying created nodes:")
        result = session.run("MATCH (n) RETURN n.name, n.user_id, n.embedding")
        for record in result:
            print(f"Node: {record}")
            
        # Verify relationships
        print("\nVerifying relationships:")
        result = session.run("""
        MATCH (n)-[r]->(m) 
        RETURN n.name, type(r), m.name
        """)
        for record in result:
            print(f"Relationship: {record}")
            
    driver.close()

def print_debug(title, data):
    """Helper to pretty print debug info"""
    print(f"\n=== {title} ===")
    print(json.dumps(data, indent=2, default=str))
    print("=" * (len(title) + 8))

async def test_memory_tools():
    """Test memory tools with Neo4j."""
    load_dotenv()
    
    # Debug: Print environment variables (excluding password)
    neo4j_config = {
        "url": os.getenv("NEO4J_URL"),
        "username": os.getenv("NEO4J_USERNAME"),
        "database": "neo4j"
    }
    print_debug("Neo4j Configuration", neo4j_config)
    
    # Setup Neo4j with test data
    setup_neo4j_schema(
        os.getenv("NEO4J_URL"),
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
    
    # Create memory config with Neo4j graph store
    config = MemoryConfig(
        graph_store=GraphStoreConfig(
            provider="neo4j",
            config={
                "url": os.getenv("NEO4J_URL"),
                "username": os.getenv("NEO4J_USERNAME"),
                "password": os.getenv("NEO4J_PASSWORD"),
                "database": "neo4j"
            }
        ),
        version="v1.1"
    )
    
    # Initialize memory instance
    memory = Memory(config=config)
    user_id = "test_user"
    memory.graph.user_id = user_id
    
    try:
        # Test 1: Query existing data
        print("\n1. Testing query of created data...")
        search_query = "John"
        print(f"Searching for: {search_query}")
        
        related = memory.graph.search(
            query=search_query,
            filters={"user_id": user_id}
        )
        print_debug("Search Results", related)
        
        # Test 2: Get all data
        print("\n2. Testing get all data...")
        all_data = memory.graph.get_all(filters={"user_id": user_id})
        print_debug("All Graph Data", all_data)
        
    except Exception as e:
        print(f"\nOperation failed with error: {str(e)}")
        import traceback
        print(f"Full traceback:\n{traceback.format_exc()}")
    finally:
        # Clean up
        try:
            memory.graph.delete_all(filters={"user_id": user_id})
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_memory_tools())
