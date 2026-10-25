"""
services/product_catalog.py

Searches the real Amazon Berkeley Objects (ABO) product catalog.
~42,650 dimension-valid products, ~524 product types.
Does NOT invent products.
"""
import json
import os

import config

_catalog = None


def _load():
    global _catalog
    if _catalog is not None:
        return
    with open(config.ABO_CATALOG_PATH, 'r', encoding='utf-8') as f:
        _catalog = json.load(f)


def search_products(query: str = '', product_type: str = '', limit: int = 20) -> dict:
    """
    Search the ABO catalog by product_type and/or free-text query.
    Returns only records with valid dimensions.
    """
    _load()

    results = []
    q = query.lower().strip()
    pt = product_type.upper().strip()

    for product in _catalog:
        # Must have valid dimensions
        try:
            l = float(product.get('length', 0) or 0)
            w = float(product.get('width', 0) or 0)
            h = float(product.get('height', 0) or 0)
        except (TypeError, ValueError):
            continue
        if l <= 0 or w <= 0 or h <= 0:
            continue

        ptype = str(product.get('product_type', '')).upper()

        type_match = (not pt) or (pt in ptype)
        text_match = (not q) or (
            q in str(product.get('item_name', '')).lower() or
            q in ptype.lower()
        )

        if type_match and text_match:
            results.append({
                'item_id': product.get('item_id'),
                'item_name': product.get('item_name'),
                'product_type': product.get('product_type'),
                'length_in': l,
                'width_in': w,
                'height_in': h,
                'volume_cubic_in': product.get('volume_cubic_in'),
            })

        if len(results) >= limit:
            break

    return {
        'count': len(results),
        'products': results,
        'catalog_size': len(_catalog),
    }


def get_representative_product(product_type: str) -> dict | None:
    """
    Return the median-volume product of a given type.
    Used by the vision pipeline to get real dimensions after detection.
    """
    _load()

    pt = product_type.upper().strip()
    candidates = []

    for product in _catalog:
        if str(product.get('product_type', '')).upper() != pt:
            continue
        try:
            l = float(product.get('length', 0) or 0)
            w = float(product.get('width', 0) or 0)
            h = float(product.get('height', 0) or 0)
        except (TypeError, ValueError):
            continue
        if l <= 0 or w <= 0 or h <= 0:
            continue
        candidates.append(product)

    if not candidates:
        return None

    candidates.sort(key=lambda p: float(p.get('volume_cubic_in', 0) or 0))
    median = candidates[len(candidates) // 2]

    raw_weight = median.get('weight')
    parsed_weight = None
    if raw_weight is not None and str(raw_weight).strip() != '':
        try:
            parsed_weight = float(raw_weight)
        except (ValueError, TypeError):
            parsed_weight = None

    return {
        'item_id': median.get('item_id') or median.get('product_id'),
        'item_name': median.get('item_name') or median.get('product_name'),
        'product_type': median.get('product_type'),
        'length_in': float(median.get('length', 0)),
        'width_in': float(median.get('width', 0)),
        'height_in': float(median.get('height', 0)),
        'weight': parsed_weight,
        'weight_unit': median.get('weight_unit'),
        'catalog_candidates': len(candidates),
    }
