import { create } from "zustand";

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

type PersistedSettings = {
  theme?: ThemeStyle;
  llmConfigs?: ModelConfig[];
  imageConfigs?: ModelConfig[];
  visionConfigs?: ModelConfig[];
  selectedLlmConfigId?: string;
  selectedImageConfigId?: string;
  selectedVisionConfigId?: string;
  provider?: string;
};

type PersistedDraft = {
  upload?: UploadResponse;
  job?: JobResponse;
  productInfo?: ProductInfo;
  platform?: Platform;
  kitTypes?: KitType[];
  kitSizes?: KitSizeMap;
};

const defaultLlmConfigs: ModelConfig[] = [
  {
    id: "llm-default",
    name: "DeepSeek V4 Flash",
    apiUrl: "https://api.deepseek.com",
    apiKey: "",
    model: "deepseek-v4-flash",
    enabled: true,
  },
];

const defaultVisionConfigs: ModelConfig[] = [
  {
    id: "vision-default",
    name: "Qwen3-VL (硅基流动)",
    apiUrl: "https://api.siliconflow.cn",
    apiKey: "",
    model: "Qwen/Qwen3-VL-32B-Instruct",
    enabled: true,
  },
];

const DYNAMIC_API = typeof window !== "undefined" ? `http://${window.location.hostname}:8000` : "http://localhost:8000";

const defaultImageConfigs: ModelConfig[] = [
  { id: "volcengine-ark", name: "火山方舟 Seedream", apiUrl: `${DYNAMIC_API}/api/generate`, apiKey: "", model: "volcengine-ark", enabled: true },
  { id: "fal-fast", name: "Fal.ai Flux Schnell", apiUrl: `${DYNAMIC_API}/api/generate`, apiKey: "", model: "fal-fast", enabled: true },
  { id: "fal-pro", name: "Fal.ai Flux Pro", apiUrl: `${DYNAMIC_API}/api/generate`, apiKey: "", model: "fal-pro", enabled: true },
  { id: "siliconflow-fast", name: "硅基流动 Flux Schnell", apiUrl: `${DYNAMIC_API}/api/generate`, apiKey: "", model: "siliconflow-fast", enabled: true },
  { id: "siliconflow-pro", name: "硅基流动 Flux Pro", apiUrl: `${DYNAMIC_API}/api/generate`, apiKey: "", model: "siliconflow-pro", enabled: true },
  { id: "agnes", name: "Agnes AI", apiUrl: `${DYNAMIC_API}/api/generate`, apiKey: "", model: "agnes", enabled: true },
  { id: "codex", name: "Codex Imagegen", apiUrl: `${DYNAMIC_API}/api/generate`, apiKey: "", model: "codex", enabled: true },
  { id: "mock", name: "Mock 本地合成", apiUrl: `${DYNAMIC_API}/api/generate`, apiKey: "", model: "mock", enabled: true },
];

function readPersistedSettings(): PersistedSettings {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(SETTINGS_STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
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
  "theme" | "llmConfigs" | "imageConfigs" | "visionConfigs" | "selectedLlmConfigId" | "selectedImageConfigId" | "selectedVisionConfigId" | "provider"
>) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(state));
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
  provider: string;
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
  setProvider: (provider: string) => void;
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
  clearDraft: () => void;
};

const VALID_THEMES = ["light", "dark", "white"];

const persisted = readPersistedSettings();
const persistedDraft = readPersistedDraft();

function defaultProductInfo(): ProductInfo {
  return {
    name: "", category: "", material: "", dimensions: "",
    sellingPoints: "", price: "", audience: "", usageScene: "", competitorDiff: ""
  };
}

function normalizeProductInfo(productInfo?: Partial<ProductInfo>): ProductInfo {
  return { ...defaultProductInfo(), ...(productInfo ?? {}) };
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
    provider: state.provider,
  };
}

function draftable(state: AppState) {
  return {
    upload: state.upload, job: state.job,
    productInfo: state.productInfo, platform: state.platform,
    kitTypes: state.kitTypes, kitSizes: state.kitSizes
  };
}

