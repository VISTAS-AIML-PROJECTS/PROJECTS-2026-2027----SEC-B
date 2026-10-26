import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("chronolens.search.attribute_filter")


COLOR_KEYWORDS = ["black", "white", "grey", "gray", "red", "blue", "green", "yellow", "brown", "silver", "purple", "orange", "pink"]
LOCATION_KEYWORDS = {
    "conference room": "office",
    "conference": "office",
    "meeting room": "office",
    "meeting": "office",
    "indoor office": "office",
    "office": "office",
    "classroom": "classroom",
    "corridor": "corridor",
    "hallway": "corridor",
    "road": "road",
    "street": "road",
    "parking area": "parking",
    "parking": "parking",
    "garage": "parking",
    "park": "park"
}



class AttributeFilter:
    """
    Phase 2.4 Attribute Query Parser & Search Result Refinement Layer.
    Extracts visual attribute and scene keywords from natural language search queries
    and calculates attribute evidence match scores for candidate results without
    modifying the Phase 2.3 hybrid ranking formula.
    """

    @classmethod
    def parse_query(cls, query: str) -> Dict[str, Any]:
        """
        Parses a natural language query into attribute key-value pairs.
        """
        q_lower = query.lower()
        extracted = {}

        # 0A. Explicit OCR syntax: what they see: "TEXT"
        ocr_match = re.match(r"^\s*what\s+they\s+see\s*:\s*(.*)$", query.strip(), re.IGNORECASE)
        if ocr_match:
            raw_target = ocr_match.group(1).strip()
            extracted_text = raw_target.strip("\"'").strip()
            extracted["ocrTextQuery"] = extracted_text
            extracted["explicitOcrQuery"] = True
            return extracted

        # 0B. Explicit Speech syntax: what they say: "TEXT"
        speech_match = re.match(r"^\s*what\s+they\s+say\s*:\s*(.*)$", query.strip(), re.IGNORECASE)
        if speech_match:
            raw_target = speech_match.group(1).strip()
            extracted_text = raw_target.strip("\"'").strip()
            extracted["speechTextQuery"] = extracted_text
            extracted["explicitSpeechQuery"] = True
            return extracted

        # 0. Standalone Explicit Native Object Query Detection
        q_clean = re.sub(r'^(a|an|the)\s+', '', q_lower).strip()
        native_vocab = {
            "laptop": "laptop", "notebook": "laptop", "computer": "laptop",
            "keyboard": "keyboard", "keypad": "keyboard",
            "handbag": "handbag", "purse": "handbag",
            "bottle": "bottle", "water bottle": "bottle",
            "chair": "chair", "seat": "chair",
            "tv": "tv", "tv screen": "tv", "television": "tv", "monitor": "tv", "screen": "tv",
            "cell phone": "cell phone", "phone": "cell phone", "mobile phone": "cell phone", "mobile": "cell phone",
            "book": "book",
            "pizza": "pizza",
            "remote": "remote", "remote control": "remote",
            "tie": "tie", "necktie": "tie",
            "car": "car", "red car": "car",
            "dog": "dog",
            "cat": "cat"
        }

        person_action_mods = ["person", "man", "woman", "child", "pedestrian", "wearing", "riding", "carrying", "near", "standing", "walking"]
        has_person_mod = any(mod in q_lower for mod in person_action_mods)

        if not has_person_mod and q_clean in native_vocab:
            extracted["explicitNativeObjectQuery"] = True
            extracted["requiredObjectClass"] = native_vocab[q_clean]
            return extracted

        # Keywords for clothing regions vs vehicle
        lower_keywords = ["pants", "trousers", "jeans", "shorts", "skirt", "bottom", "bottoms", "slacks", "leggings"]
        upper_keywords = ["shirt", "t-shirt", "tshirt", "top", "jacket", "coat", "hoodie", "sweater", "blazer", "upper", "vest"]
        vehicle_keywords = ["car", "vehicle", "truck", "bus", "bike", "bicycle", "motorcycle", "auto", "van"]

        has_lower_kw = any(kw in q_lower for kw in lower_keywords)
        has_upper_kw = any(kw in q_lower for kw in upper_keywords)
        has_vehicle_kw = any(kw in q_lower for kw in vehicle_keywords)

        # 1. Color Extraction & Targeting
        for color in COLOR_KEYWORDS:
            if color in q_lower:
                c_val = "grey" if color == "gray" else color
                if has_vehicle_kw:
                    extracted["vehicleColor"] = c_val
                    extracted["requiredObjectClass"] = "car"
                elif has_lower_kw:
                    extracted["lowerClothingColor"] = c_val
                    extracted["requiredObjectClass"] = "person"
                elif has_upper_kw:
                    extracted["upperClothingColor"] = c_val
                    extracted["requiredObjectClass"] = "person"
                else:
                    # Generic color query without explicit body part (e.g. "person in red")
                    extracted["upperClothingColor"] = c_val
                    if "person" in q_lower or "man" in q_lower or "woman" in q_lower or "wearing" in q_lower:
                        extracted["requiredObjectClass"] = "person"
                break

        # 2. Accessories & Headwear
        if "backpack" in q_lower or "bag" in q_lower or "carrying" in q_lower:
            extracted["hasBackpack"] = True
            extracted["requiredObjectClass"] = "person"
        if "helmet" in q_lower:
            extracted["hasHelmet"] = True
            extracted["requiredObjectClass"] = "person"
        if "hat" in q_lower or "cap" in q_lower or "headwear" in q_lower:
            extracted["hasHat"] = True
            extracted["requiredObjectClass"] = "person"
        if "glasses" in q_lower or "sunglasses" in q_lower:
            extracted["hasGlasses"] = True
            extracted["requiredObjectClass"] = "person"

        # 3. Environment & Location
        if "indoor" in q_lower:
            extracted["environment"] = "indoor"
        elif "outdoor" in q_lower:
            extracted["environment"] = "outdoor"

        for kw, loc_type in LOCATION_KEYWORDS.items():
            if kw in q_lower:
                extracted["locationType"] = loc_type
                break

        # 3.5 OCR / Building Text Queries (e.g., "student service", "chicano")
        ocr_phrases = ["student service", "student services", "chicano", "student", "service"]
        matched_ocr = [p for p in ocr_phrases if p in q_lower]
        if matched_ocr:
            extracted["ocrTextQuery"] = matched_ocr[0]

        # 4. Relational Query Parsing & Synonym Mapping
        object_norm_map = {
            "man": "person", "woman": "person", "child": "person",
            "pedestrian": "person", "skater": "person", "skateboarder": "person",
            "bike": "bicycle", "skating": "skateboard"
        }
        accessory_items = {"backpack", "bag", "glasses", "sunglasses", "hat", "cap", "helmet"}

        rel_pattern = r"(person|man|woman|child|pedestrian|skater|skateboarder|car|vehicle|truck|bus|bicycle|bike|motorcycle|backpack|bag|dog|cat|object)\s+(near|riding|skating|with|carrying|wearing|before|after)\s+(?:a\s+|an\s+|the\s+)?(person|man|woman|child|pedestrian|car|vehicle|truck|bus|bicycle|bike|motorcycle|skateboard|backpack|bag|dog|cat|glasses|sunglasses|hat|cap|helmet|object)"
        rel_match = re.search(rel_pattern, q_lower)
        if rel_match:
            p_obj = object_norm_map.get(rel_match.group(1), rel_match.group(1))
            raw_rel = rel_match.group(2)
            s_obj = object_norm_map.get(rel_match.group(3), rel_match.group(3))

            rel_type = "riding" if raw_rel == "skating" else ("with" if raw_rel in {"carrying", "wearing"} else raw_rel)

            # Check if this is an accessory worn/carried by a person vs a genuine spatial relation between distinct objects
            if p_obj == "person" and s_obj in accessory_items and rel_type in {"with", "carrying", "wearing"}:
                extracted["requiredObjectClass"] = "person"
                if s_obj in {"backpack", "bag"}:
                    extracted["hasBackpack"] = True
                elif s_obj in {"glasses", "sunglasses"}:
                    extracted["hasGlasses"] = True
                elif s_obj in {"hat", "cap"}:
                    extracted["hasHat"] = True
                elif s_obj == "helmet":
                    extracted["hasHelmet"] = True
            else:
                rel_info = {
                    "primaryObject": p_obj,
                    "relation": rel_type,
                    "secondaryObject": s_obj
                }
                extracted["relationInfo"] = rel_info
                extracted["primaryObject"] = p_obj
                extracted["relation"] = rel_type
                extracted["secondaryObject"] = s_obj
        elif "skat" in q_lower:
            # Standalone skating query -> map to person riding skateboard or person + skateboard
            extracted["primaryObject"] = "person"
            extracted["relation"] = "riding"
            extracted["secondaryObject"] = "skateboard"
            extracted["relationInfo"] = {
                "primaryObject": "person",
                "relation": "riding",
                "secondaryObject": "skateboard"
            }

        return extracted



    @classmethod
    def calculate_match_score(cls, item_attributes: Dict[str, Any], query_attributes: Dict[str, Any]) -> float:
        """
        Calculates normalized attribute match score (0.0 to 1.0) between stored metadata and query attributes.
        """
        if not query_attributes:
            return 1.0

        matches = 0
        total_checks = len(query_attributes)

        for key, expected_val in query_attributes.items():
            actual_val = item_attributes.get(key)
            if actual_val is not None:
                if isinstance(expected_val, bool):
                    if actual_val == expected_val:
                        matches += 1
                elif isinstance(expected_val, str):
                    if str(actual_val).lower() == expected_val.lower():
                        matches += 1

        return round(float(matches) / float(total_checks), 4) if total_checks > 0 else 1.0
