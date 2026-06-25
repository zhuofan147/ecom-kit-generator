"use client";

import { ChangeEvent, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";

type UploadZoneProps = {
  disabled?: boolean;
  onFiles: (files: File[]) => void;
};

export function UploadZone({ disabled, onFiles }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleFiles = (files?: FileList | File[]) => {
    const selected = Array.from(files ?? []).slice(0, 6);
    if (selected.length) onFiles(selected);
  };

  const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiles(event.target.files ?? undefined);
    event.target.value = "";
  };

  const openPicker = () => {
    if (!disabled) inputRef.current?.click();
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        multiple
        disabled={disabled}
        className="sr-only"
        onChange={onInputChange}
      />
      <button
        type="button"
        disabled={disabled}
        onClick={openPicker}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          if (!disabled) handleFiles(event.dataTransfer.files);
        }}
        style={{ touchAction: "manipulation" }}
        className={`flex min-h-48 w-full cursor-pointer flex-col items-center justify-center rounded border border-dashed px-6 py-8 text-center transition ${
          dragging ? "border-action bg-teal-50" : "border-slate-300 bg-white"
        } ${disabled ? "cursor-wait opacity-70" : "hover:border-action"}`}
      >
        <UploadCloud size={32} className="mb-2 text-slate-400" />
        <span className="text-base font-semibold text-ink">上传 1-6 张产品参考图</span>
        <span className="mt-2 text-sm text-slate-600">自动白底化并合成多视图参考，单张最大 20MB</span>
      </button>
    </>
  );
}
