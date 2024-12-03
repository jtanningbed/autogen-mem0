"""Test Neo4j connection with read and write operations."""
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("neo4j")

def write_transaction(tx, name):
    """Execute write operation in transaction."""
    result = tx.run(
        "CREATE (n:TestNode {name: $name, timestamp: timestamp()}) "
        "RETURN n.name as name",
        name=name
    )
    record = result.single()
    return record["name"] if record else None

def read_transaction(tx, name):
    """Execute read operation in transaction."""
    result = tx.run(
        "MATCH (n:TestNode {name: $name}) "
        "RETURN n.name as name, n.timestamp as timestamp",
        name=name
    )
    record = result.single()
    return dict(record) if record else None

def update_transaction(tx, name):
    """Execute update operation in transaction."""
    result = tx.run(
        "MATCH (n:TestNode {name: $name}) "
        "SET n.updated = true "
        "RETURN n.name as name, n.updated as updated",
        name=name
    )
    record = result.single()
    return dict(record) if record else None

def delete_transaction(tx, name):
    """Execute delete operation in transaction."""
    result = tx.run(
        "MATCH (n:TestNode {name: $name}) "
        "DELETE n "
        "RETURN count(*) as deleted",
        name=name
    )
    record = result.single()
    return record["deleted"] if record else 0

def test_connection():
    """Test Neo4j connection with read and write operations."""
    load_dotenv()
    
    uri = os.getenv("NEO4J_URL")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    
    print(f"\nTesting connection to {uri}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        
        # Test 1: Basic Read
        print("\n1. Testing basic read operation...")
        with driver.session() as session:
            result = session.run("RETURN 1 as num")
            value = result.single()["num"]
            print(f"Read successful! Test query returned: {value}")
            
        # Test 2: Write Operation - Create a test node
        print("\n2. Testing write operation - creating a node...")
        with driver.session() as session:
            node_name = session.execute_write(write_transaction, "test_node")
            print(f"Write successful! Created node with name: {node_name}")
            
        # Test 3: Read Created Node
        print("\n3. Testing read of created node...")
        with driver.session() as session:
            node = session.execute_read(read_transaction, "test_node")
            print(f"Read successful! Found node: {node}")
            
        # Test 4: Update Operation
        print("\n4. Testing update operation...")
        with driver.session() as session:
            node = session.execute_write(update_transaction, "test_node")
            print(f"Update successful! Node updated: {node}")
            
        # Optional: Cleanup - Delete test node
        print("\n5. Cleaning up - deleting test node...")
        with driver.session() as session:
            deleted = session.execute_write(delete_transaction, "test_node")
            print(f"Cleanup successful! Deleted {deleted} node(s)")
            
    except Exception as e:
        print(f"\nConnection/operation failed with error: {str(e)}")
    finally:
        driver.close()

if __name__ == "__main__":
    test_connection()
