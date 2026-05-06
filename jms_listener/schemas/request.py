from pydantic import BaseModel

# ============== Request Model ==============
class JMSRequest(BaseModel):
    workFlowName: str
    workFlowParams: str
    processType: str | None = None
