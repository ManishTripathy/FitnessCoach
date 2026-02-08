
import asyncio
import os
import sys
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from backend.services.ai.planning import retrieval_agent, search_workouts_tool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def test_retrieval_agent():
    print("Testing Retrieval Agent...")
    
    # Mock skeleton state
    mock_skeleton = {
        "weekly_goal": "Lose Weight",
        "days": [
            {"day": 1, "focus": "Legs", "search_query": "High intensity leg workout"},
            {"day": 2, "focus": "Rest", "search_query": "Rest"}
        ]
    }
    
    # We need to manually inject this into the session state or mock the previous agent's output.
    # Since ADK Runner manages state, we can try to use a Runner with just the retrieval agent,
    # but we need to prepopulate the session state 'skeleton'.
    
    runner = Runner(
        agent=retrieval_agent,
        app_name="test_app",
        session_service=InMemorySessionService()
    )
    
    user_id = "test_user"
    session_id = "test_session"
    
    await runner.session_service.create_session(
        app_name="test_app",
        user_id=user_id,
        session_id=session_id
    )
    
    # Pre-populate state
    session = await runner.session_service.get_session(app_name="test_app", session_id=session_id, user_id=user_id)
    session.state["skeleton"] = json.dumps(mock_skeleton)
    
    # Trigger the agent
    prompt = "Proceed with retrieval."
    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    print("Running agent...")
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        pass
        # print(event)

    # Check result
    session = await runner.session_service.get_session(app_name="test_app", session_id=session_id, user_id=user_id)
    result = session.state.get("retrieved_plan")
    
    print("\n--- Result ---")
    print(result)

if __name__ == "__main__":
    asyncio.run(test_retrieval_agent())
