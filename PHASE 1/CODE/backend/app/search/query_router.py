"""
Query Router for ChronoLens Phase 3.19.
Classifies input search queries into deterministic production execution routes.

Routes (in priority order):
  NATIVE_OBJECT    — standalone YOLO-class objects (laptop, bottle, etc.)
  CLOTHING_COLOR   — person + upper-body color (person wearing white shirt)
  HUMAN_ATTRIBUTE  — head attributes (glasses, hat, hair length)
  BAG_RELATION     — person carrying / with bag/backpack
  SPEECH           — spoken content / dialogue retrieval
  SCENE            — indoor/outdoor environment queries
  RELATION         — spatial/temporal relations between objects
  COMPOSITE        — multi-attribute compound queries
  GENERIC_SEMANTIC — fallback full-text semantic search
"""

import re
from typing import Dict, Any, List, Optional


class QueryRouter:
    """Classifies search queries into dedicated production routes."""

    # ── Taxonomy ──────────────────────────────────────────────────────────────

    COLORS = [
        "white", "black", "grey", "gray", "blue", "red", "yellow",
        "green", "purple", "pink", "brown", "beige", "orange", "silver",
    ]

    # YOLO-detectable standalone objects.
    # NOTE: "backpack" and "handbag" are YOLO classes → NATIVE_OBJECT only
    # when queried ALONE (no "person carrying" context).
    NATIVE_YOLO_OBJECTS: Dict[str, str] = {
        "laptop": "laptop", "notebook": "laptop", "computer": "laptop",
        "keyboard": "keyboard",
        "handbag": "handbag", "purse": "handbag",
        "backpack": "backpack",
        "bottle": "bottle", "water bottle": "bottle",
        "chair": "chair",
        "tv": "tv", "tv screen": "tv", "television": "tv",
        "monitor": "tv", "screen": "tv",
        "cell phone": "cell phone", "phone": "cell phone",
        "mobile phone": "cell phone", "mobile": "cell phone",
        "book": "book",
        "pizza": "pizza",
        "remote": "remote", "remote control": "remote",
        "tie": "tie", "necktie": "tie",
        "car": "car", "vehicle": "car",
        "bicycle": "bicycle", "bike": "bicycle",
        "motorcycle": "motorcycle",
        "bus": "bus",
        "truck": "truck",
        "umbrella": "umbrella",
        "suitcase": "suitcase",
        "sports ball": "sports ball",
        "person": "person",
    }

    # Attributes genuinely classified by the PP-Human PAR checkpoint.
    # hair length is NOT in the checkpoint — do not claim it is.
    PAR_SUPPORTED_ATTRS = {"glasses", "sunglasses", "hat", "cap", "backpack", "handbag", "shoulder bag"}

    # Head / human attributes that should NEVER be sent to Object FAISS.
    HEAD_ATTRIBUTES: List[str] = [
        "glasses", "sunglasses",
        "hat", "cap", "beanie", "helmet",
        "long hair", "short hair", "hair",
    ]

    # Bag-carry surface forms
    BAG_CARRY_PATTERNS = [
        r"person\s+carrying",
        r"man\s+carrying",
        r"woman\s+carrying",
        r"carrying\s+a\s+bag",
        r"carrying\s+a\s+backpack",
        r"carrying\s+a\s+handbag",
        r"carrying\s+a\s+shoulder\s+bag",
        r"person\s+with\s+a?\s*bag",
        r"person\s+with\s+a?\s*backpack",
        r"person\s+with\s+a?\s*handbag",
        r"person\s+with\s+a?\s*purse",
    ]

    # Speech / dialogue intent signals
    SPEECH_PATTERNS = [
        r"\b(what|who|where|when|did|has|how)\b.*\b(say|said|saying|says|speak|spoke|spoken|speaking|talk|talked|talking|mention|mentioned|mentions|tell|told)\b",
        r"\b(say|said|saying|says)\b",
        r"\b(talk|talking|talked|talks)\b",
        r"\b(speak|spoke|spoken|speaking)\b",
        r"\b(mention|mentions|mentioned|mentioning)\b",
        r"\b(conversation|dialogue|phrase|words|transcript)\b",
        r"\b(someone|person|anyone|man|woman|he|she|they)\s+(said|saying|spoke|speaking|talked|talking|mentioned|told)\b",
        r"\b(tell|told)\b",
        r"\b(where|how|what|why)\s+(are|is|were|was)\s+(you|they|we|he|she)\b",
        r"\b(audio|speech|spoken|narrat)\b",
    ]

    # Spatial/temporal relation keywords
    RELATION_PATTERNS = [
        r"\bnear\b", r"\bnext\s+to\b", r"\bbeside\b",
        r"\bbefore\b", r"\bafter\b", r"\bbehind\b",
        r"\bwith\b", r"\briding\b", r"\bholding\b",
    ]

    @classmethod
    def classify(cls, query_str: str) -> Dict[str, Any]:
        """
        Classify a query string into a route dict.
        """
        q = query_str.strip()

        # ── 0A. EXPLICIT OCR SYNTAX: what they see: "TEXT"
        ocr_match = re.match(r"^\s*what\s+they\s+see\s*:\s*(.*)$", q, re.IGNORECASE)
        if ocr_match:
            raw_target = ocr_match.group(1).strip()
            extracted_text = raw_target.strip("\"'").strip()
            return {
                "route": "OCR",
                "ocrTextQuery": extracted_text,
                "targetPhrase": extracted_text,
                "extracted_text": extracted_text,
                "raw_query": query_str,
            }

        # ── 0B. EXPLICIT SPEECH SYNTAX: what they say: "TEXT"
        speech_match = re.match(r"^\s*what\s+they\s+say\s*:\s*(.*)$", q, re.IGNORECASE)
        if speech_match:
            raw_target = speech_match.group(1).strip()
            extracted_text = raw_target.strip("\"'").strip()
            return {
                "route": "SPEECH",
                "speechMode": "EXACT_PHRASE",
                "targetPhrase": extracted_text,
                "speech_query": extracted_text,
                "extracted_text": extracted_text,
                "raw_query": query_str,
            }

        # Clean quotes for intent checking (quotes alone DO NOT trigger SPEECH)
        q_unquoted = q.strip("\"'").strip()
        ql = q_unquoted.lower()

        # ── 1. BAG_RELATION — check first for explicit bag carry intent
        for pat in cls.BAG_CARRY_PATTERNS:
            if re.search(pat, ql):
                bag_type = "backpack" if "backpack" in ql else \
                           "handbag" if "handbag" in ql else \
                           "shoulder bag" if "shoulder" in ql else "bag"
                bag_color = None
                for c in cls.COLORS:
                    if c in ql:
                        bag_color = c
                        break
                return {
                    "route": "BAG_RELATION",
                    "bag_type": bag_type,
                    "bag_color": bag_color,
                    "raw_query": query_str,
                }

        # ── 2. SPEECH — spoken content / dialogue retrieval
        # Checked BEFORE standalone native objects so queries like "What did he say about the bus?" route to SPEECH
        is_speech_intent = False
        for pat in cls.SPEECH_PATTERNS:
            if re.search(pat, ql):
                is_speech_intent = True
                break

        # Double check: visual attribute context overrides ambiguous single-word triggers
        visual_attribute_context = any(re.search(rf"\b{re.escape(attr)}\b", ql) for attr in cls.HEAD_ATTRIBUTES) or \
                                   any(w in ql for w in ["wearing", "dressed", "shirt", "pants", "shoes", "glasses", "hat"])

        if is_speech_intent and not (visual_attribute_context and not any(w in ql for w in ["say", "said", "saying", "speak", "spoke", "spoken", "talk", "mention", "tell", "told"])):
            quoted_match = re.search(r'"([^"]+)"|\'([^\']+)\'', query_str.strip())
            extracted_phrase = (quoted_match.group(1) or quoted_match.group(2) or "").strip() if quoted_match else ""
            if extracted_phrase:
                speech_mode = "EXACT_PHRASE"
                target_phrase = extracted_phrase
            else:
                speech_mode = "NATURAL"
                target_phrase = q_unquoted
            return {
                "route": "SPEECH",
                "speechMode": speech_mode,
                "targetPhrase": target_phrase,
                "speech_query": q_unquoted,
                "raw_query": query_str,
            }

        # Context-aware clothing grammar helper
        clothing_items = ["shirt", "top", "pants", "trousers", "jeans", "shorts", "jacket", "coat", "sweater", "hoodie", "suit", "dress", "skirt", "clothes", "outfit", "jersey", "vest", "t-shirt", "tshirt", "hat", "cap"]
        person_nouns = ["person", "man", "woman", "guy", "lady", "boy", "girl", "someone", "anyone"]

        clothing_grammar_pattern = rf"\b(?:{'|'.join(person_nouns)})\s+(?:in|wearing|dressed\s+in)\s+({'|'.join(cls.COLORS)})\s+({'|'.join(clothing_items)})\b"
        grammar_match = re.search(clothing_grammar_pattern, ql, re.IGNORECASE)

        # ── 3. NATIVE_OBJECT — standalone YOLO class queries
        ql_clean = re.sub(r"^(a|an|the)\s+", "", ql).strip()
        sorted_objects = sorted(cls.NATIVE_YOLO_OBJECTS.keys(), key=len, reverse=True)
        for obj_key in sorted_objects:
            if ql_clean == obj_key or re.search(rf"\b{re.escape(obj_key)}\b", ql_clean):
                yolo_class = cls.NATIVE_YOLO_OBJECTS[obj_key]
                attribute_context = grammar_match is not None or any(w in ql for w in [
                    "wearing", "carrying", "with glasses", "with hat",
                    "with long hair", "with short hair", "with a hat",
                ])
                if not attribute_context and yolo_class != "backpack":
                    return {
                        "route": "NATIVE_OBJECT",
                        "target_object": yolo_class,
                        "raw_query": query_str,
                    }

        # ── 4. CLOTHING_COLOR
        if grammar_match:
            return {
                "route": "CLOTHING_COLOR",
                "color": grammar_match.group(1).lower(),
                "clothing_item": grammar_match.group(2).lower(),
                "raw_query": query_str,
            }

        matched_color = None
        for c in cls.COLORS:
            if re.search(rf"\b{re.escape(c)}\b", ql):
                matched_color = c
                break

        if matched_color:
            clothing_context = any(w in ql for w in [
                "shirt", "top", "clothes", "jacket", "coat", "sweater",
                "wearing", "dressed", "outfit", "jersey",
            ]) and any(w in ql for w in ["person", "man", "woman", "guy", "lady"])
            if clothing_context:
                return {
                    "route": "CLOTHING_COLOR",
                    "color": matched_color,
                    "raw_query": query_str,
                }

        # ── 5. HUMAN_ATTRIBUTE (glasses, hat, hair — NEVER sent to Object FAISS)
        for ha in cls.HEAD_ATTRIBUTES:
            if re.search(rf"\b{re.escape(ha)}\b", ql):
                is_par_supported = ha in cls.PAR_SUPPORTED_ATTRS
                is_hair = "hair" in ha
                return {
                    "route": "HUMAN_ATTRIBUTE",
                    "attribute": ha,
                    "par_supported": is_par_supported and not is_hair,
                    "is_hair": is_hair,
                    "raw_query": query_str,
                }

        # ── 6. SCENE — environment / location
        if any(w in ql for w in [
            "indoor", "outdoor", "outside", "inside",
            "office", "street", "road", "park", "corridor", "hallway",
            "parking", "station", "mall", "supermarket", "store",
        ]):
            return {
                "route": "SCENE",
                "raw_query": query_str,
            }

        # ── 7. RELATION — spatial/temporal relations
        for pat in cls.RELATION_PATTERNS:
            if re.search(pat, ql):
                return {
                    "route": "RELATION",
                    "raw_query": query_str,
                }

        # ── 8. GENERIC_SEMANTIC fallback
        return {
            "route": "GENERIC_SEMANTIC",
            "raw_query": query_str,
        }

