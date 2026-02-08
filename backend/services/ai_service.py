# Facade for AI services
# Refactored into granular services in backend/services/ai/

from backend.services.ai.core import check_ai_connection
from backend.services.ai.vision import analyze_body_image
from backend.services.ai.image_gen import generate_future_physique
from backend.services.ai.recommendation import recommend_fitness_path
from backend.services.ai.planning import generate_weekly_plan_rag
from backend.services.ai.embedding import generate_text_embedding
