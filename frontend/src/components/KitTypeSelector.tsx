"use client";

import { ImageIcon, LayoutGrid } from "lucide-react";
import type { KitSizeMap, KitType, Platform } from "@/types";
import {
  KIT_DESCRIPTIONS,
  KIT_LABELS,
  KIT_SIZE_PRESETS,
  KIT_TYPES,
  getKitDimension,
} from "@/types";

type Props = {
  platform: Platform;
  value: KitType[];
  kitSizes: KitSizeMap;
  onToggle: (kitType: KitType) => void;
  onSizeChange: (kitType: KitType, size?: { w: number; h: number }) => void;
};

function sizeValue(size?: { w: number; h: number }) {
  return size ? `${size.w}x${size.h}` : "default";
}

function presetFromValue(value: string) {
  return KIT_SIZE_PRESETS.find((preset) => preset.value === value);
}

export function KitTypeSelector({
  platform,
  value,
  kitSizes,
  onToggle,
  onSizeChange,
}: Props) {
  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
        <LayoutGrid size={18} />
        套图类型
        <span className="text-sm font-normal text-slate-500">
          （已选 {value.length} 项）
        </span>
      </h2>
      <div className="grid grid-cols-2 gap-2">
        {KIT_TYPES.map((kt) => {
          const defaultDims = getKitDimension(platform, kt);
          const dims = kitSizes[kt] ?? defaultDims;
          const active = value.includes(kt);
          return (
            <div
              key={kt}
              className={`flex min-h-[150px] flex-col rounded border px-3 py-2.5 text-left transition ${
                active
                  ? "selected-card border-action"
                  : "border-line bg-white hover:border-slate-300"
                }`}
            >
              <input
                className="sr-only"
                type="checkbox"
                name="kitTypes"
                value={kt}
                checked={active}
                onChange={() => onToggle(kt)}
              />
              <button
                type="button"
                onClick={() => onToggle(kt)}
                className="flex flex-1 cursor-pointer flex-col gap-1 bg-transparent p-0 text-left"
                aria-pressed={active}
              >
                <span className="flex items-center gap-2">
                  <span
                    className={`flex h-4 w-4 items-center justify-center rounded border text-[10px] ${
                      active
                        ? "border-action bg-action text-white"
                        : "border-slate-300 bg-white"
                    }`}
                  >
                    {active ? "✓" : ""}
                  </span>
                  <span className="text-sm font-semibold text-ink">
                    {KIT_LABELS[kt]}
                  </span>
                </span>
                <span className="text-xs text-slate-500">
                  {KIT_DESCRIPTIONS[kt]}
                </span>
                <span className="text-xs text-slate-400">
                  {dims.w}×{dims.h}
                </span>
              </button>
              <div className="mt-2 flex flex-col gap-1 text-xs text-slate-500">
                <span>尺寸</span>
                <select
                  name={`kitSize-${kt}`}
                  value={sizeValue(kitSizes[kt])}
                  disabled={!active}
                  onChange={(event) => {
                    const preset = presetFromValue(event.target.value);
                    onSizeChange(
                      kt,
                      preset && "w" in preset ? { w: preset.w, h: preset.h } : undefined
                    );
                  }}
                  className="h-9 rounded border border-line bg-white px-2 text-xs text-ink disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {KIT_SIZE_PRESETS.map((preset) => (
                    <option key={preset.value} value={preset.value}>
                      {preset.value === "default"
                        ? `平台默认 ${defaultDims.w}×${defaultDims.h}`
                        : preset.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
