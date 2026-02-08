
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.ai.planning import search_workouts_tool

def test_search():
    print("Testing search_workouts_tool...")
    query = "full body hiit workout"
    
    # Check embedding generation directly
    from backend.services.ai.embedding import generate_text_embedding
    emb = generate_text_embedding(query)
    print(f"Generated embedding length: {len(emb)}")
    
    result = search_workouts_tool(query)
    print(f"Result for '{query}':")
    print(result)
    
    parsed = json.loads(result)
    if isinstance(parsed, dict) and "error" in parsed:
        print("Test FAILED with error:", parsed["error"])
    elif isinstance(parsed, list) and len(parsed) > 0:
        print(f"Test PASSED. Found {len(parsed)} workouts.")
        print(f"First workout title: {parsed[0].get('title')}")
    else:
        print("Test returned unexpected result (empty list or invalid format).")

if __name__ == "__main__":
    test_search()
