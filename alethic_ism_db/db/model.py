from typing import Optional

from pydantic import BaseModel


class Model(BaseModel):
    id: Optional[int] = None
    provider_name: str
    model_name: str


class Processor(BaseModel):
    id: Optional[int] = None
    name: str
    type: str
    model_id: Optional[int] = None


class ProcessorState(BaseModel):
    processor_id: int
    input_state_id: str
    output_state_id: Optional[str] = None

