"""
services/packaging_recommender.py

Python port of src/utils/packagingEngine.js.
Uses the same real Packrift catalog and the same ranking logic.
Does NOT invent values.
"""
import json
import os
from typing import Optional

import config

# ── Material priority (mirrors JS) ────────────────────────────────────────────
MATERIAL_PRIORITY = {
    'corrugated_cardboard': 2,
    'kraft_paper': 2,
    'paper': 2,
    'unknown': 1,
    'plastic': 0,
}

def _material_score(material: Optional[str]) -> int:
    if not material:
        return MATERIAL_PRIORITY['unknown']
    key = material.lower().strip()
    if key in MATERIAL_PRIORITY:
        return MATERIAL_PRIORITY[key]
    if 'corrugated' in key or 'cardboard' in key:
        return 2
    if 'kraft' in key or 'paper' in key:
        return 2
    if 'plastic' in key or 'poly' in key:
        return 0
    return MATERIAL_PRIORITY['unknown']


def _get_all_rotations(l, w, h):
    perms = [
        (l, w, h), (l, h, w), (w, l, h),
        (w, h, l), (h, l, w), (h, w, l),
    ]
    seen = set()
    result = []
    for p in perms:
        key = f"{p[0]},{p[1]},{p[2]}"
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result


def _fits_in_package(product_dims, package_dims, clearance=0.10):
    pl, pw, ph = product_dims
    kl, kw, kh = package_dims

    if not all([pl, pw, ph, kl, kw, kh]):
        return None
    if any(x <= 0 for x in [pl, pw, ph, kl, kw, kh]):
        return None

    factor = 1 + clearance
    package_vol = kl * kw * kh
    best = None

    for a, b, c in _get_all_rotations(pl, pw, ph):
        if a * factor <= kl and b * factor <= kw and c * factor <= kh:
            product_vol = a * b * c
            unused = package_vol - product_vol
            utilization = product_vol / package_vol
            cl_a = (kl - a) / a
            cl_b = (kw - b) / b
            cl_c = (kh - c) / c
            min_cl = min(cl_a, cl_b, cl_c)
            avg_cl = (cl_a + cl_b + cl_c) / 3

            if best is None or unused < best['unused_volume']:
                best = {
                    'fits': True,
                    'rotation': [a, b, c],
                    'product_volume': product_vol,
                    'package_volume': package_vol,
                    'unused_volume': unused,
                    'space_utilization': utilization,
                    'min_clearance_pct': min_cl * 100,
                    'avg_clearance_pct': avg_cl * 100,
                }

    return best


def _compare_key(rec):
    """Sort key: lower unused_volume, higher protection, higher material, lower price."""
    price = rec['unit_price'] if rec['unit_price'] is not None else float('inf')
    return (
        rec['unused_volume'],
        -(rec['protection_score'] or 0),
        -_material_score(rec['material']),
        price,
    )


# ── Catalog loader (cached) ───────────────────────────────────────────────────
_catalog_cache = None

def load_catalog():
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache
    with open(config.PACKAGING_CATALOG_PATH, 'r', encoding='utf-8') as f:
        _catalog_cache = json.load(f)
    return _catalog_cache


# ── Main recommend function ───────────────────────────────────────────────────
def recommend_packaging(
    product_l: float,
    product_w: float,
    product_h: float,
    is_fragile: bool = False,
    clearance_fraction: float = 0.10,
    top_n: int = 10,
):
    """
    Returns the same structure as the JS packagingEngine.
    All values come from the real Packrift catalog.
    load_capacity_verified is always False — catalog does not provide it.
    """
    catalog = load_catalog()

    meta = {
        'productL': product_l,
        'productW': product_w,
        'productH': product_h,
        'productVolume': product_l * product_w * product_h if all([product_l, product_w, product_h]) else None,
        'isFragile': is_fragile,
        'clearanceFraction': clearance_fraction,
        'totalCandidatesEvaluated': len(catalog),
        'totalPhysicalFits': 0,
        'load_capacity_verified': False,
    }

    physical_fits = []

    for pkg in catalog:
        pkg_l = pkg.get('length_in')
        pkg_w = pkg.get('width_in')
        pkg_h = pkg.get('height_in')

        if pkg_l is None or pkg_w is None or pkg_h is None:
            continue
        if pkg_l <= 0 or pkg_w <= 0 or pkg_h <= 0:
            continue

        fit = _fits_in_package(
            (product_l, product_w, product_h),
            (pkg_l, pkg_w, pkg_h),
            clearance_fraction,
        )
        if not fit:
            continue

        physical_fits.append({
            'sku': pkg.get('sku'),
            'title': pkg.get('title'),
            'family': pkg.get('family'),
            'product_type': pkg.get('product_type'),
            'package_length_in': pkg_l,
            'package_width_in': pkg_w,
            'package_height_in': pkg_h,
            'material': pkg.get('material'),
            'protection_score': pkg.get('protection_score'),
            'protection_evidence': pkg.get('protection_evidence'),
            'pack_quantity': pkg.get('pack_quantity'),
            'unit_price': pkg.get('unit_price'),
            'snapshot_price': pkg.get('snapshot_price'),
            'co2e_recycling_mt': pkg.get('co2e_recycling_mt'),
            'canonical_product_url': pkg.get('canonical_product_url'),
            'unused_volume': fit['unused_volume'],
            'space_utilization': fit['space_utilization'],
            'min_clearance_pct': fit['min_clearance_pct'],
            'avg_clearance_pct': fit['avg_clearance_pct'],
            'selected_rotation': fit['rotation'],
            'product_volume': fit['product_volume'],
            'package_volume': fit['package_volume'],
        })

    meta['totalPhysicalFits'] = len(physical_fits)

    if not physical_fits:
        return {'status': 'NO_PHYSICAL_FIT', 'recommendations': [], 'meta': meta}

    candidates = physical_fits

    if is_fragile:
        protected = [p for p in physical_fits if p.get('protection_score') and p['protection_score'] >= 2]
        if not protected:
            ranked = sorted(physical_fits, key=_compare_key)[:top_n]
            return {
                'status': 'FIT_BUT_PROTECTION_UNVERIFIED',
                'recommendations': [dict(rank=i+1, **r) for i, r in enumerate(ranked)],
                'meta': meta,
            }
        candidates = protected

    ranked = sorted(candidates, key=_compare_key)[:top_n]
    return {
        'status': 'RECOMMENDED',
        'recommendations': [dict(rank=i+1, **r) for i, r in enumerate(ranked)],
        'meta': meta,
    }
