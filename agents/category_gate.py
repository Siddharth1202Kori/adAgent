from pydantic import BaseModel, Field
from agents.ad_agent import AdAnalysis
from agents.page_agent import LandingPageAnalysis
from utils.llm import generate_structured_output


class CategoryGateResult(BaseModel):
    ad_category: str = Field(description="The product/service category the ad is promoting (e.g., 'athletic footwear', 'fitness memberships')")
    lp_category: str = Field(description="The primary product/service category the landing page is selling (e.g., 'fitness memberships', 'SaaS tool')")
    categories_match: bool = Field(description="True ONLY if both categories are the same product/service. False if they are different categories, even if tangentially related.")
    reasoning: str = Field(description="One sentence explaining why the categories match or do not match")


def check_category_gate(ad: AdAnalysis, lp: LandingPageAnalysis) -> CategoryGateResult:
    """
    Atomic, binary category check. This is deliberately a single-purpose prompt 
    to prevent attention dilution across multiple tasks.
    """
    system_prompt = (
        "You are a product categorization expert. Your ONLY job is to determine whether "
        "an ad and a landing page are selling the SAME type of product or service.\n\n"
        "Rules:\n"
        "- 'Athletic shoes' and 'fitness memberships' are DIFFERENT categories. Return false.\n"
        "- 'Running shoes' and 'athletic footwear' are the SAME category. Return true.\n"
        "- 'Protein supplements' and 'gym memberships' are DIFFERENT categories. Return false.\n"
        "- 'Cloud hosting' and 'server management' are the SAME category. Return true.\n"
        "- If the categories are merely tangentially related (both involve sports, both involve health), "
        "they are still DIFFERENT. Return false.\n"
        "- Only return true if a customer clicking the ad would find EXACTLY the type of product/service "
        "they expected on the landing page."
    )
    user_prompt = (
        f"Ad's value proposition: {ad.value_proposition}\n"
        f"Ad's CTA: {ad.cta}\n"
        f"Ad's keywords: {', '.join(ad.keywords)}\n\n"
        f"Landing page's primary offering: {lp.primary_offering}\n"
        f"Landing page's hero headline: {lp.hero.headline}\n"
        f"Landing page's hero CTA: {lp.hero.cta}\n\n"
        "Do these two belong to the SAME product/service category?"
    )
    return generate_structured_output(
        system_prompt, user_prompt, CategoryGateResult,
        model="mistral-large-latest"
    )
