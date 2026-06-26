"use client";

import { Cpu, Zap } from "lucide-react";

import { useAppStore } from "@/store";

type Props = {
  value: string;
  onChange: (provider: string) => void;
};

export function ModelSelector({ value, onChange }: Props) {
  const imageConfigs = useAppStore((s) => s.imageConfigs);

  if (imageConfigs.length === 0) {
    return (
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
          <Cpu size={18} />
          AI 生图模型
        </h2>
        <p className="text-sm text-slate-500">暂无可用的生图模型</p>
      </section>
    );
  }

  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
        <Cpu size={18} />
        AI 生图模型
      </h2>

      <div className="space-y-2">
        {imageConfigs.map((config) => {
          const isSelected = config.model === value;
          const unavailable = !config.enabled;
          return (
            <button
              key={config.id}
              type="button"
              disabled={unavailable}
              onClick={() => onChange(config.model || config.id)}
              style={{ touchAction: "manipulation" }}
              className={`flex w-full items-start gap-3 rounded border px-3 py-2.5 text-left transition ${
                isSelected
                  ? "selected-card"
                  : unavailable
                    ? "cursor-not-allowed border-slate-100 bg-slate-50 opacity-50"
                    : "border-line bg-white hover:border-slate-300"
              }`}
            >
              <span className="mt-0.5 shrink-0">
                {isSelected ? (
                  <Zap size={16} className="text-action" />
                ) : (
                  <Cpu size={16} className={unavailable ? "text-slate-300" : "text-slate-400"} />
                )}
              </span>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-ink">{config.name}</span>
                  {unavailable && (
                    <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] text-slate-500">
                      停用
                    </span>
                  )}
                  {isSelected && (
                    <span className="selected-badge rounded border px-1.5 py-0.5 text-[10px]">
                      当前
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-xs leading-4 text-slate-500">
                  {config.model || config.id}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      <div className="selected-card rounded px-3 py-2 text-xs text-ink">
        共 <strong>{imageConfigs.length}</strong> 个生图模型可用
      </div>
    </section>
  );
}
