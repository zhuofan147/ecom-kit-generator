import { create } from "zustand";

import { loadModelSettings, saveModelSettings, type SharedModelSettings } from "@/lib/api";
import type {
  JobResponse,
  KitSize,
  KitSizeMap,
  KitType,
  ModelConfig,
  Platform,
  ProductInfo,
  ThemeStyle,
  UploadResponse
} from "@/types";

const SETTINGS_STORAGE_KEY = "ecom-kit-generator-settings";
const DRAFT_STORAGE_KEY = "ecom-kit-generator-draft";
const CURRENT_SETTINGS_SCHEMA_VERSION = 2;

type PersistedSettings = {
  settingsVersion?: number;
  theme?: ThemeStyle;
  llmConfigs?: ModelConfig[];
  imageConfigs?: ModelConfig[];
  visionConfigs?: ModelConfig[];
  selectedLlmConfigId?: string;
  selectedImageConfigId?: string;
  selectedVisionConfigId?: string;
  providers?: string[];
};

type PersistedDraft = {
  upload?: UploadResponse;
  job?: JobResponse;
  productInfo?: ProductInfo;
  platform?: Platform;
  kitTypes?: KitType[];
  kitSizes?: KitSizeMap;
};

export function createBlankModelConfig(id: string, _label: string): ModelConfig {
  return {
    id,
    name: "",
    apiUrl: "",
    apiKey: "",
    model: "",
    enabled: false,
  };
}

const defaultLlmConfigs: ModelConfig[] = [
  createBlankModelConfig("llm-default", "新大模型"),
];

const defaultVisionConfigs: ModelConfig[] = [
  createBlankModelConfig("vision-default", "新视觉模型"),
];

const defaultImageConfigs: ModelConfig[] = [
  createBlankModelConfig("image-default", "新生图模型"),
];

export type ModelPreset = {
  id: string;
  name: string;
  model: string;
  apiUrl: string;
};

export const LLM_MODEL_PRESETS: ModelPreset[] = [
  {
    id: "deepseek-v4-flash",
    name: "DeepSeek V4 Flash",
    model: "deepseek-v4-flash",
    apiUrl: "https://api.deepseek.com",
  },
  {
    id: "qwen-plus",
    name: "通义千问 Qwen Plus",
    model: "qwen-plus",
    apiUrl: "https://dashscope.aliyuncs.com/compatible-mode/v1",
  },
  {
    id: "openai-gpt-4.1",
    name: "OpenAI GPT-4.1",
    model: "gpt-4.1",
    apiUrl: "https://api.openai.com/v1",
  },
];

export const VISION_MODEL_PRESETS: ModelPreset[] = [
  {
    id: "qwen-vl-siliconflow",
    name: "Qwen3-VL (硅基流动)",
    model: "Qwen/Qwen3-VL-32B-Instruct",
    apiUrl: "https://api.siliconflow.cn",
  },
  {
    id: "qwen-vl-sensenova",
    name: "Qwen3.6-Plus",
    model: "Qwen3.6-Plus",
    apiUrl: "https://api.scnet.cn/api/llm/v1",
  },
  {
    id: "openai-gpt-4.1-mini",
    name: "OpenAI GPT-4.1 mini",
    model: "gpt-4.1-mini",
    apiUrl: "https://api.openai.com/v1",
  },
];

export const IMAGE_MODEL_PRESETS: ModelPreset[] = [
  {
    id: "volcengine-ark",
    name: "火山方舟 Seedream 5.0",
    model: "volcengine-ark",
    apiUrl: "https://ark.cn-beijing.volces.com/api/v3",
  },
  {
    id: "agnes",
    name: "Agnes AI (免费)",
    model: "agnes",
    apiUrl: "https://apihub.agnes-ai.com/v1/images/generations",
  },
  {
    id: "codex",
    name: "Codex CLI (本地)",
    model: "codex",
    apiUrl: "",
  },
];

