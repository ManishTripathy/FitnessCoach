
import asyncio
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.ai.planning import generate_weekly_plan_rag

async def main():
    print("Generating plan for 'Build muscle and strength'...")
    try:
        plan = await generate_weekly_plan_rag("Build muscle and strength")
        print("\n--- Plan Generated ---")
        print(json.dumps(plan, indent=2))
        
        # Check for non-RAG data
        print("\n--- Verification ---")
        schedule = plan.get("schedule", [])
        for day in schedule:
            details = day.get("workout_details", {})
            url = details.get("url")
            thumbnail = details.get("thumbnail")
            title = details.get("title")
            
            print(f"Day {day.get('day')}: {title}")
            print(f"  URL: {url}")
            print(f"  Thumbnail: {thumbnail}")
            
            if url and "example.com" in url:
                print("  [ERROR] Found example.com URL!")
            if not url and not day.get("is_rest"):
                print("  [WARNING] No URL for non-rest day!")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
