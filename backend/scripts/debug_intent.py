
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.ai.agent import detect_intent_multi_agent

async def main():
    message = "Between 10 to 15 mins please"
    context = {
        "day_index": 1,
        "workout_title": "Full Body HIIT",
        "current_duration_mins": 30,
        "current_focus": ["HIIT", "Cardio"]
    }
    
    print(f"Testing message: '{message}'")
    result = await detect_intent_multi_agent(message, context)
    print(f"Result: {result}")
    
    if result.get("intent") == "ADJUST_WORKOUT":
        print("✅ SUCCESS: Correctly classified as ADJUST_WORKOUT")
    else:
        print(f"❌ FAILURE: Classified as {result.get('intent')}")

if __name__ == "__main__":
    asyncio.run(main())
