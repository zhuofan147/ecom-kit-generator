"use client";

import { Check, Cpu, Settings, ChevronDown, Loader2 } from "lucide-react";
import { useEffect, useState, useRef } from "react";

type Provider = {
  name: string;
  label: string;
  description: string;
  model_id: string;
  endpoint: string;
  available: boolean;
  is_default: boolean;
};

type Props = {
  selected: string[];
  onToggle: (providerName: string) => void;
  onOpenSettings?: () => void;
  /** Pass enabled image configs to bypass backend provider API entirely.
   *  When provided, ModelSelector won't fetch /api/providers — it derives
   *  the available list directly from what's enabled in Settings. */
  enabledModels?: Pick<Provider, "name" | "label" | "model_id" | "endpoint">[];
};

export function ModelSelector({ selected, onToggle, onOpenSettings, enabledModels }: Props) {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(!enabledModels);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (enabledModels) return; // use passed list, skip backend fetch
    const fetchProviders = async () => {
      try {
        const base = process.env.NEXT_PUBLIC_API_BASE_URL || `http://${window.location.hostname}:8000`;
        const res = await fetch(`${base}/api/providers`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setProviders(data.providers || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "获取失败");
      } finally {
        setLoading(false);
      }
    };
    fetchProviders();
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const available: Provider[] = enabledModels
    ? enabledModels.map((m) => ({ ...m, description: m.model_id, available: true, is_default: false }))
    : providers.filter((p) => p.available);
  const selectedList = available.filter((p) => selected.includes(p.name));

  // ── loading ──
  if (loading) {
    return (
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
          <Cpu size={18} /> AI 生图模型
        </h2>
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Loader2 size={16} className="animate-spin" /> 加载中…
        </div>
      </section>
    );
  }

  // ── error ──
  if (error) {
    return (
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
          <Cpu size={18} /> AI 生图模型
        </h2>
        <div className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
          获取模型列表失败：{error}
        </div>
        <button
          type="button"
          onClick={() => window.location.reload()}
          style={{ touchAction: "manipulation" }}
          className="text-xs text-action underline"
        >
          重试
        </button>
      </section>
    );
  }

  // ── empty ──
  if (available.length === 0) {
    return (
      <section className="space-y-3">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
          <Cpu size={18} /> AI 生图模型
        </h2>
        <p className="text-sm text-slate-500">暂无可用的生图模型</p>
        <p className="text-xs text-slate-400">请配置 API Key 后刷新</p>
        {onOpenSettings && (
          <button
            type="button"
            onClick={onOpenSettings}
            style={{ touchAction: "manipulation" }}
            className="inline-flex items-center gap-1.5 rounded border border-action bg-white px-3 py-1.5 text-xs font-semibold text-action hover:bg-panel"
          >
            <Settings size={13} /> 去设置添加模型
          </button>
        )}
      </section>
    );
  }

  // ── normal ──
  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
        <Cpu size={18} /> AI 生图模型
      </h2>

      <div ref={ref} className="relative">
        {/* trigger */}
        <button
          type="button"
          onClick={() => setOpen(!open)}
          aria-pressed={open}
          style={{ touchAction: "manipulation" }}
          className="flex w-full items-center justify-between rounded border border-line bg-white px-3 py-2.5 text-left text-sm shadow-sm hover:border-slate-300"
        >
          <span className={selectedList.length === 0 ? "text-slate-400" : "text-ink"}>
            {selectedList.length === 0
              ? "选择生图模型…"
              : selectedList.map((p) => p.label).join("、")}
          </span>
          <ChevronDown
            size={16}
            className={`shrink-0 text-slate-400 transition-transform ${open ? "rotate-180" : ""}`}
          />
        </button>

        {/* dropdown */}
        {open && (
          <div className="absolute left-0 right-0 z-50 mt-1 rounded border border-line bg-white shadow-lg">
            {available.map((p) => {
              const isSel = selected.includes(p.name);
              return (
                <button
                  key={p.name}
                  type="button"
                  onClick={() => onToggle(p.name)}
                  aria-pressed={isSel}
                  style={{ touchAction: "manipulation" }}
                  className={`flex w-full items-center gap-3 px-3 py-2.5 text-left text-sm transition hover:bg-slate-50 ${
                    isSel ? "bg-slate-50" : ""
                  }`}
                >
                  <span className="shrink-0">
                    {isSel ? (
                      <Check size={16} className="text-action" />
                    ) : (
                      <span className="block h-4 w-4 rounded border border-slate-300" />
                    )}
                  </span>
                  <div className="min-w-0">
                    <div className="font-semibold text-ink">{p.label}</div>
                    <div className="text-xs text-slate-400">{p.model_id || p.name}</div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* summary */}
      <div className="rounded bg-slate-50 px-3 py-2 text-xs text-ink">
        已选 <strong>{selectedList.length}</strong> / {available.length} 个生图模型
      </div>
    </section>
  );
}