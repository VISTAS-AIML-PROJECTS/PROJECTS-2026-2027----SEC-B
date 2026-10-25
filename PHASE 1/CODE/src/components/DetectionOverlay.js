import React from 'react';

export default function DetectionOverlay({
  imageSrc,
  detections = [],
  selectedIndex = 0,
  onSelectDetection,
}) {
  return (
    <div className="relative w-full rounded-2xl overflow-hidden bg-surface-container-low shadow-sm">
      <div className="relative w-full aspect-[4/3] bg-primary-container overflow-hidden">
        {imageSrc ? (
          <img
            src={imageSrc}
            alt="Scanned product"
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-on-primary-container">
            <span className="material-symbols-outlined text-4xl">inventory_2</span>
          </div>
        )}

        {/* Bounding box overlays */}
        {detections.map((det, index) => {
          const isSelected = index === selectedIndex;
          const bbox = det.bbox;

          return (
            <div
              key={index}
              onClick={() => onSelectDetection && onSelectDetection(index)}
              title={`${det.class_name} (${Math.round(det.confidence * 100)}%)`}
              className={`absolute cursor-pointer transition-all duration-200 ${
                isSelected
                  ? 'border-2 border-secondary-fixed ring-2 ring-primary/40 shadow-lg'
                  : 'border border-white/60 hover:border-secondary-fixed/80 bg-black/10'
              }`}
              style={{
                // If bbox has coordinates or fallback to centered relative frame
                left: bbox?.x1 ? `${Math.min(100, Math.max(0, (bbox.x1 / 640) * 100))}%` : '15%',
                top: bbox?.y1 ? `${Math.min(100, Math.max(0, (bbox.y1 / 640) * 100))}%` : '15%',
                width: bbox?.x2 ? `${Math.min(100, Math.max(10, ((bbox.x2 - bbox.x1) / 640) * 100))}%` : '70%',
                height: bbox?.y2 ? `${Math.min(100, Math.max(10, ((bbox.y2 - bbox.y1) / 640) * 100))}%` : '70%',
              }}
            >
              {/* Corner Accents */}
              <div className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-secondary-fixed"></div>
              <div className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-secondary-fixed"></div>
              <div className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-secondary-fixed"></div>
              <div className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-secondary-fixed"></div>

              {/* Tag pill */}
              <div className="absolute -top-7 left-0 flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-primary/95 text-surface text-[10px] font-semibold tracking-wide uppercase shadow-md whitespace-nowrap">
                <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-secondary-fixed' : 'bg-white/60'}`}></span>
                <span>{det.class_name}</span>
                <span className="text-secondary-fixed font-mono text-[9px]">
                  {Math.round((det.confidence || 0) * 100)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detection selection bar if multiple detections */}
      {detections.length > 1 && (
        <div className="p-3 bg-surface-container border-t border-outline-variant/30 flex items-center justify-between">
          <span className="font-label-caps text-[10px] uppercase text-on-surface-variant font-semibold">
            {detections.length} objects detected — tap to select:
          </span>
          <div className="flex gap-1.5 overflow-x-auto">
            {detections.map((d, idx) => (
              <button
                key={idx}
                onClick={() => onSelectDetection && onSelectDetection(idx)}
                className={`px-2.5 py-1 rounded-full text-xs font-medium transition-all ${
                  idx === selectedIndex
                    ? 'bg-primary text-surface font-semibold shadow-xs'
                    : 'bg-surface text-on-surface-variant hover:bg-surface-container-high'
                }`}
              >
                {d.class_name} ({Math.round(d.confidence * 100)}%)
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
