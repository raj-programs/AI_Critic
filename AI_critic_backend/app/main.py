
# main.py

import logging

import requests
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy import text

from app.core.database import engine
from app.services.crawler.runner import run_crawler
from app.services.hci.rules import run_all_rules
from app.services.ai.vlm import analyze_screenshot
from app.services.ai.critic_gemini import (
    CriticUnavailableError,
    analyze_with_critic,
)
from app.services.hci.analyzer import analyze_results


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Preflight Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebsiteRequest(BaseModel):
    url: HttpUrl

@app.get("/")
def root():
    return {"message": "Preflight API is running."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db")
def test_db():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return {"database": result.scalar()}
    except Exception:
        logger.exception("Database connection failed")
        raise HTTPException(
            status_code=503,
            detail="Database connection failed.",
        )


@app.post("/analyze")
async def analyze_website(request: WebsiteRequest):
    url = str(request.url)

    # Prevent crawling arbitrary non-web URL schemes.
    if request.url.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail="Only HTTP and HTTPS URLs are supported.",
        )

    try:
        # 1. Crawl the website and collect raw evidence.
        crawl_data = await run_in_threadpool(
            run_crawler,
            url,
        )

        if not isinstance(crawl_data, dict):
            raise RuntimeError(
                "Crawler did not return a dictionary."
            )

        if not crawl_data.get("screenshot", {}).get("path"):
            raise RuntimeError(
                "Crawler did not produce a screenshot."
            )

        # 2. Run deterministic HCI rules.
        hci_findings = await run_in_threadpool(
            run_all_rules,
            crawl_data,
        )

        component_status = {
            "crawler": {"status": "completed"},
            "hci_rules": {"status": "completed"},
            "vlm": {"status": "completed"},
            "critic": {"status": "completed"},
        }

        # 3. Analyze the screenshot using the VLM.
        screenshot_path = crawl_data["screenshot"]["path"]

        try:
            vlm_result = await run_in_threadpool(
                analyze_screenshot,
                screenshot_path,
            )
        except (ValueError, RuntimeError, requests.RequestException) as error:
            logger.warning("VLM failed without producing findings: %s", error)
            vlm_result = {"findings": []}
            component_status["vlm"] = {
                "status": "failed",
                "error": "The optional VLM could not complete.",
            }

        vlm_data = (
            vlm_result.model_dump(mode="json")
            if hasattr(vlm_result, "model_dump")
            else vlm_result
        )

        vlm_findings = (
            vlm_data.get("findings", [])
            if isinstance(vlm_data, dict)
            else []
        )

        # The critic is additive. Its unavailability must not discard
        # completed crawler, rule-engine, or VLM results.
        try:
            critic_result = await run_in_threadpool(
                analyze_with_critic,
                crawl_data,
                hci_findings,
                vlm_findings,
            )
        except CriticUnavailableError as error:
            logger.warning("Critic unavailable: %s", error)
            critic_result = {"findings": []}
            component_status["critic"] = {
                "status": "unavailable",
                "error": "The optional critic could not complete.",
            }
        except (ValueError, ImportError, requests.RequestException) as error:
            logger.warning("Critic failed without producing findings: %s", error)
            critic_result = {"findings": []}
            component_status["critic"] = {
                "status": "failed",
                "error": "The optional critic could not complete.",
            }

        critic_data = (
            critic_result.model_dump(
                mode="json",
                by_alias=True,
            )
            if hasattr(critic_result, "model_dump")
            else critic_result
        )

        # 5. Merge findings and calculate the provisional score.
        final_report = analyze_results(
            crawl_data=crawl_data,
            hci_findings=hci_findings,
            vlm_result=vlm_result,
            critic_result=critic_result,
        )

        return {
            **final_report,
            "url": url,
            "crawl": crawl_data,
            "vlm": vlm_data,
            "critic": critic_data,
            "analysis_status": {
                "status": (
                    "partial"
                    if any(
                        component["status"] != "completed"
                        for component in component_status.values()
                    )
                    else "completed"
                ),
                "components": component_status,
            },
        }

    except HTTPException:
        raise

    except Exception:
        logger.exception("Website analysis failed")
        critic_result = {"findings": []}

        raise HTTPException(
            status_code=500,
            detail=(
                "Website analysis failed. "
                "Check the backend logs for details."
            ),
        )
