from utils.llm import get_client
import logging
import time
from agents.page_agent import LandingPageAnalysis
from agents.ad_agent import AdAnalysis
from agents.optimizer import RewrittenLandingPage, OptimizerOutput

logger = logging.getLogger(__name__)


def render_optimized_html(original_html: str, ad: AdAnalysis, optimizer_output: OptimizerOutput) -> str:
    """
    The Render Agent — the final CRO applier.
    
    Takes the original site HTML, the ad creative analysis, and the full optimizer output
    (persona, identified gaps, rewritten copy) and produces a complete HTML page that:
      - Preserves the site's visual theme, images, layout, and brand identity
      - Injects the optimized ad-aligned copy (headline, subtext, CTA, features)
      - Applies CRO best practices to bridge the ad ↔ landing page experience
    """
    client = get_client()

    system_prompt = (
        "You are an expert CRO (Conversion Rate Optimization) Frontend Developer.\n\n"
        "YOUR MISSION:\n"
        "You receive the COMPLETE HTML of an original landing page, an ad analysis, and CRO optimization data.\n"
        "Your job is to produce the COMPLETE optimized HTML page that:\n\n"
        "1. PRESERVES the site's visual theme — all CSS, colors, fonts, images, layout, and brand identity stay INTACT.\n"
        "2. REPLACES the text copy (hero headline, subtext, CTA, features) with the optimized versions provided.\n"
        "3. APPLIES CRO principles to bridge the gap between the ad creative and the landing page:\n"
        "   - Ensure the hero section directly echoes the ad's value proposition (Message Match)\n"
        "   - Strengthen the CTA to continue the ad's call-to-action flow (CTA Continuity)\n"
        "   - Ensure the tone matches the ad's emotional register (Tone Alignment)\n"
        "   - If the ad highlights specific benefits, make sure those are prominent on the page\n"
        "4. DO NOT remove or break any images, links, product cards, testimonials, or structural elements.\n"
        "5. DO NOT add new sections that don't exist in the original.\n"
        "6. DO NOT wrap output in markdown code blocks. Output raw HTML starting with <!DOCTYPE html>.\n\n"
        "Think of it as: SAME SITE, SAME LOOK, but the WORDS now perfectly match the ad that brought the visitor here."
    )

    user_prompt = (
        "=== AD ANALYSIS ===\n"
        f"Value Proposition: {ad.value_proposition}\n"
        f"CTA: {ad.cta}\n"
        f"Tone: {ad.tone}\n"
        f"Target Audience: {ad.target_audience}\n\n"
        "=== CRO OPTIMIZER OUTPUT ===\n"
        f"Target Persona: {optimizer_output.persona_summary}\n"
        f"Identified Gaps: {', '.join(optimizer_output.identified_gaps)}\n\n"
        "=== OPTIMIZED COPY TO INJECT ===\n"
        f"New Hero Headline: {optimizer_output.rewritten_lp.hero.headline}\n"
        f"New Hero Subtext: {optimizer_output.rewritten_lp.hero.subtext}\n"
        f"New CTA: {optimizer_output.rewritten_lp.hero.cta}\n"
        f"New Features:\n"
    )
    for i, feat in enumerate(optimizer_output.rewritten_lp.features, 1):
        user_prompt += f"  {i}. {feat}\n"

    user_prompt += (
        "\n=== ORIGINAL HTML (PRESERVE THIS DESIGN) ===\n\n"
        f"{original_html}\n\n"
        "=== END ===\n\n"
        "Return the COMPLETE optimized HTML page. Same design, same images, optimized words."
    )

    for attempt in range(5):
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            response = client.chat.completions.create(
                model="mistral-large-latest",
                messages=messages,
                temperature=0.05,
                max_tokens=8192,
            )

            content = response.choices[0].message.content.strip()

            # Strip markdown fences if the LLM wrapped it
            if content.startswith("```html"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            return content.strip()
        except Exception as e:
            wait = 15 + (2 ** attempt) * 5
            logger.error(f"Error rendering HTML (attempt {attempt+1}/5): {e}. Retrying in {wait}s...")
            time.sleep(wait)

    return "<p>Failed to render optimized HTML after retries.</p>"
