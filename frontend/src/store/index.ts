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
  selectedLlmConfigId?: string;
  selectedImageConfigId?: string;
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
    name: "默认大模型",
    apiUrl: "https://api.openai.com/v1",
    apiKey: "",
    model: "gpt-4.1",
    enabled: true,
  },
];

const DYNAMIC_API = typeof window !== "undefined" ? `http://${window.location.hostname}:8000` : "http://localhost:8000";

const defaultImageConfigs: ModelConfig[] = [
  {
    id: "agnes",
    name: "Agnes 生图",
    apiUrl: `${DYNAMIC_API}/api/generate`,
    apiKey: "",
    model: "agnes",
    enabled: true,
  },
  {
    id: "mock",
    name: "Mock 本地合成",
    apiUrl: `${DYNAMIC_API}/api/generate`,
    apiKey: "",
    model: "mock",
    enabled: true,
  },
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
  "theme" | "llmConfigs" | "imageConfigs" | "selectedLlmConfigId" | "selectedImageConfigId" | "provider"
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
  selectedLlmConfigId: string;
  selectedImageConfigId: string;
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
  updateLlmConfig: (id: string, patch: Partial<ModelConfig>) => void;
  updateImageConfig: (id: string, patch: Partial<ModelConfig>) => void;
  selectLlmConfig: (id: string) => void;
  selectImageConfig: (id: string) => void;
  clearDraft: () => void;
};

const persisted = readPersistedSettings();
const persistedDraft = readPersistedDraft();

function defaultProductInfo(): ProductInfo {
  return {
    name: "",
    category: "",
    material: "",
    dimensions: "",
    sellingPoints: "",
    price: "",
    audience: "",
    usageScene: "",
    competitorDiff: ""
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
    selectedLlmConfigId: state.selectedLlmConfigId,
    selectedImageConfigId: state.selectedImageConfigId,
    provider: state.provider,
  };
}

function draftable(state: AppState) {
  return {
    upload: state.upload,
    job: state.job,
    productInfo: state.productInfo,
    platform: state.platform,
    kitTypes: state.kitTypes,
    kitSizes: state.kitSizes,
  };
}

