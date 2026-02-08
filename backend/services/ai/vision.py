import json
from google.genai import types
from backend.services.ai.core import get_runner, run_agent, extract_text_from_content

async def analyze_body_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    prompt = """
    You are an expert fitness coach. Analyze this body photo to estimate a high-level body category and key metrics.
    Category Definitions:
    - Lean: Clearly visible muscle definition, low body fat.
    - Average: Moderate body fat, some muscle definition, healthy appearance.
    - Overfat: Higher body fat percentage, limited muscle visibility.
    
    Output JSON with:
    - 'category' (Lean|Average|Overfat)
    - 'reasoning' (1-liner assessment of current physique and posture)
    - 'estimated_body_fat' (numeric percentage, e.g., 18)
    - 'estimated_muscle_mass' (numeric percentage, e.g., 42)
    - 'body_type_description' (e.g., 'Athletic', 'Soft', 'Muscular')
    - 'potential_bodies': List of 3 objects, each containing:
        - 'type': Short Title (e.g., 'Lean & Toned', 'Powerlifter', 'Marathon Runner')
        - 'goal_key': MUST be one of ['lean', 'athletic', 'muscle']. Use 'lean' for the slimmest/most toned option, 'athletic' for the balanced/fit option, and 'muscle' for the biggest/strongest option.
        - 'visual_prompt': A detailed visual description of this target physique for an image generator (e.g., "A lean and toned physique with visible abs..."). This will be used internally.

    Do NOT provide medical advice. These are visual estimates only.
    """
    
    runner = get_runner(
        model_name="gemini-2.0-flash",
        config=types.GenerateContentConfig(response_mime_type="application/json")
    )
    
    parts = [
        types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_bytes)),
        types.Part(text=prompt)
    ]
    
    try:
        result_content = await run_agent(runner, parts)
        text_response = extract_text_from_content(result_content)
        return json.loads(text_response)
    except Exception as e:
        return {"category": "Unknown", "reasoning": f"Failed to parse AI response: {str(e)}"}