export const ALL_MODEL_PRESETS: ModelPreset[] = [
  ...LLM_MODEL_PRESETS,
  ...VISION_MODEL_PRESETS,
  ...IMAGE_MODEL_PRESETS,
];

const LEGACY_IMAGE_PROVIDER_ALIASES: Record<string, string> = {
  mock: "volcengine-ark",
};

export function normalizeImageProvider(value?: string): string {
  if (!value) return "";
  if (value.startsWith("agnes-image-")) return "agnes";
  if (value.includes("seedream") || value.startsWith("doubao-")) return "volcengine-ark";
  return LEGACY_IMAGE_PROVIDER_ALIASES[value] ?? value;
}

export async function syncEnabledProvidersToBackend(imageConfigs: ModelConfig[]) {
  const enabled = imageConfigs
    .filter(c => c.enabled !== false)
    .map(c => normalizeImageProvider(c.model || c.id))
    .filter(Boolean);
  try {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL || `http://${window?.location?.hostname || 'localhost'}:8000`;
    await fetch(`${base}/api/providers/enabled`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled_names: enabled }),
    });
  } catch {
    // silent – sync failures shouldn't block UI
  }
}

export function normalizeModelConfigs(configs: ModelConfig[] | undefined, defaultId: string, label: string): ModelConfig[] {
  return configs?.length ? configs : [createBlankModelConfig(defaultId, label)];
}

export function applyModelPreset(config: ModelConfig, presetId: string, presets: ModelPreset[] = ALL_MODEL_PRESETS): ModelConfig {
  const preset = presets.find((item) => item.id === presetId);
  if (!preset) return config;
  return {
    ...config,
    name: preset.name,
    model: preset.model,
    apiUrl: preset.apiUrl,
    availableModels: undefined,
  };
}

export function applyImageModelPreset(config: ModelConfig, presetId: string): ModelConfig {
  return applyModelPreset(config, presetId, IMAGE_MODEL_PRESETS);
}

function freshPersistedSettings(theme?: ThemeStyle): PersistedSettings {
  return {
    settingsVersion: CURRENT_SETTINGS_SCHEMA_VERSION,
    theme: VALID_THEMES.includes(theme ?? "") ? theme : "light",
    llmConfigs: defaultLlmConfigs,
    imageConfigs: defaultImageConfigs,
    visionConfigs: defaultVisionConfigs,
    selectedLlmConfigId: "llm-default",
    selectedImageConfigId: "image-default",
    selectedVisionConfigId: "vision-default",
    providers: [] as string[],
  };
}

function readPersistedSettings(): PersistedSettings {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as PersistedSettings;
    if (parsed.settingsVersion !== CURRENT_SETTINGS_SCHEMA_VERSION) {
      const fresh = freshPersistedSettings(parsed.theme);
      window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(fresh));
      return fresh;
    }
    return parsed;
  } catch {
    return {};
  }
}

function readPersistedDraft(): PersistedDraft {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(DRAFT_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function writePersistedSettings(state: Pick<
  AppState,
  "theme" | "llmConfigs" | "imageConfigs" | "visionConfigs" | "selectedLlmConfigId" | "selectedImageConfigId" | "selectedVisionConfigId" | "providers"
>) {
  if (typeof window === "undefined") return;
  const settings = toSharedSettings(state);
  window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(settings));
  void saveModelSettings(settings).catch(() => {
    // Local settings should continue to work even when the backend is restarting.
  });
}

function toSharedSettings(state: Pick<
  AppState,
  "theme" | "llmConfigs" | "imageConfigs" | "visionConfigs" | "selectedLlmConfigId" | "selectedImageConfigId" | "selectedVisionConfigId" | "providers"
>): SharedModelSettings {
  return {
    ...state,
    settingsVersion: CURRENT_SETTINGS_SCHEMA_VERSION,
  };
}

function writePersistedDraft(state: Pick<
  AppState,
  "upload" | "job" | "productInfo" | "platform" | "kitTypes" | "kitSizes"
>) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(state));
}

