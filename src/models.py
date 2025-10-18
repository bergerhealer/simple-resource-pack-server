from pydantic import BaseModel, Field
from datetime import datetime


class MinecraftVersionRange(BaseModel):
    minimum: str
    maximum: str


class PackMetadata(BaseModel):
    name: str
    slug: str
    uploaded: datetime
    minecraft: MinecraftVersionRange
    sha1: str
    main: bool
    is_temporary: bool = Field(default=False, exclude=True)
