from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MinecraftVersionRange(BaseModel):
    minimum: str
    maximum: str


class PackMetadata(BaseModel):
    name: str
    description: Optional[str] = None
    slug: str
    uploaded: datetime
    minecraft: MinecraftVersionRange
    sha1: str
    main: bool
    is_temporary: bool = Field(default=False, exclude=True)
