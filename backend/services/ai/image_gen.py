from google.genai import types
from backend.services.ai.core import get_runner, run_agent, extract_image_from_content

async def generate_future_physique(image_bytes: bytes, goal_key: str, mime_type: str = "image/jpeg") -> bytes:
    # Goal prompts map
    goals = {
        "lean": "a Lean & Toned physique. Target 8-10% body fat. Visible six-pack abs, defined oblique muscles, tight waist. No excess fat. The look of a calisthenics athlete or boxer. Sharp definition.",
        "athletic": "a Fit & Athletic physique. Broad shoulders, V-shaped torso, flat stomach with visible muscle tone. Well-developed chest and arms. The look of a competitive swimmer or decathlete. Healthy, capable, and strong, but not overly bulky.",
        "muscle": "a Muscular & Powerful physique. Significant natural muscle mass. Large chest, thick arms, and strong legs. Target 12-15% body fat (visible abs but not shredded). The look of a superhero actor or rugby player. Impressive size but realistic proportions."
    }
    
    goal_desc = goals.get(goal_key, "healthy physique")
    prompt = (
        f"Transform the person in the reference photo to have {goal_desc}. "
        "Maintain the person's face, skin tone, and head to preserve identity, but completely modify the body shape to match the target physique. "
        "Keep the same standing pose, framing, lighting, and background. "
        "Generate a photorealistic, high-quality, 8k image. Ensure the body looks natural and not cartoonish."
    )
    
    runner = get_runner(
        model_name="gemini-2.5-flash-image", # Using flash-exp which often supports generation in preview
        config=types.GenerateContentConfig(response_modalities=["IMAGE"])
    )
    
    parts = [
        types.Part(inline_data=types.Blob(mime_type=mime_type, data=image_bytes)),
        types.Part(text=prompt)
    ]
    
    result_content = await run_agent(runner, parts)
    return extract_image_from_content(result_content)
