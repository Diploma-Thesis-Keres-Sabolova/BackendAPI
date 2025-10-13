from datetime import datetime, date

from pydantic import BaseModel

class CustomBaseModel(BaseModel):
    class Config:
        from_attributes = True
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),  # datetime.datetime
            date: lambda v: v.isoformat(),
        }
        str_strip_whitespace = True

