"""
Attribute V3 Schema Definitions for ChronoLens.
Strict pydantic and dictionary models for 7-category human attribute predictions,
provenance metadata, confidence scores, evidence frames, and MongoDB serialization.

All fields comply with Mandatory Corrections:
- attributeVersion = "v3"
- Explicit 'unknown' state for unconfident / occluded / too-small evidence.
- Retains mean, median, max confidence, supportRatio, bestEvidenceFrame, and source model.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class AttributeProvenance(BaseModel):
    value: Any = "unknown"
    confidence: float = 0.0
    mean_confidence: float = 0.0
    median_confidence: float = 0.0
    max_confidence: float = 0.0
    support_ratio: float = 0.0
    source: str = "unknown"
    model: str = "unknown"
    region: str = "full_person"
    best_evidence_frame: int = 0
    evidence_frames: List[int] = Field(default_factory=list)


class HeadAttributes(BaseModel):
    hat: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="head"))
    hat_type: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="head"))
    glasses: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="head"))
    sunglasses: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="head"))
    hairLength: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="head"))
    hairColor: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="head"))


class UpperBodyAttributes(BaseModel):
    type: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="upper_body"))
    color: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="upper_body"))
    sleeve: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="upper_body"))


class LowerBodyAttributes(BaseModel):
    type: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="lower_body"))
    color: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="lower_body"))


class FootwearAttributes(BaseModel):
    type: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="footwear"))
    color: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="footwear"))


class AccessoryAttributes(BaseModel):
    necklace: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="neck_accessory"))
    chain: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="neck_accessory"))
    scarf: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="neck_accessory"))


class BagAttributes(BaseModel):
    backpack: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="torso"))
    handbag: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="torso"))
    shoulder_bag: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="torso"))
    carrying_bag: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="torso"))
    holding_object: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="torso"))


class ViewAttributes(BaseModel):
    person_view: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="full_person"))
    body_orientation: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="full_person"))
    walking: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="trajectory"))
    standing: AttributeProvenance = Field(default_factory=lambda: AttributeProvenance(value="unknown", region="trajectory"))


class AttributeV3Evidence(BaseModel):
    bestEvidenceFrame: int = 0
    bestEvidenceTimestamp: float = 0.0
    evidenceFrames: List[int] = Field(default_factory=list)
    supportRatio: float = 0.0
    sampleCount: int = 0


class AttributeV3Record(BaseModel):
    trackId: int
    videoId: str
    attributeVersion: str = "v3"
    head: HeadAttributes = Field(default_factory=HeadAttributes)
    upperBody: UpperBodyAttributes = Field(default_factory=UpperBodyAttributes)
    lowerBody: LowerBodyAttributes = Field(default_factory=LowerBodyAttributes)
    footwear: FootwearAttributes = Field(default_factory=FootwearAttributes)
    accessories: AccessoryAttributes = Field(default_factory=AccessoryAttributes)
    bags: BagAttributes = Field(default_factory=BagAttributes)
    view: ViewAttributes = Field(default_factory=ViewAttributes)
    evidence: AttributeV3Evidence = Field(default_factory=AttributeV3Evidence)

    def to_dict(self) -> Dict[str, Any]:
        return self.dict()
