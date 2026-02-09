import asyncio
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from backend.services.ai.agent import adjust_workout_multi_agent

async def main():
    # Test case 1: Adjust duration (under 15)
    print("\n--- Test Case 1: Under 15 mins ---")
    user_message_1 = "Legs and glutes workout under 15 minutes bodyweight"
    plan_1 = {
        "schedule": [
            {"day": 3, "activity": "Legs", "details": {"id": "current_id", "duration_mins": 45, "focus": ["Legs"]}},
        ]
    }
    result_1 = await adjust_workout_multi_agent(
        user_message_1,
        3,
        plan_1,
        {"intent": "ADJUST_WORKOUT"}
    )
    print(json.dumps(result_1, indent=2))

    # Test case 2: Adjust duration range (35-40)
    print("\n--- Test Case 2: Range 35-40 mins ---")
    user_message_2 = "how about one between 35-40 mins"
    plan_2 = {
        "schedule": [
            {"day": 5, "activity": "Back", "details": {"id": "current_id", "duration_mins": 26, "focus": ["Back"]}},
        ]
    }
    result_2 = await adjust_workout_multi_agent(
        user_message_2,
        5,
        plan_2,
        {"intent": "ADJUST_WORKOUT"}
    )
    print(json.dumps(result_2, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
