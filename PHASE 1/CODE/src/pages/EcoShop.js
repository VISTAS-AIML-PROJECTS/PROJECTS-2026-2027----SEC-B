import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Package,
  ExternalLink,
  Filter,
  X,
  Search,
} from 'lucide-react';

/**
 * EcoShop — Real Packrift packaging catalog browser.
 *
 * Data source: /data/wrapture_packaging_catalog.json (2,209 records)
 * Displays real catalog fields only. No invented reviews, ratings, stock, or discounts.
 * Supports deep-linking via ?sku=XYZ to highlight exact recommendations from scanning.
 */

const FAMILY_LABELS = {
  boxes: 'Boxes',
  mailers: 'Mailers',
  poly_bags: 'Poly Bags',
};

const MATERIAL_LABELS = {
  corrugated_cardboard: 'Corrugated Cardboard',
  kraft_paper: 'Kraft Paper',
  paper: 'Paper',
  plastic: 'Plastic',
  unknown: 'Not Specified',
};

const PAGE_SIZE = 24;

function formatDimensions(item) {
  const { length_in, width_in, height_in } = item;
  if (length_in == null && width_in == null && height_in == null) return null;
  const parts = [length_in, width_in, height_in].filter((v) => v != null);
  return parts.map((v) => Number(v).toFixed(2)).join(' × ') + ' in';
}

function calculatePackageVolume(item) {
  const { length_in, width_in, height_in } = item;
  if (!length_in || !width_in || !height_in) return Infinity;
  return Number(length_in) * Number(width_in) * Number(height_in);
}

function formatCo2(val) {
  if (val == null) return null;
  // catalog value is negative (CO2 avoided during recycling scenario)
  const kg = Math.abs(val) * 1000;
  return kg.toFixed(4);
}

