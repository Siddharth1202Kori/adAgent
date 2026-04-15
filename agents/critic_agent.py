from pydantic import BaseModel, Field
from typing import List, Literal
from agents.ad_agent import AdAnalysis
from agents.page_agent import LandingPageAnalysis
from agents.optimizer import RewrittenLandingPage
from utils.llm import generate_structured_output


class CriticVerdict(BaseModel):
    tone_alignment_score: int = Field(description="Tone alignment score out of 10", ge=0, le=10)
    message_match_score: int = Field(description="Message match score with the ad out of 10", ge=0, le=10)
    clarity_score: int = Field(description="Clarity score out of 10", ge=0, le=10)
    issues: List[str] = Field(description="List of specific issues found in the rewrite")
    final_verdict: Literal["approve", "retry"] = Field(description="Final verdict: 'approve' if all scores >= 7, else 'retry'")


def critique_rewrite(ad: AdAnalysis, original_lp: LandingPageAnalysis, rewritten_lp: RewrittenLandingPage) -> CriticVerdict:
    # --- STANDARD SCORING (only reached if hard gate passes) ---
    system_prompt = (
        "You are an extremely strict and skeptical Landing Page Critic. "
        "The ad and landing page have already been confirmed to be in the same product category. "
        "Your job is to evaluate how well the REWRITTEN text matches the ad.\n\n"
        "SCORING RULES:\n"
        "1. TONE ALIGNMENT: Does the landing page tone generally match the ad's emotional appeal? "
        "Score fairly.\n"
        "2. MESSAGE MATCH: Does the landing page headline directly echo the ad's core promise? "
        "Vague headlines score 5-6.\n"
        "3. CLARITY: Would a visitor from the ad INSTANTLY understand they're in the right place? "
        "Any confusion = score 6 or below.\n"
        "4. Be constructive but fair. Good rewrites deserve 7-9.\n"
        "5. If ANY score is below 7, final_verdict MUST be 'retry'.\n"
        "6. List ALL constructive issues.\n"
        "7. Evaluate COMMERCIAL SUITABILITY."
    )
    user_prompt = (
        f"Ad Context:\n{ad.model_dump_json(indent=2)}\n\n"
        f"Original Landing Page:\n{original_lp.model_dump_json(indent=2)}\n\n"
        f"Rewritten Landing Page:\n{rewritten_lp.model_dump_json(indent=2)}\n\n"
        "Critique the rewritten landing page strictly."
    )
    return generate_structured_output(
        system_prompt, user_prompt, CriticVerdict,
        model="mistral-large-latest"
    )
