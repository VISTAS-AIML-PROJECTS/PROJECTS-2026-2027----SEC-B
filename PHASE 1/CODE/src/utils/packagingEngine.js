/**
 * packagingEngine.js
 * Wrapture client-side packaging recommendation engine.
 *
 * Works entirely in the browser with plain ES2017 JavaScript.
 * No Node-only APIs, no Python, no pandas, no NumPy.
 *
 * Data sources (fetched from public/data/ at call time):
 *   /data/wrapture_abo_products.json      — ABO product catalog
 *   /data/wrapture_packaging_catalog.json — Packrift packaging catalog
 */

// ---------------------------------------------------------------------------
// Material priority scores (higher = more preferred)
// ---------------------------------------------------------------------------
const MATERIAL_PRIORITY = {
  corrugated_cardboard: 2,
  kraft_paper: 2,
  paper: 2,
  unknown: 1,
  plastic: 0,
};

/** Return the material priority score for a catalog material string.
 *  Null / missing material is treated as unknown (score 1). */
function materialScore(material) {
  if (!material) return MATERIAL_PRIORITY.unknown;
  const key = material.toLowerCase().trim();
  if (key in MATERIAL_PRIORITY) return MATERIAL_PRIORITY[key];
  // Partial matches for common variants
  if (key.includes('corrugated') || key.includes('cardboard')) return 2;
  if (key.includes('kraft') || key.includes('paper')) return 2;
  if (key.includes('plastic') || key.includes('poly')) return 0;
  return MATERIAL_PRIORITY.unknown;
}

// ---------------------------------------------------------------------------
// Volume
// ---------------------------------------------------------------------------

/**
 * calculateVolume(l, w, h)
 * Returns l × w × h.  Returns null if any dimension is null / undefined / ≤ 0.
 *
 * @param {number|null} l
 * @param {number|null} w
 * @param {number|null} h
 * @returns {number|null}
 */
export function calculateVolume(l, w, h) {
  if (l == null || w == null || h == null) return null;
  if (l <= 0 || w <= 0 || h <= 0) return null;
  return l * w * h;
}

// ---------------------------------------------------------------------------
// 3-D rotations
// ---------------------------------------------------------------------------

/**
 * getAllRotations(l, w, h)
 * Returns all 6 unique axis-aligned orientations of a cuboid.
 * Each entry is [a, b, c] where a ≥ b ≥ c is NOT enforced —
 * all permutations are returned so the caller can test every orientation.
 *
 * Duplicate orientations (e.g. a cube) are deduplicated.
 *
 * @param {number} l
 * @param {number} w
 * @param {number} h
 * @returns {Array<[number, number, number]>}
 */
