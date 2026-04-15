from pydantic import BaseModel, Field
from typing import List
from agents.ad_agent import AdAnalysis
from agents.page_agent import LandingPageAnalysis
from utils.llm import generate_structured_output
from utils.rag import get_rag_context

class RewrittenHero(BaseModel):
    headline: str = Field(description="The rewritten hero headline")
    subtext: str = Field(description="The rewritten hero subtext")
    cta: str = Field(description="The rewritten hero call to action")

class RewrittenLandingPage(BaseModel):
    hero: RewrittenHero = Field(description="The rewritten hero section")
    features: List[str] = Field(description="The rewritten key features")

class OptimizerOutput(BaseModel):
    persona_summary: str = Field(description="One sentence summary of the target persona based on the ad.")
    identified_gaps: List[str] = Field(description="List of strategic mismatches between the ad and current landing page.")
    rewritten_lp: RewrittenLandingPage = Field(description="The actual rewritten landing page copy.")

def optimize_landing_page(
    ad: AdAnalysis,
    lp: LandingPageAnalysis,
    feedback: str = None,
) -> OptimizerOutput:
    """
    Consolidated Optimizer Phase: Combines Persona Inference, Gap Analysis, and Rewriting into ONE call via Chain of Thought.
    """
    # Fetch unified CRO context
    query = f"How to align {lp.primary_offering} with ad value proposition: {ad.value_proposition}"
    cro_context = get_rag_context(query)

    system_prompt = (
        "You are an expert Conversion Rate Optimizer and Copywriter. "
        "Your task is to analyze an ad and a landing page, infer the target persona, output the strategic gaps, "
        "and immediately generate the rewritten text elements for the landing page.\n\n"
        "RULES:\n"
        "1. Identify the Persona first.\n"
        "2. Identify the Strategic Gaps between the ad's promise and the current LP.\n"
        "3. Fully rewrite the text (headline, subtext, features) to perfectly match the ad's tone and value prop.\n"
        "4. Do NOT modify the html structure, just the text."
    )
    
    user_prompt = (
        f"CRO Principles Context:\n{cro_context}\n\n"
        f"Ad Analysis:\n{ad.model_dump_json(indent=2)}\n\n"
        f"Original Landing Page:\n{lp.model_dump_json(indent=2)}\n\n"
    )

    if feedback:
        user_prompt += f"\nNote: The previous rewrite was rejected. Apply this feedback and try again: {feedback}\n"

    return generate_structured_output(system_prompt, user_prompt, OptimizerOutput)
