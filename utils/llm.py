import os
import json
import re
import logging
from typing import Type, TypeVar
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import time

load_dotenv()

T = TypeVar('T', bound=BaseModel)
logger = logging.getLogger(__name__)

MAX_JSON_RETRIES = 2


def get_client() -> OpenAI:
    """Returns an OpenAI-compatible client pointed at the Mistral API."""
    return OpenAI(
        api_key=os.getenv("MISTRAL_API_KEY"),
        base_url="https://api.mistral.ai/v1"
    )


def _extract_json(text: str) -> str:
    """Robustly extract JSON from LLM output that may contain markdown fences or preamble."""
    # Try to find a JSON code block first
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Try to find raw JSON object
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return match.group(0).strip()

    return text.strip()


def generate_structured_output(
    system_prompt: str,
    user_prompt: str,
    response_schema: Type[T],
    temperature: float = 0.1,
    model: str = "mistral-small-latest",
    **kwargs,
) -> T:
    """
    Calls the Mistral API and parses the response into a Pydantic model.
    Retries up to MAX_JSON_RETRIES times if JSON parsing or Pydantic validation fails.
    """
    client = get_client()

    schema_json = json.dumps(response_schema.model_json_schema(), indent=2)

    full_system_prompt = (
        f"{system_prompt}\n\n"
        f"CRITICAL INSTRUCTION: You MUST respond with a JSON object populated with ACTUAL DATA.\n"
        f"Do NOT return or echo the schema definition back to me.\n"
        f"Your output MUST be a valid JSON instance matching this schema:\n"
        f"```json\n{schema_json}\n```\n"
        f"Output raw JSON only. No markdown, no explanation."
    )

    last_error = None

    for attempt in range(5):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": full_system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=4096,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            json_str = _extract_json(content)
            parsed = json.loads(json_str)

            # Defensive check to ensure the LLM didn't just echo the JSON schema
            if "properties" in parsed and any(field not in parsed for field in response_schema.model_fields.keys()):
                raise ValueError("LLM returned the JSON Schema definition instead of actual data.")

            return response_schema.model_validate(parsed)

        except Exception as e:
            last_error = e
            wait = 15 + (2 ** attempt) * 5  # 20s, 25s, 35s, 55s, 95s
            logger.warning(f"Attempt {attempt + 1}/5 failed: {type(e).__name__}: {e}. Retrying in {wait}s...")
            time.sleep(wait)

    raise last_error
