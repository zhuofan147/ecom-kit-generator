"use client";

import { Download, Loader2, RotateCcw, Tag } from "lucide-react";

import { assetUrl } from "@/lib/api";
import type { GeneratedImage } from "@/types";

type Props = {
  image: GeneratedImage;
  busy: boolean;
  onPreview: () => void;
  onRetry: () => void;
};

export function GeneratedImageCard({ image, busy, onPreview, onRetry }: Props) {
  const label = image.label || image.kit_type;

  return (
    <div className="rounded border border-line bg-white p-3">
      <div className="mb-2 flex items-center gap-1.5">
        <Tag size={12} className="text-action" />
        <span className="text-xs font-semibold text-ink">{label}</span>
      </div>
      {image.status === "failed" ? (
        <div className="flex aspect-square w-full flex-col items-center justify-center gap-3 rounded border border-red-200 bg-red-50 p-4 text-center">
          <p className="text-sm font-semibold text-red-700">生成失败</p>
          <p className="line-clamp-4 text-xs leading-5 text-red-600">
            {image.error || "该类型图片生成失败"}
          </p>
          <RetryButton busy={busy} onRetry={onRetry} tone="danger" />
        </div>
      ) : image.status === "running" ? (
        <div className="flex aspect-square w-full flex-col items-center justify-center gap-2 rounded border border-line bg-white text-sm text-slate-500">
          <Loader2 size={18} className="animate-spin text-action" />
          重新生成中…
        </div>
      ) : (
        <>
          <button
            type="button"
            onClick={onPreview}
            className="aspect-square w-full overflow-hidden rounded border border-slate-100 bg-[repeating-conic-gradient(#f1f5f9_0%_25%,transparent_0%_50%)_50%/16px_16px]"
            aria-label={`放大查看${label}`}
          >
            <img
              src={assetUrl(image.url)}
              alt={label}
              className="h-full w-full object-contain"
            />
          </button>
          <div className="mt-2 grid grid-cols-2 gap-2">
            <RetryButton busy={busy} onRetry={onRetry} />
            <a
              className="inline-flex items-center justify-center gap-1.5 rounded border border-line bg-surface px-3 py-1.5 text-xs font-medium text-ink transition-colors hover:border-action hover:text-action"
              href={assetUrl(image.url)}
              download
            >
              <Download size={13} />
              下载
            </a>
          </div>
        </>
      )}
    </div>
  );
}

function RetryButton({
  busy,
  onRetry,
  tone = "default",
}: {
  busy: boolean;
  onRetry: () => void;
  tone?: "default" | "danger";
}) {
  const className = tone === "danger"
    ? "inline-flex items-center gap-1.5 rounded border border-red-200 bg-white px-3 py-1.5 text-xs font-semibold text-red-700 hover:border-red-400 disabled:cursor-not-allowed disabled:opacity-60"
    : "inline-flex items-center justify-center gap-1.5 rounded border border-line bg-white px-3 py-1.5 text-xs font-medium text-ink transition-colors hover:border-action hover:text-action disabled:cursor-not-allowed disabled:opacity-60";

  return (
    <button
      type="button"
      disabled={busy}
      onClick={onRetry}
      className={className}
    >
      <RotateCcw size={13} />
      重新生成
    </button>
  );
}
