from pydantic import BaseModel, ConfigDict


class TCExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    previous_school_name: str | None = None
    previous_class: str | None = None
    board: str | None = None
    left_year: str | None = None
    reason_for_leaving: str | None = None
    school_address: str | None = None


class TCExtractionResponse(BaseModel):
    success: bool
    document_type: str = "transfer_certificate"
    fields: TCExtractionResult
