"use client";

import { ChevronLeft, ChevronRight, Download, Pencil, X } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { retouchImage } from "@/lib/api";

type ImageItem = {
  url: string;
  label?: string;
  kit_type?: string;
  prompt?: string;
};

type Props = {
  open: boolean;
  images: ImageItem[];
  currentIndex: number;
  onIndexChange: (index: number) => void;
  onClose: () => void;
};

type EditStatus = "idle" | "loading" | "done" | "error";

export function ImagePreviewModal({ open, images, currentIndex, onIndexChange, onClose }: Props) {
  // ── 编辑图生图 state ──
  const [editing, setEditing] = useState(false);
  const [editPrompt, setEditPrompt] = useState("");
  const [editStatus, setEditStatus] = useState<EditStatus>("idle");
  const [editError, setEditError] = useState("");
  const [retouchedUrl, setRetouchedUrl] = useState("");

  const handlePrev = useCallback(() => {
    onIndexChange((currentIndex - 1 + images.length) % images.length);
  }, [currentIndex, images.length, onIndexChange]);

  const handleNext = useCallback(() => {
    onIndexChange((currentIndex + 1) % images.length);
  }, [currentIndex, images.length, onIndexChange]);

  // 打开编辑弹窗
  const handleEditOpen = useCallback(() => {
    const img = images[currentIndex];
    setEditPrompt(img?.prompt || "");
    setEditStatus("idle");
    setEditError("");
    setRetouchedUrl("");
    setEditing(true);
  }, [currentIndex, images]);

  // 提交图生图编辑
  const handleEditSubmit = useCallback(async () => {
    const img = images[currentIndex];
    if (!editPrompt.trim() || !img) return;

    setEditStatus("loading");
    setEditError("");
    try {
      const result = await retouchImage({
        imageUrl: img.url,
        prompt: editPrompt.trim(),
      });
      setRetouchedUrl(result.url);
      setEditStatus("done");
    } catch (err: any) {
      setEditError(err?.message || "生成失败，请重试");
      setEditStatus("error");
    }
  }, [currentIndex, images, editPrompt]);

  useEffect(() => {
    if (!open) return;
    const handleKey = (e: KeyboardEvent) => {
      if (editing) return; // 编辑时禁用键盘导航
      if (e.key === "ArrowLeft") handlePrev();
      if (e.key === "ArrowRight") handleNext();
      if (e.key === "Escape") {
        if (editing) setEditing(false);
        else onClose();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, editing, handlePrev, handleNext, onClose]);

  if (!open || images.length === 0) return null;

  const img = images[currentIndex];
  const title = img.label || img.kit_type || "套图预览";
  const hasMultiple = images.length > 1;
  // 如果编辑完成，显示修后图
  const displayUrl = retouchedUrl || img.url;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
      <div className="flex max-h-[92vh] w-full max-w-6xl flex-col rounded border border-line bg-panel shadow-2xl">
        {/* header */}
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
          <div className="flex items-center gap-2 min-w-0">
            <h2 className="min-w-0 truncate text-sm font-semibold text-ink">
              {retouchedUrl ? `${title}（已编辑）` : title}
            </h2>
            {hasMultiple && (
              <span className="shrink-0 text-xs text-slate-400">
                {currentIndex + 1} / {images.length}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* 下载 */}
            <a
              href={displayUrl}
              download
              className="inline-flex h-9 items-center gap-2 rounded border border-line bg-surface px-3 text-sm font-semibold text-ink hover:border-action hover:text-action transition-colors"
            >
              <Download size={16} />
              下载
            </a>
            {/* 编辑 */}
            <button
              type="button"
              onClick={handleEditOpen}
              className="inline-flex h-9 items-center gap-2 rounded border border-line bg-surface px-3 text-sm font-semibold text-ink hover:border-action hover:text-action transition-colors"
              aria-pressed={editing}
              style={{ touchAction: "manipulation" }}
            >
              <Pencil size={16} />
              编辑
            </button>
            {/* 关闭 */}
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
            src={displayUrl}
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

      {/* ── 编辑弹窗 ── */}
      {editing && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-lg rounded border border-line bg-panel shadow-2xl">
            <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
              <h3 className="text-sm font-semibold text-ink">
                {editStatus === "done" ? "编辑完成" : "修改提示词"}
              </h3>
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="inline-flex h-8 w-8 items-center justify-center rounded border border-line text-ink hover:border-action hover:text-action transition-colors"
                aria-label="关闭编辑"
                style={{ touchAction: "manipulation" }}
              >
                <X size={15} />
              </button>
            </div>

            <div className="px-4 py-3 space-y-3">
              {editStatus === "done" ? (
                <div className="text-sm text-ink space-y-2">
                  <p className="text-green-600 font-medium">✅ 图生图编辑完成</p>
                  <p className="text-slate-500 text-xs">当前预览已切换为编辑后的图片，可下载保存。</p>
                </div>
              ) : editStatus === "loading" ? (
                <div className="flex items-center justify-center py-8">
                  <p className="text-sm text-slate-500 animate-pulse">⏳ 正在生成，请稍候…</p>
                </div>
              ) : (
                <>
                  <label className="block text-xs font-medium text-slate-500">
                    修改后提示词（当前图作为参考做图生图）
                  </label>
                  <textarea
                    value={editPrompt}
                    onChange={(e) => setEditPrompt(e.target.value)}
                    rows={5}
                    className="w-full rounded border border-line bg-surface px-3 py-2 text-sm text-ink placeholder:text-slate-400 focus:border-action focus:outline-none resize-y"
                    placeholder="输入修改后的提示词…"
                  />
                  {editError && (
                    <p className="text-xs text-red-500">{editError}</p>
                  )}
                  <div className="flex justify-end gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => setEditing(false)}
                      className="inline-flex h-9 items-center gap-2 rounded border border-line bg-surface px-3 text-sm text-ink hover:border-action hover:text-action transition-colors"
                      style={{ touchAction: "manipulation" }}
                    >
                      取消
                    </button>
                    <button
                      type="button"
                      onClick={handleEditSubmit}
                      disabled={!editPrompt.trim()}
                      className="inline-flex h-9 items-center gap-2 rounded border border-action bg-action px-3 text-sm font-semibold text-white hover:brightness-110 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ touchAction: "manipulation" }}
                    >
                      提交生成
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
