from enum import StrEnum


class ProcessType(StrEnum):
    HDR_FETCH = "HdrFetch"
    MTL_FETCH = "MTLFetch"
    INIT = "Init"

