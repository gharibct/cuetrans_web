from pydantic import BaseModel

# ============== Response Model ==============
class JMSResponse(BaseModel):
    hdrcache: list[dict]