type AppState = {
  upload?: UploadResponse;
  job?: JobResponse;
  productInfo: ProductInfo;
  platform: Platform;
  kitTypes: KitType[];
  kitSizes: KitSizeMap;
  providers: string[];
  theme: ThemeStyle;
  llmConfigs: ModelConfig[];
  imageConfigs: ModelConfig[];
  visionConfigs: ModelConfig[];
  selectedLlmConfigId: string;
  selectedImageConfigId: string;
  selectedVisionConfigId: string;
  setUpload: (upload?: UploadResponse) => void;
  setJob: (job?: JobResponse) => void;
  setProductInfo: (productInfo: ProductInfo) => void;
  setPlatform: (platform: Platform) => void;
  setKitTypes: (kitTypes: KitType[]) => void;
  toggleKitType: (kitType: KitType) => void;
  setKitSize: (kitType: KitType, size?: KitSize) => void;
  toggleProvider: (model: string) => void;
  setTheme: (theme: ThemeStyle) => void;
  addLlmConfig: () => void;
  addImageConfig: () => void;
  addVisionConfig: () => void;
  updateLlmConfig: (id: string, patch: Partial<ModelConfig>) => void;
  updateImageConfig: (id: string, patch: Partial<ModelConfig>) => void;
  updateVisionConfig: (id: string, patch: Partial<ModelConfig>) => void;
  removeLlmConfig: (id: string) => void;
  removeImageConfig: (id: string) => void;
  removeVisionConfig: (id: string) => void;
  selectLlmConfig: (id: string) => void;
  selectImageConfig: (id: string) => void;
  selectVisionConfig: (id: string) => void;
  hydrateFromStorage: () => void;
  clearDraft: () => void;
};

const VALID_THEMES = ["light", "dark", "white"];

const persisted: PersistedSettings = {};
const persistedDraft: PersistedDraft = {};

function defaultProductInfo(): ProductInfo {
  return {
    rawInfo: "",
    name: "", category: "", material: "", dimensions: "",
    sellingPoints: "", price: "", audience: "", usageScene: "", competitorDiff: ""
  };
}

function normalizeProductInfo(productInfo?: Partial<ProductInfo>): ProductInfo {
  return { ...defaultProductInfo(), ...(productInfo ?? {}) };
}


export function normalizeImageConfigs(configs?: ModelConfig[]): ModelConfig[] {
  if (!configs?.length) return defaultImageConfigs;

  const hasVolcengineConfig = configs.some(
    (config) => normalizeImageProvider(config.model || config.id) === "volcengine-ark" &&
      config.model !== "mock" &&
      config.id !== "mock"
  );

  return configs.flatMap((config) => {
    const originalProvider = config.model || config.id;
    const provider = normalizeImageProvider(originalProvider);
    const isLegacyMock = originalProvider === "mock" || config.id === "mock";
    if (isLegacyMock && hasVolcengineConfig) return [];

    const preset = IMAGE_MODEL_PRESETS.find((item) => item.model === provider || item.id === provider);
    return [{
      ...config,
      name: isLegacyMock && preset ? preset.name : config.name,
      model: provider,
      enabled: config.enabled ?? false,
    }];
  });
}

export function normalizeImageConfigId(configs: ModelConfig[], selectedId?: string): string {
  if (selectedId && configs.some((config) => config.id === selectedId)) return selectedId;
  return configs[0]?.id ?? "";
}

function hasCompleteModelConfig(config: Pick<ModelConfig, "apiUrl" | "apiKey" | "model">): boolean {
  return Boolean(config.apiUrl.trim() && config.apiKey.trim() && config.model.trim());
}

export function normalizeProviders(configs: ModelConfig[], persistedProviders?: string[]): string[] {
  const enabledConfigs = configs.filter((config) => config.enabled !== false && hasCompleteModelConfig(config));
  if (!persistedProviders?.length) return enabledConfigs.length ? [normalizeImageProvider(enabledConfigs[0].model)] : [];
  return persistedProviders
    .map(normalizeImageProvider)
    .filter((p) => enabledConfigs.some((c) => normalizeImageProvider(c.model || c.id) === p));
}

