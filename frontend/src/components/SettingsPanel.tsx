"use client";

import { List, PlugZap, Plus, Settings, X } from "lucide-react";
import { useState } from "react";

import type { ModelConfig, ThemeStyle } from "@/types";
import { testLlmConnection, listModels } from "@/lib/api";

type Props = {
  open: boolean;
  theme: ThemeStyle;
  llmConfigs: ModelConfig[];
  imageConfigs: ModelConfig[];
  selectedLlmConfigId: string;
  selectedImageConfigId: string;
  onClose: () => void;
  onThemeChange: (theme: ThemeStyle) => void;
  onAddLlmConfig: () => void;
  onAddImageConfig: () => void;
  onUpdateLlmConfig: (id: string, patch: Partial<ModelConfig>) => void;
  onUpdateImageConfig: (id: string, patch: Partial<ModelConfig>) => void;
  onRemoveLlmConfig: (id: string) => void;
  onRemoveImageConfig: (id: string) => void;
  onRemoveVisionConfig: (id: string) => void;
  onSelectLlmConfig: (id: string) => void;
  onSelectImageConfig: (id: string) => void;
  onSelectVisionConfig: (id: string) => void;
  visionConfigs?: ModelConfig[];
  selectedVisionConfigId?: string;
  onAddVisionConfig?: () => void;
  onUpdateVisionConfig?: (id: string, patch: Partial<ModelConfig>) => void;
};

const themeOptions: Array<{ value: ThemeStyle; label: string; swatch: string }> = [
  { value: "light", label: "明亮", swatch: "bg-white" },
  { value: "dark", label: "暗黑", swatch: "bg-black" },
  { value: "white", label: "纯白", swatch: "bg-white" },
];

export function SettingsPanel({
  open,
  theme,
  llmConfigs,
  imageConfigs,
  selectedLlmConfigId,
  selectedImageConfigId,
  onClose,
  onThemeChange,
  onAddLlmConfig,
  onAddImageConfig,
  onUpdateLlmConfig,
  onUpdateImageConfig,
  onRemoveLlmConfig,
  onRemoveImageConfig,
  onRemoveVisionConfig,
  onSelectLlmConfig,
  onSelectImageConfig,
  onSelectVisionConfig,
  visionConfigs,
  selectedVisionConfigId,
  onAddVisionConfig,
  onUpdateVisionConfig,
}: Props) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/30 px-4 py-5 backdrop-blur-sm">
      <section className="ml-auto flex h-full w-full max-w-3xl flex-col overflow-hidden rounded border border-line bg-white shadow-xl">
        <header className="flex items-center justify-between border-b border-line px-5 py-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
            <Settings size={18} />
            设置
          </h2>
          <button
            type="button"
            aria-label="关闭设置"
            onClick={onClose}
            className="inline-flex h-9 w-9 items-center justify-center rounded border border-line bg-white text-slate-600 hover:bg-slate-50"
          >
            <X size={18} />
          </button>
        </header>

        <div className="flex-1 space-y-6 overflow-y-auto px-5 py-5">
          <section className="space-y-3">
            <h3 className="text-base font-semibold text-ink">页面风格</h3>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {themeOptions.map((option) => (
                <label key={option.value} className="cursor-pointer">
                  <input
                    type="radio"
                    name="theme"
                    value={option.value}
                    checked={theme === option.value}
                    onChange={() => onThemeChange(option.value)}
                    className="sr-only"
                  />
                  <span className={`selectable-card flex items-center gap-2 rounded border border-line bg-white px-3 py-2 text-sm font-medium text-ink transition`}>
                    <span className={`h-4 w-4 rounded-full border border-line ${option.swatch} ${
                      option.value === "white" ? "theme-swatch-white" : ""
                    }`} />
                    {option.label}
                  </span>
                </label>
              ))}
            </div>
          </section>

          <ModelConfigSection
            title="大语言模型配置"
            configs={llmConfigs}
            selectedId={selectedLlmConfigId}
            onAdd={onAddLlmConfig}
            onSelect={onSelectLlmConfig}
            onUpdate={onUpdateLlmConfig}
            onRemove={onRemoveLlmConfig}
          />

          <ModelConfigSection
            title="生图模型配置"
            configs={imageConfigs}
            selectedId={selectedImageConfigId}
            onAdd={onAddImageConfig}
            onSelect={onSelectImageConfig}
            onUpdate={onUpdateImageConfig}
            onRemove={onRemoveImageConfig}
          />

          {visionConfigs && onAddVisionConfig && onUpdateVisionConfig && onSelectVisionConfig && (
            <ModelConfigSection
              title="视觉模型配置（Vision）"
              configs={visionConfigs}
              selectedId={selectedVisionConfigId ?? "vision-default"}
              onAdd={onAddVisionConfig}
              onSelect={onSelectVisionConfig}
              onUpdate={onUpdateVisionConfig}
              onRemove={onRemoveVisionConfig}
            />
          )}
        </div>
      </section>
    </div>
  );
}

// ── ModelConfigSection (internal) ─────────────────────────────────

