import os
import uuid
import base64
import json
import asyncio
from typing import Optional, Dict, Any, List

from google import genai
from google.genai import types
from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.models import Gemini
from google.adk.sessions import InMemorySessionService
from backend.core.config import settings

# Opik Integration
import opik
from opik.integrations.adk import OpikTracer, track_adk_agent_recursive

# Configure Opik (assumes OPIK_API_KEY is set in environment or local setup)
opik.configure(use_local=False)

# Ensure API key is set for ADK/GenAI
if settings.GOOGLE_API_KEY:
    os.environ["GOOGLE_API_KEY"] = settings.GOOGLE_API_KEY

async def check_ai_connection() -> Dict[str, Any]:
    status = {
        "initialized": False,
        "api_key_present": False,
        "connectivity": "unknown",
        "error": None
    }
    
    if not settings.GOOGLE_API_KEY:
        status["error"] = "GOOGLE_API_KEY not found in environment variables"
        return status
        
    status["api_key_present"] = True
    
    try:
        # Configure Opik tracer for test
        opik_tracer = OpikTracer(
            name="test_agent",
            tags=["health-check"],
            metadata={
                "environment": "development",
                "model": "gemini-2.0-flash",
                "framework": "google-adk",
            },
            project_name="fitness_coach"
        )

        # Use a simple agent to test connection
        agent = Agent(
            name="test_agent", 
            model=Gemini(model="gemini-2.0-flash"),
        )
        
        # Add Opik callbacks
        track_adk_agent_recursive(agent, opik_tracer)
        
        session_service = InMemorySessionService()
        runner = Runner(
            agent=agent,
            app_name="fitness_coach_app",
            session_service=session_service
        )
        
        # Create session explicitly
        await session_service.create_session(
            app_name="fitness_coach_app",
            user_id="test",
            session_id="test"
        )
    
        # Run a minimal prompt
        content = types.Content(role="user", parts=[types.Part(text="Hello")])
        # We just need to ensure no exception is raised
        # Consume async generator
        async for _ in runner.run_async(user_id="test", session_id="test", new_message=content):
            pass
        
        status["initialized"] = True
        status["connectivity"] = "connected"
        status["details"] = "Successfully connected via Google ADK."
        
    except Exception as e:
        status["connectivity"] = "failed"
        status["error"] = str(e)
        
    return status

def get_runner(model_name: str, instruction: str = "", config: types.GenerateContentConfig = None, tracer_name: str = "fitness_coach_agent") -> Runner:
    if not settings.GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set")
    
    # Configure Opik tracer
    opik_tracer = OpikTracer(
        name=tracer_name,
        tags=["ai-service"],
        metadata={
            "environment": "development",
            "model": model_name,
            "framework": "google-adk",
        },
        project_name="fitness_coach"
    )

    model = Gemini(model=model_name)
    agent = Agent(
        name="fitness_coach_agent",
        model=model,
        instruction=instruction,
        generate_content_config=config,
    )
    
    # Add Opik callbacks
    track_adk_agent_recursive(agent, opik_tracer)
    
    return Runner(
        agent=agent,
        app_name="fitness_coach_app",
        session_service=InMemorySessionService()
    )

async def run_agent(runner: Runner, parts: list, max_retries: int = 3) -> types.Content:
    content = types.Content(role="user", parts=parts)
    
    final_content = None
    delay = 2  # Start with 2s delay
    
    for attempt in range(max_retries + 1):
        # Generate fresh session for each attempt to avoid history pollution (e.g. duplicating user messages on retry)
        uid = str(uuid.uuid4())[:8]
        sid = str(uuid.uuid4())[:8]
        # Ensure session exists
        await runner.session_service.create_session(app_name="fitness_coach_app", user_id=uid, session_id=sid)
        
        try:
            async for event in runner.run_async(user_id=uid, session_id=sid, new_message=content):
                if event.content:
                    final_content = event.content
            return final_content
            
        except Exception as e:
            error_msg = str(e)
            if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg) and attempt < max_retries:
                print(f"  [429 Error] Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                # If it's not a 429 or we've exhausted retries, re-raise
                raise e
                
    return final_content

def extract_text_from_content(content: types.Content) -> str:
    if not content or not content.parts:
        return ""
    text = ""
    for part in content.parts:
        if part.text:
            text += part.text
    return text

def decode_inline_data(data: object) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return base64.b64decode(data)
    raise ValueError("Unsupported inline data format from model response")

def extract_image_from_content(content: types.Content) -> bytes:
    if not content or not content.parts:
        raise ValueError("Model returned no content")
        
    for part in content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and getattr(inline, "data", None):
            return decode_inline_data(inline.data)
            
    raise ValueError("Model returned no image data")
