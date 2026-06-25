"use client";

import { Plus, Settings, X } from "lucide-react";

import type { ModelConfig, ThemeStyle } from "@/types";

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
  onSelectLlmConfig: (id: string) => void;
  onSelectImageConfig: (id: string) => void;
};

const themeOptions: Array<{ value: ThemeStyle; label: string; swatch: string }> = [
  { value: "black", label: "黑色", swatch: "bg-slate-950" },
  { value: "blue", label: "蓝色", swatch: "bg-blue-700" },
  { value: "green", label: "绿色", swatch: "bg-teal-700" },
  { value: "white", label: "白色", swatch: "bg-white" },
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
  onSelectLlmConfig,
  onSelectImageConfig,
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
                    className="peer sr-only"
                  />
                  <span className="selectable-card flex items-center gap-2 rounded border border-line bg-white px-3 py-2 text-sm font-medium text-ink transition">
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
          />

          <ModelConfigSection
            title="生图模型配置"
            configs={imageConfigs}
            selectedId={selectedImageConfigId}
            onAdd={onAddImageConfig}
            onSelect={onSelectImageConfig}
            onUpdate={onUpdateImageConfig}
          />
        </div>
      </section>
    </div>
  );
}

function ModelConfigSection({
  title,
  configs,
  selectedId,
  onAdd,
  onSelect,
  onUpdate,
}: {
  title: string;
  configs: ModelConfig[];
  selectedId: string;
  onAdd: () => void;
  onSelect: (id: string) => void;
  onUpdate: (id: string, patch: Partial<ModelConfig>) => void;
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
          <div key={config.id} className="rounded border border-line bg-panel p-3">
            <label className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink">
              <input
                type="radio"
                name={title}
                checked={selectedId === config.id}
                onChange={() => onSelect(config.id)}
              />
              当前选择
              <span className="text-xs font-normal text-slate-500">{config.enabled ? "启用" : "停用"}</span>
            </label>

            <div className="grid gap-3 md:grid-cols-2">
              <TextField
                label="名称"
                value={config.name}
                onChange={(name) => onUpdate(config.id, { name })}
              />
              <TextField
                label="模型名"
                value={config.model}
                onChange={(model) => onUpdate(config.id, { model })}
              />
              <TextField
                label="API 地址"
                value={config.apiUrl}
                onChange={(apiUrl) => onUpdate(config.id, { apiUrl })}
              />
              <TextField
                label="API Key"
                value={config.apiKey}
                type="password"
                onChange={(apiKey) => onUpdate(config.id, { apiKey })}
              />
            </div>

            <label className="mt-3 flex items-center gap-2 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={config.enabled}
                onChange={(event) => onUpdate(config.id, { enabled: event.target.checked })}
              />
              启用此配置
            </label>
          </div>
        ))}
      </div>
    </section>
  );
}

function TextField({
  label,
  value,
  type = "text",
  onChange,
}: {
  label: string;
  value: string;
  type?: "text" | "password";
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-slate-600">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 w-full rounded border border-line bg-white px-3 py-2 text-sm text-ink outline-none focus:border-action"
      />
    </label>
  );
}
