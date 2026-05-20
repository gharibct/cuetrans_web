from pydantic import BaseModel,Json
from typing import Any

# ============== Request Model ==============
# workflowParams will be json 
class JMSRequest(BaseModel):
    workFlowName: str
    workFlowParams: Any
    processType: str | None = None