function persistable(state: AppState) {
  return {
    theme: state.theme,
    llmConfigs: state.llmConfigs,
    imageConfigs: state.imageConfigs,
    visionConfigs: state.visionConfigs,
    selectedLlmConfigId: state.selectedLlmConfigId,
    selectedImageConfigId: state.selectedImageConfigId,
    selectedVisionConfigId: state.selectedVisionConfigId,
    providers: state.providers,
  };
}

function draftable(state: AppState) {
  return {
    upload: state.upload, job: state.job,
    productInfo: state.productInfo, platform: state.platform,
    kitTypes: state.kitTypes, kitSizes: state.kitSizes
  };
}

function hasAnyModelSettings(settings: PersistedSettings): boolean {
  const configs = [
    ...(settings.llmConfigs ?? []),
    ...(settings.imageConfigs ?? []),
    ...(settings.visionConfigs ?? []),
  ];
  return configs.some((config) => Boolean(
    config.name.trim() ||
    config.apiUrl.trim() ||
    config.apiKey.trim() ||
    config.model.trim() ||
    config.availableModels?.length
  ));
}

async function hydrateSettingsFromBackend(
  get: () => AppState,
  set: (partial: Partial<AppState>) => void,
  localSettings: PersistedSettings,
) {
  if (typeof window === "undefined") return;
  try {
    const remoteSettings = await loadModelSettings();
    if (!remoteSettings) {
      if (hasAnyModelSettings(localSettings)) {
        await saveModelSettings(toSharedSettings(persistable(get())));
      }
      return;
    }

    const nextImageConfigs = normalizeImageConfigs(remoteSettings.imageConfigs);
    const nextState = {
      providers: normalizeProviders(nextImageConfigs, remoteSettings.providers),
      theme: (VALID_THEMES.includes(remoteSettings.theme ?? "") ? remoteSettings.theme : "light") as ThemeStyle,
      llmConfigs: normalizeModelConfigs(remoteSettings.llmConfigs, "llm-default", "新大模型"),
      imageConfigs: nextImageConfigs,
      visionConfigs: normalizeModelConfigs(remoteSettings.visionConfigs, "vision-default", "新视觉模型"),
      selectedLlmConfigId: remoteSettings.selectedLlmConfigId ?? "llm-default",
      selectedImageConfigId: normalizeImageConfigId(nextImageConfigs, remoteSettings.selectedImageConfigId),
      selectedVisionConfigId: remoteSettings.selectedVisionConfigId ?? "vision-default",
    };
    window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(toSharedSettings(nextState)));
    syncEnabledProvidersToBackend(nextImageConfigs);
    set(nextState);
  } catch {
    // Keep using origin-local settings when the backend is unavailable.
  }
}

