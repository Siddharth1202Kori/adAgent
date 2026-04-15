import streamlit as st
import requests
import time
import base64
import streamlit.components.v1 as components

st.set_page_config(page_title="AdAgent Optimizer", layout="wide")

st.title("AdAgent: Multi-Agent CRO Optimizer")

with st.sidebar:
    st.header("Input Data")

    input_method = st.radio("Ad Input Method", ["Text", "Image Upload"])

    ad_text = ""
    ad_image_b64 = None

    if input_method == "Text":
        ad_text = st.text_area("Paste Ad Copy Here")
    else:
        uploaded_file = st.file_uploader("Upload Ad Image", type=["png", "jpg", "jpeg", "webp"])
        if uploaded_file:
            st.image(uploaded_file, caption="Uploaded Ad", use_column_width=True)
            ad_image_b64 = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")

    lp_url = st.text_input("Landing Page URL")
    submit = st.button("Optimize")

has_ad = ad_text or ad_image_b64

if submit and has_ad and lp_url:
    with st.spinner("Agents are analyzing and optimizing... This may take a minute."):
        start_time = time.time()
        try:
            payload = {"ad_text": ad_text, "lp_url": lp_url}
            if ad_image_b64:
                payload["ad_image_base64"] = ad_image_b64

            response = requests.post(
                "http://127.0.0.1:8000/personalize", json=payload, timeout=300
            )
            response.raise_for_status()
            data = response.json()

            elapsed = time.time() - start_time

            # === CATEGORY MISMATCH — EARLY RETURN ===
            if data.get("category_mismatch"):
                st.error(f"⛔ Category Mismatch Detected (in {elapsed:.2f}s)")

                gate = data.get("category_gate") or {}
                st.markdown(
                    f"**Ad Category:** `{gate.get('ad_category', '?')}`\n\n"
                    f"**Landing Page Category:** `{gate.get('lp_category', '?')}`\n\n"
                    f"**Reason:** {gate.get('reasoning', '')}"
                )

                st.warning(
                    "The ad and landing page are promoting fundamentally different products/services. "
                    "Text rewrites cannot fix this — the ad must point to a relevant landing page."
                )

                # Still show scores (all 1/10)
                verdict = data.get("critic_verdict") or {}
                st.subheader("Critic Scores (Auto-Failed)")
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.metric("Tone Alignment", f"{verdict.get('tone_alignment_score', 1)}/10")
                with sc2:
                    st.metric("Message Match", f"{verdict.get('message_match_score', 1)}/10")
                with sc3:
                    st.metric("Clarity", f"{verdict.get('clarity_score', 1)}/10")

                if verdict.get("issues"):
                    st.markdown("**Issues:**")
                    for issue in verdict.get("issues", []):
                        st.markdown(f"- {issue}")

                with st.expander("View Full Agent Debug Data"):
                    st.json(data)

            # === NORMAL FLOW — CATEGORIES MATCHED ===
            else:
                st.success(f"Optimization complete in {elapsed:.2f} seconds!")

                # Side-by-side: Original vs Improved
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Original Elements")
                    lp = data.get("lp_analysis") or {}
                    hero = lp.get("hero") or {}
                    st.markdown(f"**Hero Headline:**\n{hero.get('headline', '')}")
                    st.markdown(f"**Hero Subtext:**\n{hero.get('subtext', '')}")
                    st.markdown(f"**Hero CTA:**\n{hero.get('cta', '')}")
                    st.markdown("**Features:**")
                    for f in lp.get("features") or []:
                        st.markdown(f"- {f}")
                    if lp.get("testimonials"):
                        st.markdown("**Testimonials:**")
                        for t in lp.get("testimonials") or []:
                            st.markdown(f"- _{t}_")
                    st.markdown(f"**Tone:** {lp.get('tone', '')}")

                with col2:
                    st.subheader("Improved Elements")
                    rw = data.get("rewritten_lp") or {}
                    if rw:
                        rw_hero = rw.get("hero") or {}
                        st.markdown(f"**Hero Headline:**\n{rw_hero.get('headline', '')}")
                        st.markdown(f"**Hero Subtext:**\n{rw_hero.get('subtext', '')}")
                        st.markdown(f"**Hero CTA:**\n{rw_hero.get('cta', '')}")
                        st.markdown("**Features:**")
                        for f in rw.get("features") or []:
                            st.markdown(f"- {f}")
                    else:
                        st.warning("No rewritten landing page returned.")

                st.divider()

                # Category Gate result
                gate = data.get("category_gate") or {}
                st.success(f"✅ Category Gate Passed: Ad ({gate.get('ad_category', '?')}) ↔ LP ({gate.get('lp_category', '?')})")

                # What Changed section
                st.subheader("Alignment Agent: What Changed & Why")
                alignment = data.get("alignment_recommendation") or {}
                st.markdown("#### Mismatches Identified:")
                for m in alignment.get("mismatches") or []:
                    st.markdown(f"- {m}")
                st.markdown("#### Missing Elements:")
                for me in alignment.get("missing_elements") or []:
                    st.markdown(f"- {me}")
                st.markdown("#### Section Recommendations:")
                for section, rec in (alignment.get("section_recommendations") or {}).items():
                    st.markdown(f"- **{section}**: {rec}")

                st.divider()

                # Critic Scores
                st.subheader("Critic Agent Scores")
                verdict = data.get("critic_verdict") or {}
                sc1, sc2, sc3 = st.columns(3)
                with sc1:
                    st.metric("Tone Alignment", f"{verdict.get('tone_alignment_score', '-')}/10")
                with sc2:
                    st.metric("Message Match", f"{verdict.get('message_match_score', '-')}/10")
                with sc3:
                    st.metric("Clarity", f"{verdict.get('clarity_score', '-')}/10")

                final = verdict.get("final_verdict", "")
                if final == "approve":
                    st.success(f"Final Verdict: **{final.upper()}** ✅")
                elif final:
                    st.warning(f"Final Verdict: **{final.upper()}** (best after retries)")

                if verdict.get("issues"):
                    st.markdown("**Issues noted:**")
                    for issue in verdict.get("issues") or []:
                        st.markdown(f"- {issue}")

                st.divider()

                # HTML Previews
                st.subheader("Visual Preview")
                preview_col1, preview_col2 = st.columns(2)
                
                with preview_col1:
                    st.markdown("#### Original Landing Page")
                    original_html = data.get("original_html")
                    if original_html:
                        components.html(original_html, height=600, scrolling=True)
                    else:
                        st.warning("Original HTML not available.")
                
                with preview_col2:
                    st.markdown("#### Optimized Landing Page")
                    rendered_html = data.get("rendered_html")
                    if rendered_html:
                        components.html(rendered_html, height=600, scrolling=True)
                    else:
                        st.warning("Optimized HTML not available.")

                st.divider()

                with st.expander("View Full Agent Debug Data"):
                    st.json(data)

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    if "detail" in error_data:
                        error_msg = error_data["detail"]
                except:
                    pass
            st.error(f"Optimization failed: {error_msg}")
        except Exception as e:
            st.error(f"Error during optimization: {str(e)}")
elif submit:
    st.warning("Please provide an ad (text or image) and a landing page URL.")
