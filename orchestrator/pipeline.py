import logging
import time
from typing import Dict, Any

from utils.scraper import scrape_landing_page, fetch_raw_html
from agents.ad_agent import analyze_ad, analyze_ad_image
from agents.page_agent import analyze_landing_page
from agents.category_gate import check_category_gate
from agents.optimizer import optimize_landing_page
from agents.critic_agent import critique_rewrite
from agents.render_agent import render_optimized_html

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# In-memory cache for URLs (cleared on server restart)
URL_CACHE = {}


def run_optimization_pipeline(ad_text: str, lp_url: str, ad_image_base64: str = None) -> Dict[str, Any]:
    logger.info("Starting optimization pipeline")

    # Step 1: Ad Analysis — use image if provided, else text
    if ad_image_base64:
        logger.info("Step 1: Analyzing Ad Image")
        ad_analysis = analyze_ad_image(ad_image_base64)
    else:
        logger.info("Step 1: Analyzing Ad Text")
        ad_analysis = analyze_ad(ad_text)

    # Step 2: LP Analysis
    logger.info(f"Step 2: Scraping Landing Page: {lp_url}")
    if lp_url in URL_CACHE:
        page_text, raw_html = URL_CACHE[lp_url]
    else:
        page_text = scrape_landing_page(lp_url)
        raw_html = fetch_raw_html(lp_url)
        URL_CACHE[lp_url] = (page_text, raw_html)

    if not page_text or not raw_html:
        return {"error": "Failed to scrape landing page"}

    logger.info("Step 2: Analyzing Landing Page")
    time.sleep(2)
    lp_analysis = analyze_landing_page(page_text)

    # Step 3: CATEGORY GATE — atomic binary check (new)
    logger.info("Step 3: Category Gate Check")
    time.sleep(2)
    category_result = check_category_gate(ad_analysis, lp_analysis)
    logger.info(f"Category Gate: match={category_result.categories_match}, "
                f"ad={category_result.ad_category}, lp={category_result.lp_category}")

    if not category_result.categories_match:
        # Early return — do not proceed to Persona/Alignment/Rewrite
        logger.warning("CATEGORY MISMATCH DETECTED — pipeline halted early")
        return {
            "category_mismatch": True,
            "ad_analysis": ad_analysis.model_dump(),
            "lp_analysis": lp_analysis.model_dump(),
            "category_gate": category_result.model_dump(),
            "persona_analysis": None,
            "alignment_recommendation": None,
            "rewritten_lp": None,
            "critic_verdict": {
                "tone_alignment_score": 1,
                "message_match_score": 1,
                "clarity_score": 1,
                "issues": [
                    f"FUNDAMENTAL CATEGORY MISMATCH: Ad promotes '{category_result.ad_category}' "
                    f"but landing page sells '{category_result.lp_category}'.",
                    category_result.reasoning,
                    "Text rewrites cannot fix this. The ad must point to a relevant landing page.",
                ],
                "final_verdict": "retry",
            },
            "rendered_html": None,
        }

    # Step 4: OPTIMIZER LOOP (Evaluator Critic built-in)
    logger.info("PHASE 2: OPTIMIZER AND EVALUATOR (Max 3 attempts)")
    max_retries = 2  # Total 3 attempts
    iteration = 0

    # Step 6: Rewrite & Critic Loop
    max_retries = 2
    iteration = 0
    feedback = None
    final_verdict = None
    rewritten_lp = None

    while iteration <= max_retries:
        logger.info(f"Optimizer Iteration {iteration + 1}/3")
        time.sleep(2)
        optimizer_output = optimize_landing_page(ad_analysis, lp_analysis, feedback)

        logger.info(f"Evaluator Critic Check {iteration + 1}")
        time.sleep(2)
        critic_verdict = critique_rewrite(ad_analysis, lp_analysis, optimizer_output.rewritten_lp)

        logger.info(f"Critic Verdict: {critic_verdict.final_verdict}")
        if critic_verdict.final_verdict == "approve":
            final_verdict = critic_verdict
            break

        # Use issues list as feedback for the next rewrite attempt
        feedback = "; ".join(critic_verdict.issues)
        final_verdict = critic_verdict
        iteration += 1

    rendered_html = None
    if optimizer_output and optimizer_output.rewritten_lp:
        logger.info("PHASE 4: RENDERER — Applying CRO to original HTML")
        time.sleep(2)
        rendered_html = render_optimized_html(raw_html, ad_analysis, optimizer_output)

    return {
        "category_mismatch": False,
        "ad_analysis": ad_analysis.model_dump(),
        "lp_analysis": lp_analysis.model_dump(),
        "category_gate": category_result.model_dump(),
        "persona_analysis": {"summary": optimizer_output.persona_summary} if optimizer_output else None,
        "alignment_recommendation": {"mismatches": optimizer_output.identified_gaps} if optimizer_output else None,
        "rewritten_lp": optimizer_output.rewritten_lp.model_dump() if optimizer_output and optimizer_output.rewritten_lp else None,
        "critic_verdict": final_verdict.model_dump() if final_verdict else None,
        "rendered_html": rendered_html,
        "original_html": raw_html,
    }