export const useAppStore = create<AppState>((set, get) => ({
  upload: persistedDraft.upload,
  job: persistedDraft.job,
  productInfo: normalizeProductInfo(persistedDraft.productInfo),
  platform: persistedDraft.platform ?? "taobao",
  kitTypes: persistedDraft.kitTypes?.length ? persistedDraft.kitTypes : ["main_white"],
  kitSizes: persistedDraft.kitSizes ?? {},
  providers: normalizeProviders(normalizeImageConfigs(persisted.imageConfigs), persisted.providers),
  theme: (VALID_THEMES.includes(persisted.theme ?? "") ? persisted.theme : "light") as ThemeStyle,
  llmConfigs: persisted.llmConfigs?.length ? persisted.llmConfigs : defaultLlmConfigs,
  imageConfigs: normalizeImageConfigs(persisted.imageConfigs),
  visionConfigs: normalizeModelConfigs(persisted.visionConfigs, "vision-default", "新视觉模型"),
  selectedLlmConfigId: persisted.selectedLlmConfigId ?? "llm-default",
  selectedImageConfigId: normalizeImageConfigId(normalizeImageConfigs(persisted.imageConfigs), persisted.selectedImageConfigId),
  selectedVisionConfigId: persisted.selectedVisionConfigId ?? "vision-default",

  setUpload: (upload) =>
    set((state) => { const n = { upload }; writePersistedDraft({ ...draftable(state), ...n }); return n; }),
  setJob: (job) =>
    set((state) => { const n = { job }; writePersistedDraft({ ...draftable(state), ...n }); return n; }),
  setProductInfo: (productInfo) =>
    set((state) => { const n = { productInfo }; writePersistedDraft({ ...draftable(state), ...n }); return n; }),
  setPlatform: (platform) =>
    set((state) => { const n = { platform }; writePersistedDraft({ ...draftable(state), ...n }); return n; }),
  setKitTypes: (kitTypes) =>
    set((state) => { const n = { kitTypes }; writePersistedDraft({ ...draftable(state), ...n }); return n; }),
  toggleKitType: (kitType) =>
    set((state) => {
      const has = state.kitTypes.includes(kitType);
      const n = has ? state.kitTypes.filter((k) => k !== kitType) : [...state.kitTypes, kitType];
      const p = { kitTypes: n.length > 0 ? n : state.kitTypes };
      writePersistedDraft({ ...draftable(state), ...p });
      return p;
    }),
  setKitSize: (kitType, size) =>
    set((state) => {
      const nextSizes = { ...state.kitSizes };
      if (size) nextSizes[kitType] = size; else delete nextSizes[kitType];
      const p = { kitSizes: nextSizes };
      writePersistedDraft({ ...draftable(state), ...p });
      return p;
    }),
  toggleProvider: (model) =>
    set((state) => {
      const idx = state.providers.indexOf(model);
      const nextProviders = idx >= 0
        ? state.providers.filter((p) => p !== model)
        : [...state.providers, model];
      writePersistedSettings({ ...persistable(state), providers: nextProviders });
      return { providers: nextProviders };
    }),
  setTheme: (theme) =>
    set((state) => { const n = { theme }; writePersistedSettings({ ...persistable(state), ...n }); return n; }),

  addLlmConfig: () =>
    set((state) => {
      const id = `llm-${Date.now()}`;
      const n = { llmConfigs: [...state.llmConfigs, { id, name: "新大模型", apiUrl: "", apiKey: "", model: "", enabled: false }], selectedLlmConfigId: id };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  addImageConfig: () =>
    set((state) => {
      const id = `image-${Date.now()}`;
      const configs = [...state.imageConfigs, { id, name: "新生图模型", apiUrl: "", apiKey: "", model: "", enabled: false }];
      const n = { imageConfigs: configs, selectedImageConfigId: id };
      writePersistedSettings({ ...persistable(state), ...n });
      syncEnabledProvidersToBackend(configs);
      return n;
    }),
  addVisionConfig: () =>
    set((state) => {
      const id = `vision-${Date.now()}`;
      const n = { visionConfigs: [...state.visionConfigs, { id, name: "新视觉模型", apiUrl: "", apiKey: "", model: "", enabled: false }], selectedVisionConfigId: id };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),

  updateLlmConfig: (id, patch) =>
    set((state) => {
      const n = {
        llmConfigs: state.llmConfigs.map((c) =>
          c.id === id
            ? { ...c, ...patch }
            : patch.enabled === true
              ? { ...c, enabled: false }
              : c,
        ),
      };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  updateImageConfig: (id, patch) =>
    set((state) => {
      const configs = state.imageConfigs.map((c) => c.id === id ? { ...c, ...patch } : c);
      const n = { imageConfigs: configs, providers: normalizeProviders(configs, state.providers) };
      writePersistedSettings({ ...persistable(state), ...n });
      syncEnabledProvidersToBackend(configs);
      return n;
    }),
  updateVisionConfig: (id, patch) =>
    set((state) => {
      const n = {
        visionConfigs: state.visionConfigs.map((c) =>
          c.id === id
            ? { ...c, ...patch }
            : patch.enabled === true
              ? { ...c, enabled: false }
              : c,
        ),
      };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),

  removeLlmConfig: (id) =>
    set((state) => {
      const configs = state.llmConfigs.filter((c) => c.id !== id);
      const n = { llmConfigs: configs, selectedLlmConfigId: state.selectedLlmConfigId === id ? (configs[0]?.id ?? "llm-default") : state.selectedLlmConfigId };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  removeImageConfig: (id) =>
    set((state) => {
      const configs = state.imageConfigs.filter((c) => c.id !== id);
      const n = {
        imageConfigs: configs,
        selectedImageConfigId: state.selectedImageConfigId === id ? (configs[0]?.id ?? "") : state.selectedImageConfigId,
        providers: normalizeProviders(configs, state.providers),
      };
      writePersistedSettings({ ...persistable(state), ...n });
      syncEnabledProvidersToBackend(configs);
      return n;
    }),
  removeVisionConfig: (id) =>
    set((state) => {
      const configs = state.visionConfigs.filter((c) => c.id !== id);
      const n = { visionConfigs: configs, selectedVisionConfigId: state.selectedVisionConfigId === id ? (configs[0]?.id ?? "vision-default") : state.selectedVisionConfigId };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),

  selectLlmConfig: (id) =>
    set((state) => { const n = { selectedLlmConfigId: id }; writePersistedSettings({ ...persistable(state), ...n }); return n; }),
  selectImageConfig: (id) =>
    set((state) => {
      const cfg = state.imageConfigs.find(c => c.id === id);
      const provider = cfg ? normalizeImageProvider(cfg.model || cfg.id) : "";
      const n = {
        selectedImageConfigId: id,
        providers: provider ? [provider] : state.providers,
      };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  selectVisionConfig: (id) =>
    set((state) => { const n = { selectedVisionConfigId: id }; writePersistedSettings({ ...persistable(state), ...n }); return n; }),

  hydrateFromStorage: () =>
    set(() => {
      const nextSettings = readPersistedSettings();
      const nextDraft = readPersistedDraft();
      const nextImageConfigs = normalizeImageConfigs(nextSettings.imageConfigs);
      void hydrateSettingsFromBackend(get, set, nextSettings);
      return {
        upload: nextDraft.upload,
        job: nextDraft.job,
        productInfo: normalizeProductInfo(nextDraft.productInfo),
        platform: nextDraft.platform ?? "taobao",
        kitTypes: nextDraft.kitTypes?.length ? nextDraft.kitTypes : ["main_white"],
        kitSizes: nextDraft.kitSizes ?? {},
        providers: normalizeProviders(nextImageConfigs, nextSettings.providers),
        theme: (VALID_THEMES.includes(nextSettings.theme ?? "") ? nextSettings.theme : "light") as ThemeStyle,
        llmConfigs: normalizeModelConfigs(nextSettings.llmConfigs, "llm-default", "新大模型"),
        imageConfigs: nextImageConfigs,
        visionConfigs: normalizeModelConfigs(nextSettings.visionConfigs, "vision-default", "新视觉模型"),
        selectedLlmConfigId: nextSettings.selectedLlmConfigId ?? "llm-default",
        selectedImageConfigId: normalizeImageConfigId(nextImageConfigs, nextSettings.selectedImageConfigId),
        selectedVisionConfigId: nextSettings.selectedVisionConfigId ?? "vision-default",
      };
    }),

  clearDraft: () =>
    set((state) => {
      if (typeof window !== "undefined") window.localStorage.removeItem(DRAFT_STORAGE_KEY);
      const n = { upload: undefined, job: undefined, productInfo: defaultProductInfo(), platform: "taobao" as Platform, kitTypes: ["main_white"] as KitType[], kitSizes: {} };
      writePersistedSettings(persistable({ ...state, ...n }));
      return n;
    }),
}));