export const useAppStore = create<AppState>((set, get) => ({
  upload: persistedDraft.upload,
  job: persistedDraft.job,
  productInfo: normalizeProductInfo(persistedDraft.productInfo),
  platform: persistedDraft.platform ?? "taobao",
  kitTypes: persistedDraft.kitTypes?.length ? persistedDraft.kitTypes : ["main_white"],
  kitSizes: persistedDraft.kitSizes ?? {},
  provider: persisted.provider ?? "volcengine-ark",
  theme: (VALID_THEMES.includes(persisted.theme ?? "") ? persisted.theme : "light") as ThemeStyle,
  llmConfigs: persisted.llmConfigs?.length ? persisted.llmConfigs : defaultLlmConfigs,
  imageConfigs: persisted.imageConfigs?.length ? persisted.imageConfigs : defaultImageConfigs,
  visionConfigs: persisted.visionConfigs?.length ? persisted.visionConfigs : defaultVisionConfigs,
  selectedLlmConfigId: persisted.selectedLlmConfigId ?? "llm-default",
  selectedImageConfigId: persisted.selectedImageConfigId ?? "volcengine-ark",
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
  setProvider: (provider) =>
    set((state) => {
      const matched = state.imageConfigs.find((c) => c.model === provider || c.id === provider);
      const n = { provider, selectedImageConfigId: matched?.id ?? state.selectedImageConfigId };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  setTheme: (theme) =>
    set((state) => { const n = { theme }; writePersistedSettings({ ...persistable(state), ...n }); return n; }),

  addLlmConfig: () =>
    set((state) => {
      const id = `llm-${Date.now()}`;
      const n = { llmConfigs: [...state.llmConfigs, { id, name: "新大模型", apiUrl: "", apiKey: "", model: "", enabled: true }], selectedLlmConfigId: id };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  addImageConfig: () =>
    set((state) => {
      const id = `image-${Date.now()}`;
      const n = { imageConfigs: [...state.imageConfigs, { id, name: "新生图模型", apiUrl: "", apiKey: "", model: "", enabled: true }], selectedImageConfigId: id, provider: "" };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  addVisionConfig: () =>
    set((state) => {
      const id = `vision-${Date.now()}`;
      const n = { visionConfigs: [...state.visionConfigs, { id, name: "新视觉模型", apiUrl: "", apiKey: "", model: "", enabled: true }], selectedVisionConfigId: id };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),

  updateLlmConfig: (id, patch) =>
    set((state) => {
      const n = { llmConfigs: state.llmConfigs.map((c) => c.id === id ? { ...c, ...patch } : c) };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  updateImageConfig: (id, patch) =>
    set((state) => {
      const configs = state.imageConfigs.map((c) => c.id === id ? { ...c, ...patch } : c);
      const sel = configs.find((c) => c.id === state.selectedImageConfigId);
      const n = { imageConfigs: configs, provider: sel?.model ?? state.provider };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  updateVisionConfig: (id, patch) =>
    set((state) => {
      const n = { visionConfigs: state.visionConfigs.map((c) => c.id === id ? { ...c, ...patch } : c) };
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
      const n = { imageConfigs: configs, selectedImageConfigId: state.selectedImageConfigId === id ? (configs[0]?.id ?? "mock") : state.selectedImageConfigId };
      writePersistedSettings({ ...persistable(state), ...n });
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
      const sel = state.imageConfigs.find((c) => c.id === id);
      const n = { selectedImageConfigId: id, provider: sel?.model ?? state.provider };
      writePersistedSettings({ ...persistable(state), ...n });
      return n;
    }),
  selectVisionConfig: (id) =>
    set((state) => { const n = { selectedVisionConfigId: id }; writePersistedSettings({ ...persistable(state), ...n }); return n; }),

  clearDraft: () =>
    set((state) => {
      if (typeof window !== "undefined") window.localStorage.removeItem(DRAFT_STORAGE_KEY);
      const n = { upload: undefined, job: undefined, productInfo: defaultProductInfo(), platform: "taobao" as Platform, kitTypes: ["main_white"] as KitType[], kitSizes: {} };
      writePersistedSettings(persistable({ ...state, ...n }));
      return n;
    }),
}));
