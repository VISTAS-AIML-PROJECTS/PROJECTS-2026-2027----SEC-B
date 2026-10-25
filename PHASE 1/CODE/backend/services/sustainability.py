"""
services/sustainability.py

Packaging simulation using real Packrift catalog data only.

Fields used (all from catalog — nothing invented):
  sku, title, family, product_type
  length_in, width_in, height_in, cube_in
  unit_price          — per-unit cost (present in 1843/2209 records)
  package_weight_lb   — per-unit physical weight = snapshot_weight_value / pack_quantity
                        (present in 1843/2209 records; confirmed by derivation)
  co2e_recycling_mt   — CO₂ equivalent avoided during recycling, in metric tonnes
                        (present in 1355/2209 records; always negative = CO₂ saved)
  material            — corrugated_cardboard | kraft_paper | plastic | unknown
  protection_score    — integer 0–3
  protection_evidence — list of strings

Fields intentionally NOT used:
  snapshot_price      — total pack price, not per-unit
  snapshot_weight_value — total pack weight, not per-unit
  reference_dim_weight_lb_139 — dimensional/billable weight, NOT physical mass

Sustainability score:
  NOT calculated. No complete comparable environmental dataset is available
  to produce a scientifically meaningful score. Returning null is correct.
"""

import json
import os
import config

_catalog_cache = None
_catalog_index = None   # sku → record


def _load():
    global _catalog_cache, _catalog_index
    if _catalog_cache is not None:
        return
    with open(config.PACKAGING_CATALOG_PATH, 'r', encoding='utf-8') as f:
        _catalog_cache = json.load(f)
    _catalog_index = {r['sku']: r for r in _catalog_cache if r.get('sku')}


LB_TO_KG = 0.453592   # exact conversion factor


