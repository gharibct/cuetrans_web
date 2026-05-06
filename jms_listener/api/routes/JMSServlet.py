from fastapi import APIRouter, HTTPException, Form
import json
import logging
from schemas.response import JMSResponse
from services.workflow_handler import handle_workflow

router = APIRouter(prefix="/JMSServlet", tags=["CueTrans Handlers"])
logger = logging.getLogger(__name__) 

# ============== API Endpoint ==============
@router.post("", include_in_schema=False)
@router.post("/")
async def handle_jms_servlet(
    workFlowName: str = Form(...),
    workFlowParams: str = Form(...),
    processType: str = Form(None)
):
    """
    Accepts POST requests with form-encoded data matching the original servlet
    """
    try:
        result = await handle_workflow(
            workFlowName=workFlowName,
            workFlowParams=workFlowParams
        )
        return result
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
