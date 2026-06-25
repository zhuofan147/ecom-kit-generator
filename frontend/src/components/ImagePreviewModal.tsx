"use client";

import { ChevronLeft, ChevronRight, Download, X } from "lucide-react";
import { useCallback, useEffect } from "react";

type ImageItem = {
  url: string;
  label?: string;
  kit_type?: string;
};

type Props = {
  open: boolean;
  images: ImageItem[];
  currentIndex: number;
  onIndexChange: (index: number) => void;
  onClose: () => void;
};

export function ImagePreviewModal({ open, images, currentIndex, onIndexChange, onClose }: Props) {
  const handlePrev = useCallback(() => {
    onIndexChange((currentIndex - 1 + images.length) % images.length);
  }, [currentIndex, images.length, onIndexChange]);

  const handleNext = useCallback(() => {
    onIndexChange((currentIndex + 1) % images.length);
  }, [currentIndex, images.length, onIndexChange]);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, handlePrev, handleNext, onClose]);

  if (!open || images.length === 0) return null;

  const img = images[currentIndex];
  const title = img.label || img.kit_type || "套图预览";
  const hasMultiple = images.length > 1;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
      <div className="flex max-h-[92vh] w-full max-w-6xl flex-col rounded border border-line bg-panel shadow-2xl">
        {/* header */}
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
          <div className="flex items-center gap-2 min-w-0">
            <h2 className="min-w-0 truncate text-sm font-semibold text-ink">
              {title}
            </h2>
            {hasMultiple && (
              <span className="shrink-0 text-xs text-slate-400">
                {currentIndex + 1} / {images.length}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <a
              href={img.url}
              download
              className="inline-flex h-9 items-center gap-2 rounded border border-line bg-surface px-3 text-sm font-semibold text-ink hover:border-action hover:text-action transition-colors"
            >
              <Download size={16} />
              下载
            </a>
            <button
              type="button"
              onClick={onClose}
              className="inline-flex h-9 w-9 items-center justify-center rounded border border-line bg-surface text-ink hover:border-action hover:text-action transition-colors"
              aria-label="关闭预览"
            >
              <X size={17} />
            </button>
          </div>
        </div>

        {/* body with navigation */}
        <div className="relative flex min-h-0 flex-1 items-center justify-center overflow-hidden bg-[repeating-conic-gradient(#e2e8f0_0%_25%,transparent_0%_50%)_50%/20px_20px]">
          {/* left arrow */}
          {hasMultiple && (
            <button
              type="button"
              onClick={handlePrev}
              className="absolute left-3 z-10 inline-flex h-11 w-11 items-center justify-center rounded-full border border-line bg-surface/90 text-ink shadow-lg backdrop-blur-sm hover:border-action hover:text-action transition-colors"
              aria-label="上一张"
            >
              <ChevronLeft size={24} />
            </button>
          )}

          {/* image */}
          <img
            src={img.url}
            alt={title}
            className="max-h-[78vh] max-w-full object-contain"
          />

          {/* right arrow */}
          {hasMultiple && (
            <button
              type="button"
              onClick={handleNext}
              className="absolute right-3 z-10 inline-flex h-11 w-11 items-center justify-center rounded-full border border-line bg-surface/90 text-ink shadow-lg backdrop-blur-sm hover:border-action hover:text-action transition-colors"
              aria-label="下一张"
            >
              <ChevronRight size={24} />
            </button>
          )}
        </div>

        {/* thumbnail strip */}
        {hasMultiple && (
          <div className="flex gap-2 overflow-x-auto border-t border-line px-4 py-2.5">
            {images.map((item, i) => (
              <button
                key={i}
                type="button"
                onClick={() => onIndexChange(i)}
                className={`shrink-0 overflow-hidden rounded border transition-all ${
                  i === currentIndex
                    ? "border-action ring-1 ring-action/30"
                    : "border-line opacity-60 hover:opacity-100"
                }`}
                aria-label={`查看第 ${i + 1} 张`}
              >
                <img
                  src={item.url}
                  alt={item.label || item.kit_type || ""}
                  className="h-14 w-14 object-cover"
                />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
