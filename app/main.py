import logging
import traceback
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from orchestrator.pipeline import run_optimization_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AdAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PersonalizeRequest(BaseModel):
    ad_text: str = ""
    lp_url: str
    ad_image_base64: Optional[str] = None

@app.get("/")
async def root_health_check():
    return {"status": "AdAgent Backend is running and healthy", "version": "1.0"}

@app.post("/personalize")
async def personalize(request: PersonalizeRequest):
    try:
        if not request.ad_text and not request.ad_image_base64:
            raise HTTPException(status_code=400, detail="Provide either ad text or an ad image")
        result = run_optimization_pipeline(
            request.ad_text, request.lp_url, request.ad_image_base64
        )
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline failed:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
