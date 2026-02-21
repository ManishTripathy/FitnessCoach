
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.ai.agent import detect_intent_multi_agent

async def main():
    test_messages = [
        "Between 10 to 15 mins please",
        "Suggest a full body hiit workout",
        "Suggest a full body workout",
        "I feel tired and need some motivation",
    ]

    context = {
        "day_index": 1,
        "workout_title": "Full Body HIIT",
        "current_duration_mins": 30,
        "current_focus": ["HIIT", "Cardio"],
    }

    for message in test_messages:
        print(f"\nTesting message: '{message}'")
        result = await detect_intent_multi_agent(message, context)
        print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