const EcoShop = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const deepLinkedSku = searchParams.get('sku')?.trim() || '';

  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilterModal, setShowFilterModal] = useState(false);

  // Active filters
  const [filterFamily, setFilterFamily] = useState('');
  const [filterMaterial, setFilterMaterial] = useState('');
  const [filterProtection, setFilterProtection] = useState(''); // 'available' | 'none'
  const [filterMinPrice, setFilterMinPrice] = useState('');
  const [filterMaxPrice, setFilterMaxPrice] = useState('');
  const [sortBy, setSortBy] = useState('recommended');

  const recommendedRef = useRef(null);

  useEffect(() => {
    fetch('/data/wrapture_packaging_catalog.json')
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setCatalog(data);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  // Find deep-linked item if present
  const recommendedProduct = useMemo(() => {
    if (!deepLinkedSku || !catalog.length) return null;
    return catalog.find(
      (p) => (p.sku || '').toLowerCase() === deepLinkedSku.toLowerCase()
    );
  }, [catalog, deepLinkedSku]);

  // Scroll to recommended item when found
  useEffect(() => {
    if (recommendedProduct && recommendedRef.current) {
      recommendedRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [recommendedProduct]);

  // Count active filters
  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filterFamily) count++;
    if (filterMaterial) count++;
    if (filterProtection) count++;
    if (filterMinPrice !== '' || filterMaxPrice !== '') count++;
    if (sortBy !== 'recommended') count++;
    return count;
  }, [filterFamily, filterMaterial, filterProtection, filterMinPrice, filterMaxPrice, sortBy]);

  // Filter & sort logic
  const filtered = useMemo(() => {
    let result = catalog;

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      result = result.filter(
        (p) =>
          (p.title && p.title.toLowerCase().includes(q)) ||
          (p.sku && p.sku.toLowerCase().includes(q)) ||
          (p.product_type && p.product_type.toLowerCase().includes(q)) ||
          (p.material && p.material.toLowerCase().includes(q))
      );
    }

    // Family filter
    if (filterFamily) {
      result = result.filter((p) => p.family === filterFamily);
    }

    // Material filter
    if (filterMaterial) {
      if (filterMaterial === 'unknown') {
        result = result.filter((p) => !p.material || p.material === 'unknown');
      } else {
        result = result.filter((p) => (p.material || '').toLowerCase() === filterMaterial.toLowerCase());
      }
    }

    // Protection evidence filter
    if (filterProtection === 'available') {
      result = result.filter(
        (p) => (p.protection_evidence && p.protection_evidence.length > 0) || (p.protection_score != null && p.protection_score > 0)
      );
    } else if (filterProtection === 'none') {
      result = result.filter(
        (p) => (!p.protection_evidence || p.protection_evidence.length === 0) && (!p.protection_score || p.protection_score === 0)
      );
    }

    // Price range filter
    if (filterMinPrice !== '') {
      const min = parseFloat(filterMinPrice);
      if (!isNaN(min)) {
        result = result.filter((p) => p.unit_price != null && p.unit_price >= min);
      }
    }
    if (filterMaxPrice !== '') {
      const max = parseFloat(filterMaxPrice);
      if (!isNaN(max)) {
        result = result.filter((p) => p.unit_price != null && p.unit_price <= max);
      }
    }

    // Sorting
    const sorted = [...result];
    if (sortBy === 'price_asc') {
      sorted.sort((a, b) => (a.unit_price ?? Infinity) - (b.unit_price ?? Infinity));
    } else if (sortBy === 'volume_asc') {
      sorted.sort((a, b) => calculatePackageVolume(a) - calculatePackageVolume(b));
    } else if (sortBy === 'protection_desc') {
      sorted.sort((a, b) => (b.protection_score ?? 0) - (a.protection_score ?? 0));
    } else if (sortBy === 'co2_saved_desc') {
      // most negative co2e_recycling_mt = most CO2 avoided
      sorted.sort((a, b) => (a.co2e_recycling_mt ?? 0) - (b.co2e_recycling_mt ?? 0));
    }

    return sorted;
  }, [
    catalog,
    searchQuery,
    filterFamily,
    filterMaterial,
    filterProtection,
    filterMinPrice,
    filterMaxPrice,
    sortBy,
  ]);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const resetFilters = () => {
    setFilterFamily('');
    setFilterMaterial('');
    setFilterProtection('');
    setFilterMinPrice('');
    setFilterMaxPrice('');
    setSortBy('recommended');
    setPage(1);
  };

  const clearDeepLink = () => {
    searchParams.delete('sku');
    setSearchParams(searchParams);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] p-6 text-center">
        <div className="w-12 h-12 rounded-2xl bg-surface-container flex items-center justify-center text-primary shadow-xs border border-outline-variant/30 mb-4 animate-pulse">
          <span className="material-symbols-outlined text-[28px] animate-spin">progress_activity</span>
        </div>
        <h2 className="font-serif text-[20px] text-primary font-medium">Loading Packrift Catalog…</h2>
        <p className="font-body-sm text-[13px] text-on-surface-variant mt-1">
          Loading 2,209 verified packaging records
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12 p-6 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-center">
        <span className="material-symbols-outlined text-[32px] mb-2 text-red-500">error</span>
        <h3 className="font-serif text-[18px] font-semibold">Failed to load catalog</h3>
        <p className="text-[13px] mt-1">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded-xl text-[13px] font-medium"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full min-h-full bg-surface pb-safe-nav">
      <div className="flex flex-col w-full px-4 md:px-6 space-y-4 pb-12">
        {/* Editorial Header */}
        <section className="pt-3 flex flex-col gap-1">
          <span className="font-label-caps text-[11px] tracking-[0.2em] text-secondary font-bold uppercase">
            PACKRIFT CATALOG
          </span>
          <h1 className="font-serif text-[28px] md:text-[34px] text-primary font-medium tracking-tight">
            EcoShop Packaging
          </h1>
          <p className="font-body-sm text-[13px] text-on-surface-variant">
            Explore {catalog.length.toLocaleString()} real packaging products with dimensions, unit pricing, and EPA WARM recycling metrics.
          </p>
        </section>

        {/* ── HIGHLIGHTED RECOMMENDED PRODUCT (from scan flow) ── */}
        {recommendedProduct && (
          <section ref={recommendedRef} className="pt-1">
            <div className="relative rounded-2xl p-5 bg-surface-container-high border-2 border-secondary shadow-md overflow-hidden">
              <div className="flex items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <span className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-surface shadow-xs">
                    <span className="material-symbols-outlined text-[18px] text-secondary-fixed">auto_awesome</span>
                  </span>
                  <div>
                    <span className="font-label-caps text-[10px] tracking-wider uppercase text-secondary font-bold block">
                      RECOMMENDED FOR YOUR PRODUCT
                    </span>
                    <span className="font-label-mono-data text-[12px] font-semibold text-primary">
                      Matched via AI Scan &amp; Sizing Engine
                    </span>
                  </div>
                </div>
                <button
                  onClick={clearDeepLink}
                  aria-label="Dismiss recommendation highlight"
                  className="p-1 rounded-full text-on-surface-variant hover:bg-surface-container hover:text-primary transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Card body */}
              <div className="bg-surface rounded-xl p-4 border border-outline-variant/30 shadow-xs flex flex-col md:flex-row gap-4 justify-between items-start md:items-center">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <span className="font-label-mono-data text-[11px] px-2.5 py-0.5 rounded-full bg-surface-container text-primary font-semibold border border-outline-variant/30">
                      SKU: {recommendedProduct.sku}
                    </span>
                    {recommendedProduct.family && (
                      <span className="font-label-caps text-[10px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-bold uppercase tracking-wider">
                        {FAMILY_LABELS[recommendedProduct.family] || recommendedProduct.family}
                      </span>
                    )}
                    {recommendedProduct.material && recommendedProduct.material !== 'unknown' && (
                      <span className="font-label-caps text-[10px] px-2 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-bold uppercase tracking-wider">
                        {MATERIAL_LABELS[recommendedProduct.material] || recommendedProduct.material}
                      </span>
                    )}
                  </div>
                  <h3 className="font-serif text-[18px] text-primary font-medium leading-snug">
                    {recommendedProduct.title || 'Packaging Item'}
                  </h3>

                  {/* Metadata line */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-outline-variant/20 text-xs">
                    <div>
                      <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Dimensions</span>
                      <span className="font-label-mono-data font-bold text-primary">
                        {formatDimensions(recommendedProduct) || 'Not specified'}
                      </span>
                    </div>
                    <div>
                      <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Pack Quantity</span>
                      <span className="font-label-mono-data font-medium text-primary">
                        {recommendedProduct.pack_quantity ? `${recommendedProduct.pack_quantity} units` : 'Not specified'}
                      </span>
                    </div>
                    <div>
                      <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Protection</span>
                      <span className="font-body-sm font-medium text-primary truncate block">
                        {recommendedProduct.protection_evidence?.length
                          ? recommendedProduct.protection_evidence.join(', ')
                          : recommendedProduct.protection_score != null
                          ? `Score: ${recommendedProduct.protection_score}`
                          : 'Not specified'}
                      </span>
                    </div>
                    <div>
                      <span className="text-on-surface-variant block text-[10px] font-label-caps uppercase">Recycling CO₂e</span>
                      <span className="font-label-mono-data font-semibold text-secondary truncate block">
                        {formatCo2(recommendedProduct.co2e_recycling_mt)
                          ? `${formatCo2(recommendedProduct.co2e_recycling_mt)} kg avoided*`
                          : 'Not available'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Pricing & Link */}
                <div className="w-full md:w-auto flex md:flex-col items-center md:items-end justify-between gap-3 shrink-0 pt-2 md:pt-0">
                  <div className="text-left md:text-right">
                    <span className="font-serif text-[22px] font-bold text-primary block leading-none">
                      {recommendedProduct.unit_price != null
                        ? `$${Number(recommendedProduct.unit_price).toFixed(2)}`
                        : 'Price unavailable'}
                    </span>
                    <span className="font-body-sm text-[11px] text-on-surface-variant">per unit</span>
                  </div>

                  {recommendedProduct.canonical_product_url ? (
                    <a
                      href={recommendedProduct.canonical_product_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-4 py-2.5 bg-primary text-surface rounded-xl text-[12px] font-semibold tracking-wide flex items-center gap-1.5 hover:bg-primary-container transition-colors shadow-xs"
                    >
                      <span>View on Packrift</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  ) : (
                    <span className="text-[11px] text-on-surface-variant italic">Catalog item</span>
                  )}
                </div>
              </div>
            </div>
          </section>
        )}

        {/* ── SEARCH & FILTER CONTROLS ── */}
        <section className="flex flex-col sm:flex-row gap-2.5 pt-1">
          {/* Search bar */}
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-on-surface-variant/60 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search by title, SKU, or material…"
              className="w-full bg-surface-container-low border border-outline-variant/40 rounded-xl pl-10 pr-4 py-2.5 text-[13px] text-primary placeholder-on-surface-variant/60 focus:outline-none focus:border-secondary transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant/60 hover:text-primary"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Filter button with badge */}
          <button
            onClick={() => setShowFilterModal(true)}
            className={`py-2.5 px-4 rounded-xl text-[13px] font-medium flex items-center justify-center gap-2 border transition-colors cursor-pointer ${
              activeFilterCount > 0
                ? 'bg-primary text-surface border-primary shadow-xs'
                : 'bg-surface-container-low text-primary border-outline-variant/40 hover:bg-surface-container'
            }`}
          >
            <Filter className="w-4 h-4" />
            <span>Filters {activeFilterCount > 0 ? `(${activeFilterCount})` : ''}</span>
          </button>
        </section>

        {/* Active Filter Chips */}
        {activeFilterCount > 0 && (
          <section className="flex flex-wrap items-center gap-1.5 pt-0.5">
            <span className="text-[11px] font-label-caps uppercase text-on-surface-variant mr-1">Active:</span>
            {filterFamily && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container text-xs text-primary border border-outline-variant/30">
                Family: {FAMILY_LABELS[filterFamily] || filterFamily}
                <button onClick={() => setFilterFamily('')}><X className="w-3 h-3" /></button>
              </span>
            )}
            {filterMaterial && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container text-xs text-primary border border-outline-variant/30">
                Material: {MATERIAL_LABELS[filterMaterial] || filterMaterial}
                <button onClick={() => setFilterMaterial('')}><X className="w-3 h-3" /></button>
              </span>
            )}
            {filterProtection && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container text-xs text-primary border border-outline-variant/30">
                Protection: {filterProtection === 'available' ? 'Available' : 'None'}
                <button onClick={() => setFilterProtection('')}><X className="w-3 h-3" /></button>
              </span>
            )}
            {(filterMinPrice || filterMaxPrice) && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container text-xs text-primary border border-outline-variant/30">
                Price: {filterMinPrice ? `$${filterMinPrice}` : '$0'} - {filterMaxPrice ? `$${filterMaxPrice}` : '∞'}
                <button onClick={() => { setFilterMinPrice(''); setFilterMaxPrice(''); }}><X className="w-3 h-3" /></button>
              </span>
            )}
            {sortBy !== 'recommended' && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-surface-container text-xs text-primary border border-outline-variant/30">
                Sort: {sortBy}
                <button onClick={() => setSortBy('recommended')}><X className="w-3 h-3" /></button>
              </span>
            )}
            <button
              onClick={resetFilters}
              className="text-[11px] text-secondary font-semibold hover:underline ml-1 cursor-pointer"
            >
              Clear all
            </button>
          </section>
        )}

        {/* Results Count */}
        <div className="flex items-center justify-between pt-1 px-1">
          <span className="font-label-caps text-[11px] text-on-surface-variant font-medium">
            Showing {filtered.length.toLocaleString()} matching packaging records
          </span>
          {totalPages > 1 && (
            <span className="font-label-mono-data text-[11px] text-on-surface-variant">
              Page {page} of {totalPages}
            </span>
          )}
        </div>

        {/* ── PRODUCT CARDS GRID ── */}
        {pageItems.length === 0 ? (
          <div className="rounded-2xl p-12 text-center bg-surface-container-low border border-outline-variant/30">
            <Package className="w-12 h-12 text-on-surface-variant/40 mx-auto mb-3" />
            <h3 className="font-serif text-[18px] text-primary font-medium">No matching packaging found</h3>
            <p className="font-body-sm text-[13px] text-on-surface-variant mt-1 max-w-sm mx-auto">
              Try broadening your search query or clearing some of your active filters.
            </p>
            <button
              onClick={resetFilters}
              className="mt-4 px-4 py-2 bg-primary text-surface rounded-xl text-[13px] font-medium"
            >
              Clear All Filters
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pageItems.map((product) => {
              const dims = formatDimensions(product);
              const co2kg = formatCo2(product.co2e_recycling_mt);
              const matLabel =
                MATERIAL_LABELS[product.material] ||
                product.material ||
                'Not specified';

              return (
                <div
                  key={product.sku}
                  className="bg-surface-container-low rounded-2xl p-4 border border-outline-variant/30 shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between"
                >
                  <div>
                    {/* Top Chips Row */}
                    <div className="flex items-center justify-between gap-1 mb-2">
                      <span className="font-label-mono-data text-[10px] px-2 py-0.5 rounded-full bg-surface text-on-surface-variant font-medium border border-outline-variant/20 truncate">
                        {product.sku}
                      </span>
                      <div className="flex items-center gap-1 shrink-0">
                        {product.family && (
                          <span className="font-label-caps text-[9px] px-2 py-0.5 rounded-full bg-primary/10 text-primary font-bold uppercase tracking-wider">
                            {FAMILY_LABELS[product.family] || product.family}
                          </span>
                        )}
                        {product.material && (
                          <span className="font-label-caps text-[9px] px-2 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-bold uppercase tracking-wider">
                            {matLabel}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Main Title */}
                    <h3 className="font-serif text-[16px] text-primary font-medium leading-snug line-clamp-2 mb-3">
                      {product.title || 'Packaging Item'}
                    </h3>

                    {/* Price Hero */}
                    <div className="mb-3.5 pb-3 border-b border-outline-variant/20 flex items-baseline justify-between">
                      <div>
                        <span className="font-serif text-[22px] font-bold text-primary leading-none">
                          {product.unit_price != null
                            ? `$${Number(product.unit_price).toFixed(2)}`
                            : 'Price unavailable'}
                        </span>
                        {product.unit_price != null && (
                          <span className="font-body-sm text-[11px] text-on-surface-variant ml-1">/ unit</span>
                        )}
                      </div>
                      {product.pack_quantity != null && (
                        <span className="font-label-mono-data text-[11px] text-on-surface-variant">
                          Pack of {product.pack_quantity}
                        </span>
                      )}
                    </div>

                    {/* Specifications List */}
                    <div className="space-y-1.5 text-xs">
                      {dims && (
                        <div className="flex items-center justify-between text-on-surface-variant">
                          <span className="text-[11px] font-label-caps uppercase">Dimensions:</span>
                          <span className="font-label-mono-data font-semibold text-primary">{dims}</span>
                        </div>
                      )}

                      {product.protection_evidence?.length ? (
                        <div className="flex items-start justify-between text-on-surface-variant gap-2">
                          <span className="text-[11px] font-label-caps uppercase shrink-0">Protection:</span>
                          <span className="font-body-sm text-right text-primary truncate max-w-[65%]">
                            {product.protection_evidence.join(', ')}
                          </span>
                        </div>
                      ) : product.protection_score != null && product.protection_score > 0 ? (
                        <div className="flex items-center justify-between text-on-surface-variant">
                          <span className="text-[11px] font-label-caps uppercase">Protection Score:</span>
                          <span className="font-body-sm font-semibold text-primary">
                            Level {product.protection_score} / 3
                          </span>
                        </div>
                      ) : null}

                      {co2kg != null && (
                        <div className="flex items-center justify-between text-on-surface-variant">
                          <span className="text-[11px] font-label-caps uppercase">Recycling CO₂e:</span>
                          <span className="font-label-mono-data font-medium text-secondary">
                            {co2kg} kg avoided*
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action Link */}
                  <div className="mt-4 pt-3 border-t border-outline-variant/20 flex items-center justify-between">
                    {product.canonical_product_url ? (
                      <a
                        href={product.canonical_product_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full py-2 px-3 rounded-xl bg-surface border border-outline-variant/30 text-primary font-body-sm text-[12px] font-semibold flex items-center justify-center gap-1.5 hover:bg-surface-container transition-colors shadow-2xs"
                      >
                        <span>View on Packrift</span>
                        <ExternalLink className="w-3.5 h-3.5 text-secondary" />
                      </a>
                    ) : (
                      <span className="text-[11px] text-on-surface-variant/60 italic w-full text-center py-1">
                        Catalog reference item
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── PAGINATION ── */}
        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-3 pt-6 pb-2">
            <button
              disabled={page === 1}
              onClick={() => {
                setPage((p) => Math.max(1, p - 1));
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className="py-2 px-4 rounded-xl bg-surface-container-low border border-outline-variant/30 text-[13px] font-medium text-primary hover:bg-surface-container disabled:opacity-40 disabled:pointer-events-none transition-colors"
            >
              ← Previous
            </button>
            <span className="font-label-mono-data text-[12px] text-on-surface-variant font-medium">
              Page {page} of {totalPages}
            </span>
            <button
              disabled={page === totalPages}
              onClick={() => {
                setPage((p) => Math.min(totalPages, p + 1));
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              className="py-2 px-4 rounded-xl bg-surface-container-low border border-outline-variant/30 text-[13px] font-medium text-primary hover:bg-surface-container disabled:opacity-40 disabled:pointer-events-none transition-colors"
            >
              Next →
            </button>
          </div>
        )}

        {/* EPA WARM note */}
        <p className="text-center font-body-sm text-[11px] text-on-surface-variant/70 pt-2">
          * Modeled recycling CO₂e factor based on EPA WARM end-of-life recycling avoided emissions. No fabricated values.
        </p>
      </div>

      {/* ── FILTER & SORT BOTTOM SHEET / MODAL ── */}
      {showFilterModal && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-xs p-0 sm:p-4">
          <div className="w-full sm:max-w-lg bg-surface rounded-t-3xl sm:rounded-3xl border border-outline-variant/30 shadow-2xl max-h-[85vh] flex flex-col overflow-hidden animate-in slide-in-from-bottom duration-200">
            {/* Modal Header */}
            <div className="px-5 py-4 border-b border-outline-variant/20 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-secondary" />
                <h3 className="font-serif text-[18px] text-primary font-medium">Filter &amp; Sort Products</h3>
              </div>
              <button
                onClick={() => setShowFilterModal(false)}
                className="p-1 rounded-full text-on-surface-variant hover:bg-surface-container text-primary"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-5 space-y-5 overflow-y-auto flex-1 text-sm">
              {/* Material Filter */}
              <div>
                <label className="font-label-caps text-[10px] uppercase tracking-wider text-secondary font-bold block mb-2">
                  Material
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: '', label: 'All Materials' },
                    { id: 'corrugated_cardboard', label: 'Corrugated Cardboard' },
                    { id: 'kraft_paper', label: 'Kraft Paper' },
                    { id: 'paper', label: 'Paper' },
                    { id: 'plastic', label: 'Plastic' },
                    { id: 'unknown', label: 'Not Specified' },
                  ].map((mat) => (
                    <button
                      key={mat.id}
                      onClick={() => setFilterMaterial(mat.id)}
                      className={`py-2 px-3 rounded-xl text-[12px] font-medium text-left border transition-colors ${
                        filterMaterial === mat.id
                          ? 'bg-primary text-surface border-primary font-semibold'
                          : 'bg-surface-container-low text-primary border-outline-variant/30 hover:bg-surface-container'
                      }`}
                    >
                      {mat.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Packaging Family */}
              <div>
                <label className="font-label-caps text-[10px] uppercase tracking-wider text-secondary font-bold block mb-2">
                  Packaging Family
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: '', label: 'All Families' },
                    { id: 'boxes', label: 'Boxes' },
                    { id: 'mailers', label: 'Mailers' },
                    { id: 'poly_bags', label: 'Poly Bags' },
                  ].map((fam) => (
                    <button
                      key={fam.id}
                      onClick={() => setFilterFamily(fam.id)}
                      className={`py-2 px-3 rounded-xl text-[12px] font-medium text-left border transition-colors ${
                        filterFamily === fam.id
                          ? 'bg-primary text-surface border-primary font-semibold'
                          : 'bg-surface-container-low text-primary border-outline-variant/30 hover:bg-surface-container'
                      }`}
                    >
                      {fam.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Protection Evidence */}
              <div>
                <label className="font-label-caps text-[10px] uppercase tracking-wider text-secondary font-bold block mb-2">
                  Protection Evidence
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: '', label: 'All' },
                    { id: 'available', label: 'Available' },
                    { id: 'none', label: 'Not Available' },
                  ].map((prot) => (
                    <button
                      key={prot.id}
                      onClick={() => setFilterProtection(prot.id)}
                      className={`py-2 px-3 rounded-xl text-[12px] font-medium text-left border transition-colors ${
                        filterProtection === prot.id
                          ? 'bg-primary text-surface border-primary font-semibold'
                          : 'bg-surface-container-low text-primary border-outline-variant/30 hover:bg-surface-container'
                      }`}
                    >
                      {prot.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Price Range */}
              <div>
                <label className="font-label-caps text-[10px] uppercase tracking-wider text-secondary font-bold block mb-2">
                  Unit Price Range ($)
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-[11px] text-on-surface-variant block mb-1">Min Price</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="$0.00"
                      value={filterMinPrice}
                      onChange={(e) => setFilterMinPrice(e.target.value)}
                      className="w-full bg-surface-container-low border border-outline-variant/40 rounded-xl px-3 py-2 text-[13px] text-primary"
                    />
                  </div>
                  <div>
                    <span className="text-[11px] text-on-surface-variant block mb-1">Max Price</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="$10.00"
                      value={filterMaxPrice}
                      onChange={(e) => setFilterMaxPrice(e.target.value)}
                      className="w-full bg-surface-container-low border border-outline-variant/40 rounded-xl px-3 py-2 text-[13px] text-primary"
                    />
                  </div>
                </div>
              </div>

              {/* Sort By */}
              <div>
                <label className="font-label-caps text-[10px] uppercase tracking-wider text-secondary font-bold block mb-2">
                  Sort By
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {[
                    { id: 'recommended', label: 'Recommended' },
                    { id: 'price_asc', label: 'Lowest Unit Price' },
                    { id: 'volume_asc', label: 'Smallest Package Volume' },
                    { id: 'protection_desc', label: 'Highest Protection Evidence' },
                    { id: 'co2_saved_desc', label: 'Lowest Available CO₂e' },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => setSortBy(opt.id)}
                      className={`py-2 px-3 rounded-xl text-[12px] font-medium text-left border transition-colors ${
                        sortBy === opt.id
                          ? 'bg-primary text-surface border-primary font-semibold'
                          : 'bg-surface-container-low text-primary border-outline-variant/30 hover:bg-surface-container'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-outline-variant/20 flex gap-2.5 bg-surface-container-low">
              <button
                onClick={resetFilters}
                className="py-2.5 px-4 bg-surface text-on-surface-variant border border-outline-variant/30 rounded-xl text-[13px] font-medium hover:bg-surface-container"
              >
                Clear All
              </button>
              <button
                onClick={() => {
                  setPage(1);
                  setShowFilterModal(false);
                }}
                className="flex-1 py-2.5 bg-primary text-surface rounded-xl text-[13px] font-medium tracking-wide hover:bg-primary-container shadow-xs"
              >
                Apply Filters ({filtered.length} products)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EcoShop;
