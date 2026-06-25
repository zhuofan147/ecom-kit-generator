"use client";

import { Cpu, Zap } from "lucide-react";
import { useEffect, useState } from "react";

import type { ProviderInfo } from "@/types";

type Props = {
  value: string;
  onChange: (provider: string) => void;
};

export function ModelSelector({ value, onChange }: Props) {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${typeof window !== "undefined" ? `http://${window.location.hostname}:8000` : "http://localhost:8000"}/api/providers`)
      .then((r) => r.json())
      .then((data) => setProviders(data.providers || []))
      .catch(() => setProviders([]))
      .finally(() => setLoading(false));
  }, []);

  const selected = providers.find((p) => p.name === value);

  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
        <Cpu size={18} />
        AI 生图模型
      </h2>

      {loading ? (
        <p className="text-sm text-slate-500">加载中…</p>
      ) : (
        <div className="space-y-2">
          {providers.map((p) => (
            <button
              key={p.name}
              type="button"
              disabled={!p.available}
              onClick={() => onChange(p.name)}
              className={`flex w-full items-start gap-3 rounded border px-3 py-2.5 text-left transition ${
                p.name === value
                  ? "selected-card"
                  : !p.available
                    ? "cursor-not-allowed border-slate-100 bg-slate-50 opacity-50"
                    : "border-line bg-white hover:border-slate-300"
              }`}
            >
              <span className="mt-0.5 shrink-0">
                {p.name === value ? (
                  <Zap size={16} className="text-action" />
                ) : (
                  <Cpu size={16} className={p.available ? "text-slate-400" : "text-slate-300"} />
                )}
              </span>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-ink">{p.label}</span>
                  {!p.available && (
                    <span className="rounded bg-slate-200 px-1.5 py-0.5 text-[10px] text-slate-500">
                      不可用
                    </span>
                  )}
                  {p.name === value && (
                    <span className="selected-badge rounded border px-1.5 py-0.5 text-[10px]">
                      当前
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-xs leading-4 text-slate-500">{p.description}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <div className="selected-card rounded px-3 py-2 text-xs text-ink">
          当前：<strong>{selected.label}</strong> — {selected.description}
        </div>
      )}
    </section>
  );
}
