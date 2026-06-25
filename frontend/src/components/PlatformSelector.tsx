"use client";

import { Check, Globe } from "lucide-react";
import type { Platform } from "@/types";
import { PLATFORMS } from "@/types";
import { platformRules } from "@/lib/platform-rules";

type Props = {
  value: Platform;
  onChange: (platform: Platform) => void;
};

export function PlatformSelector({ value, onChange }: Props) {
  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
        <Globe size={18} />
        选择平台
      </h2>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {PLATFORMS.map((p) => {
          const rule = platformRules[p];
          const active = value === p;
          return (
            <div key={p} className="relative">
              <input
                className="sr-only"
                type="radio"
                name="platform"
                value={p}
                checked={active}
                onChange={() => onChange(p)}
              />
              <button
                type="button"
                onClick={() => onChange(p)}
                aria-pressed={active}
                className={`selectable-card relative flex min-h-[72px] w-full cursor-pointer flex-col items-start gap-1 rounded border bg-transparent px-3 py-2.5 text-left transition ${
                  active
                    ? "selected-card border-action"
                    : "border-line bg-white hover:border-slate-300"
                }`}
              >
                <span className="text-sm font-semibold text-ink">{rule.label}</span>
                <span className="text-xs text-slate-500">
                  {rule.width}×{rule.height}
                </span>
                {active && (
                  <Check
                    size={14}
                    className="absolute right-2 top-2 text-action"
                  />
                )}
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}
