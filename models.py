from pydantic import BaseModel, Field, UUID4
from typing import Literal, Optional
from datetime import datetime

class MietspiegelCatalog(BaseModel):
    """
    Represents the parent catalog for a specific city and year. 
    Used to route incoming requests to the correct calculation provider.
    """
    id: UUID4 = Field(
        description="Unique identifier for the catalog.",
        examples=["e7b9a5d1-3b4a-4c2d-9876-1a2b3c4d5e6f"]
    )
    slug: str = Field(
        description="URL-friendly identifier for the city.",
        examples=["berlin", "koeln", "muenchen"]
    )
    display_name: str = Field(
        description="Human-readable name of the city/catalog.",
        examples=["Berlin", "Köln"]
    )
    version_year: str = Field(
        description="The active year of the Mietspiegel publication.",
        examples=["2024", "2025"]
    )
    is_active: bool = Field(
        default=True,
        description="Flags if this is the currently active catalog for the city.",
        examples=[True]
    )
    calculation_logic: Literal['street_lookup', 'group_span'] = Field(
        description="Instructs the backend on which provider logic to use for base rent calculations.",
        examples=["street_lookup"]
    )
    zip_code_min: int = Field(
        description="The lowest postal code belonging to this catalog's jurisdiction.",
        examples=[10115]
    )
    zip_code_max: int = Field(
        description="The highest postal code belonging to this catalog's jurisdiction.",
        examples=[14199]
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of when the catalog was added to the database."
    )


class MietspiegelGrid(BaseModel):
    """
    Represents a single row of base rent calculation parameters from a Mietspiegel matrix.
    """
    catalog_id: UUID4 = Field(
        description="Foreign key linking to the MietspiegelCatalog.",
        examples=["e7b9a5d1-3b4a-4c2d-9876-1a2b3c4d5e6f"]
    )
    wohnlage: Literal['low', 'mid', 'good', 'unknown'] = Field(
        description="The assessed residential quality of the specific address or area.",
        examples=["mid"]
    )
    equipment_level: Optional[int] = Field(
        default=None,
        description="Specific to group-span logic (like Cologne). Modifies rent based on heating/bathroom availability.",
        examples=[2]
    )
    buildingyear_min: int = Field(
        default=0,
        description="The start year of the construction period bracket.",
        examples=[1919]
    )
    buildingyear_max: int = Field(
        default=9999,
        description="The end year of the construction period bracket.",
        examples=[1949]
    )
    size_lower: float = Field(
        default=0.0,
        description="The lower bound of the apartment size bracket in square meters.",
        examples=[60.0]
    )
    size_upper: float = Field(
        default=9999.0,
        description="The upper bound of the apartment size bracket in square meters.",
        examples=[89.99]
    )
    rent_sqm_min: float = Field(
        description="The lower bound of the official base rent span.",
        examples=[5.55]
    )
    rent_sqm_avg: float = Field(
        description="The mathematical average or officially stated median base rent.",
        examples=[6.54]
    )
    rent_sqm_max: float = Field(
        description="The upper bound of the official base rent span.",
        examples=[8.82]
    )
    location_flag: Literal['ALL', 'Ost', 'West'] = Field(
        default='ALL',
        description="Geographical constraint necessary for historical city splits (e.g., East vs. West Berlin 1973-1990).",
        examples=["West"]
    )