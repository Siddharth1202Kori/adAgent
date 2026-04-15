from pydantic import BaseModel, Field
from typing import List
from utils.llm import generate_structured_output


class HeroSection(BaseModel):
    headline: str = Field(description="The main headline in the hero section")
    subtext: str = Field(description="The subtext or subheadline in the hero section")
    cta: str = Field(description="The call to action text in the hero section")


class LandingPageAnalysis(BaseModel):
    primary_offering: str = Field(description="One canonical sentence describing the page's primary commercial offering. E.g. 'This page sells monthly gym memberships and personal training packages.'")
    hero: HeroSection = Field(description="The hero section of the landing page")
    features: List[str] = Field(description="Key features or benefits listed on the page")
    testimonials: List[str] = Field(description="Testimonials or social proof quotes found on the page. Empty list if none found.")
    faq: List[str] = Field(description="FAQ questions found on the page. Empty list if none found.")
    tone: str = Field(description="The overall tone of the landing page content")


def analyze_landing_page(page_text: str) -> LandingPageAnalysis:
    system_prompt = (
        "You are an expert UX researcher and CRO specialist. "
        "Analyze the provided text from a landing page and extract its core structural elements.\n\n"
        "IMPORTANT: The 'primary_offering' field must be a single, clear sentence that describes "
        "what this page is SELLING. Not what the company does in general — what specific product or "
        "service this particular page is trying to get the visitor to buy. "
        "For testimonials and faq, extract actual content if present, otherwise return empty lists."
    )
    user_prompt = f"Analyze the following landing page text:\n\n{page_text}"
    return generate_structured_output(
        system_prompt, user_prompt, LandingPageAnalysis,
        model="mistral-small-latest"
    )
