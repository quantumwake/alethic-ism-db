from enum import Enum
from typing import Optional

from core.processor_state import ProcessorStatus
from pydantic import BaseModel


class Processor(BaseModel):
    id: str
    type: str


class ProcessorState(BaseModel):
    processor_id: str
    input_state_id: str
    output_state_id: Optional[str] = None
    status: ProcessorStatus = ProcessorStatus.CREATED