function getAllRotations(l, w, h) {
  const perms = [
    [l, w, h],
    [l, h, w],
    [w, l, h],
    [w, h, l],
    [h, l, w],
    [h, w, l],
  ];
  // Deduplicate by string key
  const seen = new Set();
  return perms.filter(([a, b, c]) => {
    const key = `${a},${b},${c}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

// ---------------------------------------------------------------------------
// Fit check
// ---------------------------------------------------------------------------

/**
 * fitsInPackage(productDims, packageDims, clearanceFraction)
 *
 * Returns the best-fitting rotation result or null if no rotation fits.
 *
 * A rotation [pl, pw, ph] fits inside package [kl, kw, kh] when:
 *   pl × (1 + clearanceFraction) ≤ kl
 *   pw × (1 + clearanceFraction) ≤ kw
 *   ph × (1 + clearanceFraction) ≤ kh
 *
 * "Best" = the rotation that maximises space utilisation (minimises unused volume).
 *
 * @param {{ l: number, w: number, h: number }} productDims
 * @param {{ l: number, w: number, h: number }} packageDims
 * @param {number} clearanceFraction  e.g. 0.10 for 10 %
 * @returns {{
 *   fits: boolean,
 *   rotation: [number, number, number] | null,
 *   productVolume: number | null,
 *   packageVolume: number | null,
 *   unusedVolume: number | null,
 *   spaceUtilization: number | null,   // 0–1
 *   minClearancePct: number | null,    // smallest clearance across 3 axes, as %
 *   avgClearancePct: number | null,    // average clearance across 3 axes, as %
 * }}
 */
function fitsInPackage(productDims, packageDims, clearanceFraction = 0.10) {
  const { l: pl, w: pw, h: ph } = productDims;
  const { l: kl, w: kw, h: kh } = packageDims;

  const noFit = {
    fits: false,
    rotation: null,
    productVolume: null,
    packageVolume: null,
    unusedVolume: null,
    spaceUtilization: null,
    minClearancePct: null,
    avgClearancePct: null,
  };

  if (!pl || !pw || !ph || !kl || !kw || !kh) return noFit;
  if (pl <= 0 || pw <= 0 || ph <= 0) return noFit;
  if (kl <= 0 || kw <= 0 || kh <= 0) return noFit;

  const factor = 1 + clearanceFraction;
  const rotations = getAllRotations(pl, pw, ph);
  const packageVol = calculateVolume(kl, kw, kh);

  let best = null;

  for (const [a, b, c] of rotations) {
    if (a * factor <= kl && b * factor <= kw && c * factor <= kh) {
      const productVol = calculateVolume(a, b, c); // same as pl*pw*ph
      const unused = packageVol - productVol;
      const utilization = productVol / packageVol;

      // Per-axis clearance as fraction of product dimension
      const clA = (kl - a) / a;
      const clB = (kw - b) / b;
      const clC = (kh - c) / c;
      const minCl = Math.min(clA, clB, clC);
      const avgCl = (clA + clB + clC) / 3;

      if (best === null || unused < best.unusedVolume) {
        best = {
          fits: true,
          rotation: [a, b, c],
          productVolume: productVol,
          packageVolume: packageVol,
          unusedVolume: unused,
          spaceUtilization: utilization,
          minClearancePct: minCl * 100,
          avgClearancePct: avgCl * 100,
        };
      }
    }
  }

  return best !== null ? best : noFit;
}

// ---------------------------------------------------------------------------
// Best rotation (exported helper)
// ---------------------------------------------------------------------------

/**
 * getBestRotation(productL, productW, productH, packageL, packageW, packageH, clearanceFraction)
 *
 * Returns the [l, w, h] rotation of the product that fits best inside the
 * given package, or null if no rotation fits.
 *
 * @param {number} productL
 * @param {number} productW
 * @param {number} productH
 * @param {number} packageL
 * @param {number} packageW
 * @param {number} packageH
 * @param {number} [clearanceFraction=0.10]
 * @returns {[number, number, number] | null}
 */
export function getBestRotation(
  productL, productW, productH,
  packageL, packageW, packageH,
  clearanceFraction = 0.10
) {
  const result = fitsInPackage(
    { l: productL, w: productW, h: productH },
    { l: packageL, w: packageW, h: packageH },
    clearanceFraction
  );
  return result.fits ? result.rotation : null;
}

// ---------------------------------------------------------------------------
// Ranking comparator
// ---------------------------------------------------------------------------

/**
 * compareRecommendations(a, b)
 *
 * Ranking priority (ascending = better):
 *   1. Lowest unused volume
 *   2. Higher protection score
 *   3. Higher material priority score
 *   4. Lower verified unit price (null prices rank last)
 */
function compareRecommendations(a, b) {
  // 1. Unused volume — lower is better
  const unusedDiff = a.unusedVolume - b.unusedVolume;
  if (Math.abs(unusedDiff) > 0.001) return unusedDiff;

  // 2. Protection score — higher is better
  const protDiff = (b.protection_score ?? 0) - (a.protection_score ?? 0);
  if (protDiff !== 0) return protDiff;

  // 3. Material priority — higher is better
  const matDiff = materialScore(b.material) - materialScore(a.material);
  if (matDiff !== 0) return matDiff;

  // 4. Unit price — lower is better; null ranks last
  const aPrice = a.unit_price;
  const bPrice = b.unit_price;
  if (aPrice == null && bPrice == null) return 0;
  if (aPrice == null) return 1;   // a ranks worse
  if (bPrice == null) return -1;  // b ranks worse
  return aPrice - bPrice;
}

// ---------------------------------------------------------------------------
// Main engine
// ---------------------------------------------------------------------------

/**
 * recommendPackaging(options)
 *
 * Fetches the packaging catalog from /data/wrapture_packaging_catalog.json
 * (or uses a pre-loaded catalog passed via options.catalog) and returns a
 * ranked list of suitable packaging options for the given product.
 *
 * @param {{
 *   productL: number,          // product length in inches
 *   productW: number,          // product width in inches
 *   productH: number,          // product height in inches
 *   isFragile?: boolean,       // default false
 *   clearanceFraction?: number,// default 0.10
 *   catalog?: Array,           // pre-loaded packaging catalog (optional)
 *   topN?: number,             // max results to return (default 10)
 * }} options
 *
 * @returns {Promise<{
 *   status: 'RECOMMENDED' | 'NO_PHYSICAL_FIT' | 'FIT_BUT_PROTECTION_UNVERIFIED',
 *   recommendations: Array,
 *   meta: {
 *     productL: number,
 *     productW: number,
 *     productH: number,
 *     productVolume: number | null,
 *     isFragile: boolean,
 *     clearanceFraction: number,
 *     totalCandidatesEvaluated: number,
 *     totalPhysicalFits: number,
 *   }
 * }>}
 */
export async function recommendPackaging({
  productL,
  productW,
  productH,
  isFragile = false,
  clearanceFraction = 0.10,
  catalog = null,
  topN = 10,
}) {
  // ------------------------------------------------------------------
  // 1. Load catalog if not pre-supplied
  // ------------------------------------------------------------------
  let packagingCatalog = catalog;
  if (!packagingCatalog) {
    const response = await fetch('/data/wrapture_packaging_catalog.json');
    if (!response.ok) {
      throw new Error(
        `Failed to fetch packaging catalog: HTTP ${response.status}`
      );
    }
    packagingCatalog = await response.json();
  }

  const productVolume = calculateVolume(productL, productW, productH);

  const meta = {
    productL,
    productW,
    productH,
    productVolume,
    isFragile,
    clearanceFraction,
    totalCandidatesEvaluated: packagingCatalog.length,
    totalPhysicalFits: 0,
  };

  // ------------------------------------------------------------------
  // 2. Evaluate every packaging record
  // ------------------------------------------------------------------
  const physicalFits = [];

  for (const pkg of packagingCatalog) {
    const pkgL = pkg.length_in;
    const pkgW = pkg.width_in;
    const pkgH = pkg.height_in;

    // Skip records with missing package dimensions
    if (pkgL == null || pkgW == null || pkgH == null) continue;
    if (pkgL <= 0 || pkgW <= 0 || pkgH <= 0) continue;

    const fitResult = fitsInPackage(
      { l: productL, w: productW, h: productH },
      { l: pkgL, w: pkgW, h: pkgH },
      clearanceFraction
    );

    if (!fitResult.fits) continue;

    physicalFits.push({
      // Identity
      sku: pkg.sku ?? null,
      title: pkg.title ?? null,
      family: pkg.family ?? null,
      product_type: pkg.product_type ?? null,

      // Packaging dimensions (from catalog — not invented)
      package_length_in: pkgL,
      package_width_in: pkgW,
      package_height_in: pkgH,

      // Protection (preserved as-is; null if missing)
      material: pkg.material ?? null,
      protection_score: pkg.protection_score ?? null,
      protection_evidence: pkg.protection_evidence ?? null,

      // Pricing (null if missing — never invented)
      pack_quantity: pkg.pack_quantity ?? null,
      unit_price: pkg.unit_price ?? null,
      snapshot_price: pkg.snapshot_price ?? null,

      // Environmental (null if missing — never invented)
      co2e_recycling_mt: pkg.co2e_recycling_mt ?? null,

      // Reference
      canonical_product_url: pkg.canonical_product_url ?? null,

      // Fit geometry
      productVolume: fitResult.productVolume,
      packageVolume: fitResult.packageVolume,
      unusedVolume: fitResult.unusedVolume,
      spaceUtilization: fitResult.spaceUtilization,
      minClearancePct: fitResult.minClearancePct,
      avgClearancePct: fitResult.avgClearancePct,
      selectedRotation: fitResult.rotation,
    });
  }

  meta.totalPhysicalFits = physicalFits.length;

  // ------------------------------------------------------------------
  // 3. No physical fit at all
  // ------------------------------------------------------------------
  if (physicalFits.length === 0) {
    return {
      status: 'NO_PHYSICAL_FIT',
      recommendations: [],
      meta,
    };
  }

  // ------------------------------------------------------------------
  // 4. Fragility filter
  // ------------------------------------------------------------------
  let candidates = physicalFits;

  if (isFragile) {
    const protectedFits = physicalFits.filter(
      (p) => p.protection_score != null && p.protection_score >= 2
    );

    if (protectedFits.length === 0) {
      // Physical fits exist but none satisfy the fragile protection requirement
      // Return the physical fits ranked normally so the caller can still inspect
      // them, but signal that protection is unverified.
      const ranked = physicalFits
        .sort(compareRecommendations)
        .slice(0, topN)
        .map((rec, i) => ({
          rank: i + 1,
          ...rec,
          reason:
            'Physically fits but protection_score < 2; ' +
            'fragile protection unverified for this package.',
        }));

      return {
        status: 'FIT_BUT_PROTECTION_UNVERIFIED',
        recommendations: ranked,
        meta,
      };
    }

    candidates = protectedFits;
  }

  // ------------------------------------------------------------------
  // 5. Rank and return
  // ------------------------------------------------------------------
  const ranked = candidates
    .sort(compareRecommendations)
    .slice(0, topN)
    .map((rec, i) => {
      const utilPct = rec.spaceUtilization != null
        ? `${(rec.spaceUtilization * 100).toFixed(1)}%`
        : 'unknown';

      const pricePart = rec.unit_price != null
        ? `unit price $${rec.unit_price.toFixed(2)}`
        : 'price unavailable';

      const matPart = rec.material
        ? `material: ${rec.material}`
        : 'material: unknown';

      return {
        rank: i + 1,
        sku: rec.sku,
        title: rec.title,
        family: rec.family,
        material: rec.material,
        protection_score: rec.protection_score,
        protection_evidence: rec.protection_evidence,
        package_length_in: rec.package_length_in,
        package_width_in: rec.package_width_in,
        package_height_in: rec.package_height_in,
        product_volume_in3: rec.productVolume,
        package_volume_in3: rec.packageVolume,
        unused_volume_in3: rec.unusedVolume,
        space_utilization: rec.spaceUtilization,
        min_clearance_pct: rec.minClearancePct,
        avg_clearance_pct: rec.avgClearancePct,
        selected_rotation: rec.selectedRotation,
        pack_quantity: rec.pack_quantity,
        unit_price: rec.unit_price,
        snapshot_price: rec.snapshot_price,
        co2e_recycling_mt: rec.co2e_recycling_mt,
        canonical_product_url: rec.canonical_product_url,
        reason:
          `Rank ${i + 1}: space utilization ${utilPct}, ` +
          `${matPart}, protection score ${rec.protection_score ?? 'unknown'}, ` +
          `${pricePart}.`,
      };
    });

  return {
    status: 'RECOMMENDED',
    recommendations: ranked,
    meta,
  };
}
