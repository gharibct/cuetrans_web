from urllib import request

from fastapi import APIRouter, HTTPException, Form
import json
import logging
from schemas.request import JMSRequest
from services.workflow_handler import handle_workflow

router = APIRouter(prefix="/JMSServlet", tags=["CueTrans Handlers"])
logger = logging.getLogger(__name__) 

# ============== API Endpoint ==============
# async def handle_jms_servlet(
#     workFlowName: str = Form(...),
#     workFlowParams: str = Form(...),
#     processType: str = Form(None)
# ):

@router.post("", include_in_schema=False)
@router.post("/")
# The input will be json and not form data
# Input will be Request Object
async def handle_jms_servlet(
    request: JMSRequest
):    
    """
    Accepts POST requests with form-encoded data matching the original servlet
    """
    try:
        print(f"Received request: {request.workFlowName}, {request.workFlowParams}, {request.processType}")
        result = await handle_workflow(
            workFlowName=request.workFlowName,
            workFlowParams=request.workFlowParams
        )
        return result
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
