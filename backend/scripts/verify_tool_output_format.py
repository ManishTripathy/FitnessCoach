
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.ai.planning import search_workouts_tool

def verify_tool():
    query = "High intensity leg workout"
    print(f"Calling search_workouts_tool with query: '{query}'")
    
    result_json = search_workouts_tool(query)
    
    print("\n--- Tool Output ---")
    print(result_json)
    
    try:
        data = json.loads(result_json)
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            print("\n--- Verification ---")
            print(f"Has ID: {'id' in first_item}")
            print(f"Has URL: {'url' in first_item}")
            print(f"Has Thumbnail: {'thumbnail' in first_item}")
            print(f"URL Value: {first_item.get('url')}")
            print(f"Thumbnail Value: {first_item.get('thumbnail')}")
        else:
            print("No data returned or error.")
    except Exception as e:
        print(f"JSON Parse Error: {e}")

if __name__ == "__main__":
    verify_tool()
