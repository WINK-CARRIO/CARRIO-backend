from typing import List, Optional

from pydantic import BaseModel
from datetime import datetime


class CompanyCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None


class CompanyResponse(BaseModel):
    id: int
    name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[CompanyResponse]
