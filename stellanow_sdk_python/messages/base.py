"""
Copyright (C) 2022-2025 Stella Technologies (UK) Limited.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_serializer


class StellaNowBaseModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        ser_json_timedelta="iso8601",
    )

    @model_serializer(mode="wrap")
    def serialize_model(self, default_serializer: Any) -> Any:
        data = default_serializer(self)

        def convert_fields(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: convert_fields(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_fields(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
            elif isinstance(obj, date):
                return obj.isoformat()
            return obj

        return convert_fields(data)