def simulate(
    product_type: str,
    length_cm: float,
    width_cm: float,
    height_cm: float,
    weight_kg: float,
    packaging_sku: str = None,
    packaging_material: str = None,
) -> dict:
    """
    Return simulation metrics for a specific packaging SKU or the best-fit
    package for the given material filter.

    All returned metric values come directly from catalog fields.
    Null is returned when a field is absent — never a fabricated value.
    """
    _load()

    # ── Resolve packaging record ──────────────────────────────────────────────

    pkg = None

    if packaging_sku:
        pkg = _catalog_index.get(packaging_sku)
        if pkg is None:
            return {
                'status': 'error',
                'error': f"SKU '{packaging_sku}' not found in catalog.",
            }

    else:
        # Find best-fit package for the given dimensions + optional material filter
        from services.packaging_recommender import recommend_packaging

        # Convert cm → inches
        pl = length_cm / 2.54
        pw = width_cm  / 2.54
        ph = height_cm / 2.54

        result = recommend_packaging(
            product_l=pl,
            product_w=pw,
            product_h=ph,
            is_fragile=False,
            clearance_fraction=0.10,
            top_n=20,
        )

        candidates = result.get('recommendations', [])

        if not candidates:
            return {
                'status': 'no_fit',
                'error': 'No packaging in the catalog fits these dimensions with 10% clearance.',
                'meta': result.get('meta'),
            }

        # If a material filter is requested, prefer matching records
        if packaging_material and packaging_material.lower() != 'any':
            mat_filter = packaging_material.lower().strip()
            filtered = [c for c in candidates
                        if (c.get('material') or '').lower() == mat_filter]
            if filtered:
                candidates = filtered

        # Pick the top-ranked candidate (lowest unused volume)
        top = candidates[0]
        pkg = _catalog_index.get(top['sku']) if top.get('sku') else None

        if pkg is None:
            return {
                'status': 'error',
                'error': 'Could not resolve catalog record for top recommendation.',
            }

    # ── Extract metrics from catalog record ───────────────────────────────────

    raw_unit_price    = pkg.get('unit_price')
    raw_weight_lb     = pkg.get('package_weight_lb')
    raw_co2           = pkg.get('co2e_recycling_mt')
    raw_material      = pkg.get('material')

    # unit_price: use only if present and positive
    cost_per_unit = None
    if raw_unit_price is not None and raw_unit_price > 0:
        cost_per_unit = round(float(raw_unit_price), 4)

    # package_weight_lb → kg (per-unit physical weight)
    packaging_weight_kg = None
    if raw_weight_lb is not None and raw_weight_lb > 0:
        packaging_weight_kg = round(float(raw_weight_lb) * LB_TO_KG, 5)

    # co2e_recycling_mt: negative = CO₂ saved during recycling
    # Return as-is from catalog; explain sign convention in response
    co2e_recycling_mt = None
    if raw_co2 is not None:
        co2e_recycling_mt = float(raw_co2)

    # material
    material_display = raw_material if raw_material and raw_material != 'unknown' else None

    # ── Build response ────────────────────────────────────────────────────────

    return {
        'status': 'ok',
        'packaging': {
            'sku':              pkg.get('sku'),
            'title':            pkg.get('title'),
            'family':           pkg.get('family'),
            'product_type':     pkg.get('product_type'),
            'length_in':        pkg.get('length_in'),
            'width_in':         pkg.get('width_in'),
            'height_in':        pkg.get('height_in'),
            'material':         material_display,
            'protection_score': pkg.get('protection_score'),
            'protection_evidence': pkg.get('protection_evidence'),
            'canonical_product_url': pkg.get('canonical_product_url'),
        },
        'metrics': {
            'cost_per_unit_usd':    cost_per_unit,
            'packaging_weight_kg':  packaging_weight_kg,
            'co2e_recycling_mt':    co2e_recycling_mt,
            # Sustainability score intentionally not calculated.
            # No complete comparable environmental dataset is available
            # to produce a scientifically meaningful score.
            'sustainability_score': None,
            'sustainability_score_note': (
                'Not calculated. A reproducible sustainability score requires '
                'full lifecycle CO\u2082 data (production + transport + end-of-life) '
                'which is not available in the current catalog.'
            ),
        },
        'data_availability': {
            'cost_per_unit':    cost_per_unit is not None,
            'packaging_weight': packaging_weight_kg is not None,
            'co2_recycling':    co2e_recycling_mt is not None,
        },
        'co2_sign_convention': (
            'co2e_recycling_mt is negative when recycling avoids CO\u2082 emissions '
            '(i.e. a more negative value = more CO\u2082 saved). '
            'Source: Packrift catalog field co2e_recycling_mt.'
        ),
        'weight_source': (
            'packaging_weight_kg is derived from package_weight_lb '
            '(= snapshot_weight_value / pack_quantity from catalog), '
            'converted at 0.453592 kg/lb.'
        ),
    }


def get_catalog_materials() -> dict:
    """Calculate material distribution dynamically from the actual Packrift catalog."""
    _load()
    from collections import Counter
    counts = Counter()
    for r in _catalog_cache:
        mat = (r.get('material') or '').strip().lower()
        if not mat or mat == 'unknown':
            counts['unknown'] += 1
        elif 'corrugated' in mat or 'cardboard' in mat:
            counts['corrugated_cardboard'] += 1
        elif 'plastic' in mat or 'poly' in mat:
            counts['plastic'] += 1
        elif 'kraft' in mat:
            counts['kraft_paper'] += 1
        elif 'paper' in mat:
            counts['paper'] += 1
        else:
            counts['unknown'] += 1

    label_map = {
        'corrugated_cardboard': 'Corrugated Cardboard',
        'plastic': 'Plastic',
        'kraft_paper': 'Kraft Paper',
        'paper': 'Paper',
        'unknown': 'Not Specified',
    }

    materials = [
        {'id': 'corrugated_cardboard', 'label': label_map['corrugated_cardboard'], 'count': counts['corrugated_cardboard']},
        {'id': 'plastic',              'label': label_map['plastic'],              'count': counts['plastic']},
        {'id': 'kraft_paper',          'label': label_map['kraft_paper'],          'count': counts['kraft_paper']},
        {'id': 'unknown',              'label': label_map['unknown'],              'count': counts['unknown']},
    ]

    return {
        'materials': materials,
        'total_records': len(_catalog_cache),
        'note': f"Counts calculated directly from {len(_catalog_cache):,} Packrift catalog records."
    }

