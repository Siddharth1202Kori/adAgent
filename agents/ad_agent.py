from pydantic import BaseModel, Field
from typing import List
from utils.llm import generate_structured_output, get_client, _extract_json, MAX_JSON_RETRIES
import json
import logging
from tenacity import retry, retry_if_exception_type, wait_exponential, stop_after_attempt
from openai import RateLimitError
import logging

logger = logging.getLogger(__name__)

@retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_exponential(multiplier=1.5, min=4, max=60),
    stop=stop_after_attempt(10),
    before_sleep=lambda retry_state: logger.warning(f"Rate limit hit in analyze_ad_image. Retrying... (Attempt {retry_state.attempt_number})")
)
def _call_vision_completion(client, messages):
    return client.chat.completions.create(
        model="pixtral-12b-2409",
        messages=messages,
        temperature=0.1,
        max_tokens=4096,
        response_format={"type": "json_object"},
    )

class AdAnalysis(BaseModel):
    target_audience: str = Field(description="The primary audience targeted by this ad")
    pain_points: List[str] = Field(description="Pain points addressed in the ad")
    value_proposition: str = Field(description="The core value proposition or promise made")
    tone: str = Field(description="The emotional tone of the ad")
    cta: str = Field(description="The primary call to action the ad wants the user to take")
    keywords: List[str] = Field(description="Important keywords and phrases used in the ad")


def analyze_ad(ad_text: str) -> AdAnalysis:
    system_prompt = "You are an expert copywriter and ad analyst. Extract the key elements of the provided ad copy."
    user_prompt = f"Analyze the following ad copy:\n\n{ad_text}"
    return generate_structured_output(
        system_prompt, user_prompt, AdAnalysis,
        model="mistral-small-latest"
    )


def analyze_ad_image(image_base64: str) -> AdAnalysis:
    """Analyze an ad image using Mistral's vision model to extract ad copy elements."""
    client = get_client()

    example_output = json.dumps({
        "target_audience": "Example: Young professionals aged 25-35",
        "pain_points": ["Example pain point 1", "Example pain point 2"],
        "value_proposition": "Example: Premium quality at affordable prices",
        "tone": "Example: Energetic and aspirational",
        "cta": "Example: Shop Now",
        "keywords": ["keyword1", "keyword2"]
    }, indent=2)

    last_error = None
    for attempt in range(1, MAX_JSON_RETRIES + 2):
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "You are an expert copywriter and ad analyst. "
                                "Look at this ad image carefully and extract the key marketing elements. "
                                "Respond with ONLY a JSON object (no markdown, no explanation) with these exact keys filled with actual values from the ad:\n\n"
                                f"{example_output}\n\n"
                                "Replace ALL example values with real values extracted from the ad image. "
                                "Do NOT return the schema definition. Return actual extracted data."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                        },
                    ],
                },
            ]
            response = _call_vision_completion(client, messages)

            content = response.choices[0].message.content
            json_str = _extract_json(content)
            parsed = json.loads(json_str)

            # Guard against schema echo-back
            if "properties" in parsed and "target_audience" not in parsed:
                raise ValueError("Model returned the schema definition instead of actual data")

            return AdAnalysis.model_validate(parsed)

        except Exception as e:
            if isinstance(e, RateLimitError):
                raise
            last_error = e
            logger.warning(f"analyze_ad_image attempt {attempt}/{MAX_JSON_RETRIES + 1} failed: {e}")
            if attempt > MAX_JSON_RETRIES:
                raise

    raise last_error