export const useAppStore = create<AppState>((set, get) => ({
  upload: persistedDraft.upload,
  job: persistedDraft.job,
  productInfo: normalizeProductInfo(persistedDraft.productInfo),
  platform: persistedDraft.platform ?? "taobao",
  kitTypes: persistedDraft.kitTypes?.length ? persistedDraft.kitTypes : ["main_white"],
  kitSizes: persistedDraft.kitSizes ?? {},
  provider: persisted.provider ?? "agnes",
  theme: persisted.theme ?? "green",
  llmConfigs: persisted.llmConfigs?.length ? persisted.llmConfigs : defaultLlmConfigs,
  imageConfigs: persisted.imageConfigs?.length ? persisted.imageConfigs : defaultImageConfigs,
  selectedLlmConfigId: persisted.selectedLlmConfigId ?? "llm-default",
  selectedImageConfigId: persisted.selectedImageConfigId ?? "agnes",
  setUpload: (upload) =>
    set((state) => {
      const next = { upload };
      writePersistedDraft({ ...draftable(state), ...next });
      return next;
    }),
  setJob: (job) =>
    set((state) => {
      const next = { job };
      writePersistedDraft({ ...draftable(state), ...next });
      return next;
    }),
  setProductInfo: (productInfo) =>
    set((state) => {
      const next = { productInfo };
      writePersistedDraft({ ...draftable(state), ...next });
      return next;
    }),
  setPlatform: (platform) =>
    set((state) => {
      const next = { platform };
      writePersistedDraft({ ...draftable(state), ...next });
      return next;
    }),
  setKitTypes: (kitTypes) =>
    set((state) => {
      const next = { kitTypes };
      writePersistedDraft({ ...draftable(state), ...next });
      return next;
    }),
  toggleKitType: (kitType) =>
    set((state) => {
      const has = state.kitTypes.includes(kitType);
      const next = has
        ? state.kitTypes.filter((k) => k !== kitType)
        : [...state.kitTypes, kitType];
      // Keep at least one selected
      const patch = { kitTypes: next.length > 0 ? next : state.kitTypes };
      writePersistedDraft({ ...draftable(state), ...patch });
      return patch;
    }),
  setKitSize: (kitType, size) =>
    set((state) => {
      const nextSizes = { ...state.kitSizes };
      if (size) {
        nextSizes[kitType] = size;
      } else {
        delete nextSizes[kitType];
      }
      const patch = { kitSizes: nextSizes };
      writePersistedDraft({ ...draftable(state), ...patch });
      return patch;
    }),
  setProvider: (provider) =>
    set((state) => {
      const matched = state.imageConfigs.find((config) => config.model === provider || config.id === provider);
      const next = {
        provider,
        selectedImageConfigId: matched?.id ?? state.selectedImageConfigId,
      };
      writePersistedSettings({ ...persistable(state), ...next });
      return next;
    }),
  setTheme: (theme) =>
    set((state) => {
      const next = { theme };
      writePersistedSettings({ ...persistable(state), ...next });
      return next;
    }),
  addLlmConfig: () =>
    set((state) => {
      const id = `llm-${Date.now()}`;
      const next = {
        llmConfigs: [
          ...state.llmConfigs,
          {
            id,
            name: "新大模型",
            apiUrl: "",
            apiKey: "",
            model: "",
            enabled: true,
          },
        ],
        selectedLlmConfigId: id,
      };
      writePersistedSettings({ ...persistable(state), ...next });
      return next;
    }),
  addImageConfig: () =>
    set((state) => {
      const id = `image-${Date.now()}`;
      const next = {
        imageConfigs: [
          ...state.imageConfigs,
          {
            id,
            name: "新生图模型",
            apiUrl: "",
            apiKey: "",
            model: "",
            enabled: true,
          },
        ],
        selectedImageConfigId: id,
        provider: "",
      };
      writePersistedSettings({ ...persistable(state), ...next });
      return next;
    }),
  updateLlmConfig: (id, patch) =>
    set((state) => {
      const next = {
        llmConfigs: state.llmConfigs.map((config) =>
          config.id === id ? { ...config, ...patch } : config
        ),
      };
      writePersistedSettings({ ...persistable(state), ...next });
      return next;
    }),
  updateImageConfig: (id, patch) =>
    set((state) => {
      const imageConfigs = state.imageConfigs.map((config) =>
        config.id === id ? { ...config, ...patch } : config
      );
      const selected = imageConfigs.find((config) => config.id === state.selectedImageConfigId);
      const next = {
        imageConfigs,
        provider: selected?.model ?? state.provider,
      };
      writePersistedSettings({ ...persistable(state), ...next });
      return next;
    }),
  selectLlmConfig: (id) =>
    set((state) => {
      const next = { selectedLlmConfigId: id };
      writePersistedSettings({ ...persistable(state), ...next });
      return next;
    }),
  selectImageConfig: (id) =>
    set((state) => {
      const selected = state.imageConfigs.find((config) => config.id === id);
      const next = {
        selectedImageConfigId: id,
        provider: selected?.model ?? state.provider,
      };
      writePersistedSettings({ ...persistable(state), ...next });
      return next;
    }),
  clearDraft: () =>
    set((state) => {
      if (typeof window !== "undefined") {
        window.localStorage.removeItem(DRAFT_STORAGE_KEY);
      }
      const next = {
        upload: undefined,
        job: undefined,
        productInfo: defaultProductInfo(),
        platform: "taobao" as Platform,
        kitTypes: ["main_white"] as KitType[],
        kitSizes: {},
      };
      writePersistedSettings(persistable({ ...state, ...next }));
      return next;
    }),
}));