function ModelConfigSection({
  title,
  configs,
  selectedId,
  onAdd,
  onSelect,
  onUpdate,
  onRemove,
}: {
  title: string;
  configs: ModelConfig[];
  selectedId: string;
  onAdd: () => void;
  onSelect: (id: string) => void;
  onUpdate: (id: string, patch: Partial<ModelConfig>) => void;
  onRemove: (id: string) => void;
}) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-base font-semibold text-ink">{title}</h3>
        <button
          type="button"
          onClick={onAdd}
          className="inline-flex items-center gap-1.5 rounded border border-action bg-white px-3 py-1.5 text-sm font-semibold text-action hover:bg-panel"
        >
          <Plus size={15} />
          添加
        </button>
      </div>

      <div className="space-y-3">
        {configs.map((config) => (
          <ConfigCard
            key={config.id}
            title={title}
            config={config}
            isSelected={selectedId === config.id}
            onSelect={() => onSelect(config.id)}
            onUpdate={(patch) => onUpdate(config.id, patch)}
            onRemove={() => onRemove(config.id)}
          />
        ))}
      </div>
    </section>
  );
}

// ── single config card ────────────────────────────────────────────

function ConfigCard({
  title,
  config,
  isSelected,
  onSelect,
  onUpdate,
  onRemove,
}: {
  title: string;
  config: ModelConfig;
  isSelected: boolean;
  onSelect: () => void;
  onUpdate: (patch: Partial<ModelConfig>) => void;
  onRemove: () => void;
}) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const [loadingModels, setLoadingModels] = useState(false);

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await testLlmConnection({
        apiUrl: config.apiUrl,
        apiKey: config.apiKey,
        model: config.model,
      });
      if (res.success) {
        setTestResult({ ok: true, msg: `✓ ${res.latency_ms}ms — ${res.response || "ok"}` });
      } else {
        setTestResult({ ok: false, msg: `✗ ${res.error || "连接失败"}` });
      }
    } catch (e: any) {
      setTestResult({ ok: false, msg: `✗ ${e.message || "请求失败"}` });
    } finally {
      setTesting(false);
    }
  };

  const handleListModels = async () => {
    setLoadingModels(true);
    try {
      const res = await listModels({ apiUrl: config.apiUrl, apiKey: config.apiKey });
      if (res.models?.length) {
        onUpdate({ availableModels: res.models });
      }
      if (res.error) {
        setTestResult({ ok: false, msg: `✗ ${res.error}` });
      }
    } catch (e: any) {
      setTestResult({ ok: false, msg: `✗ ${e.message || "获取失败"}` });
    } finally {
      setLoadingModels(false);
    }
  };

  const availableModels = config.availableModels;
  const showModelSelect = availableModels && availableModels.length > 0;

  return (
    <div className="rounded border border-line bg-panel p-3">
      <label className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink">
        <input
          type="radio"
          name={title}
          checked={isSelected}
          onChange={onSelect}
        />
        当前选择
        <span className="text-xs font-normal text-slate-500">{config.enabled ? "启用" : "停用"}</span>
        <button
          type="button"
          className="ml-auto inline-flex h-6 w-6 items-center justify-center rounded text-slate-400 hover:bg-red-50 hover:text-red-600"
          title="删除此配置"
          onClick={(e) => { e.preventDefault(); onRemove(); }}
        >
          <X size={14} />
        </button>
      </label>

      <div className="grid gap-3 md:grid-cols-2">
        <TextField
          label="名称"
          value={config.name}
          onChange={(name) => onUpdate({ name })}
        />
        {showModelSelect ? (
          <div className="space-y-1.5">
            <span className="text-xs font-medium text-slate-600">模型名</span>
            <select
              value={config.model}
              onChange={(e) => onUpdate({ model: e.target.value })}
              className="w-full rounded border border-line bg-white px-3 py-2 text-sm text-ink"
            >
              {availableModels.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
        ) : (
          <TextField
            label="模型名"
            value={config.model}
            onChange={(model) => onUpdate({ model })}
          />
        )}
        <TextField
          label="API 地址"
          value={config.apiUrl}
          onChange={(apiUrl) => onUpdate({ apiUrl })}
        />
        <TextField
          label="API Key"
          value={config.apiKey}
          type="password"
          onChange={(apiKey) => onUpdate({ apiKey })}
        />
      </div>

      {/* Buttons row */}
      <div className="mt-3 flex flex-wrap items-start gap-2">
        <button
          type="button"
          onClick={handleTest}
          disabled={testing}
          className="inline-flex items-center gap-1.5 rounded border border-line bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:border-action hover:text-action disabled:opacity-50"
        >
          <PlugZap size={13} />
          {testing ? "测试中…" : "测试连通"}
        </button>
        <button
          type="button"
          onClick={handleListModels}
          disabled={loadingModels}
          className="inline-flex items-center gap-1.5 rounded border border-line bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:border-action hover:text-action disabled:opacity-50"
        >
          <List size={13} />
          {loadingModels ? "获取中…" : `获取模型${showModelSelect ? ` (${availableModels!.length})` : ""}`}
        </button>

        {testResult && (
          <span className={`self-center text-xs ${testResult.ok ? "text-green-700" : "text-red-600"}`}>
            {testResult.msg}
          </span>
        )}
      </div>
    </div>
  );
}

// ── TextField (internal) ──────────────────────────────────────────

function TextField({
  label,
  value,
  type = "text",
  onChange,
}: {
  label: string;
  value: string;
  type?: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-1.5">
      <span className="text-xs font-medium text-slate-600">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded border border-line bg-white px-3 py-2 text-sm text-ink placeholder:text-slate-400"
      />
    </div>
  );
}
