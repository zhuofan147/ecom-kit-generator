import { describe, expect, it } from "vitest";

import {
  applyModelPreset,
  createBlankModelConfig,
  LLM_MODEL_PRESETS,
  VISION_MODEL_PRESETS,
  normalizeImageConfigId,
  normalizeImageConfigs,
  normalizeModelConfigs,
  normalizeProviders,
} from "./index";

describe("blank model configuration", () => {
  it("creates one empty configurable card without preset API values", () => {
    expect(createBlankModelConfig("llm-default", "新大模型")).toEqual({
      id: "llm-default",
      name: "",
      apiUrl: "",
      apiKey: "",
      model: "",
      enabled: false,
    });
    expect(normalizeModelConfigs(undefined, "llm-default", "新大模型")).toEqual([
      {
        id: "llm-default",
        name: "",
        apiUrl: "",
        apiKey: "",
        model: "",
        enabled: false,
      },
    ]);
  });
});

describe("image model presets", () => {
  it("writes preset merchant, model, and base_url into the current image card", () => {
    const config = {
      ...createBlankModelConfig("image-default", "新生图模型"),
      availableModels: ["agnes-image-2.1-flash"],
    };

    expect(applyModelPreset(config, "volcengine-ark")).toEqual({
      id: "image-default",
      name: "火山方舟 Seedream 5.0",
      apiUrl: "https://ark.cn-beijing.volces.com/api/v3",
      apiKey: "",
      model: "volcengine-ark",
      enabled: false,
      availableModels: undefined,
    });
  });
});

describe("llm and vision model presets", () => {
  it("provides presets for language and vision model cards", () => {
    expect(LLM_MODEL_PRESETS.length).toBeGreaterThan(0);
    expect(VISION_MODEL_PRESETS.length).toBeGreaterThan(0);
    expect(applyModelPreset(createBlankModelConfig("llm-default", "新大模型"), LLM_MODEL_PRESETS[0].id)).toMatchObject({
      name: LLM_MODEL_PRESETS[0].name,
      model: LLM_MODEL_PRESETS[0].model,
      apiUrl: LLM_MODEL_PRESETS[0].apiUrl,
      apiKey: "",
    });
    expect(applyModelPreset(createBlankModelConfig("vision-default", "新视觉模型"), VISION_MODEL_PRESETS[0].id)).toMatchObject({
      name: VISION_MODEL_PRESETS[0].name,
      model: VISION_MODEL_PRESETS[0].model,
      apiUrl: VISION_MODEL_PRESETS[0].apiUrl,
      apiKey: "",
    });
  });
});

describe("image model settings normalization", () => {
  it("migrates a legacy mock image config to VolcEngine Ark", () => {
    const configs = normalizeImageConfigs([
      {
        id: "mock",
        name: "Mock",
        apiUrl: "",
        apiKey: "",
        model: "mock",
        enabled: false,
      },
    ]);

    expect(configs).toEqual([
      {
        id: "mock",
        name: "火山方舟 Seedream 5.0",
        apiUrl: "",
        apiKey: "",
        model: "volcengine-ark",
        enabled: false,
      },
    ]);
    expect(normalizeProviders(configs, ["mock"])).toEqual([]);
    expect(normalizeImageConfigId(configs, "mock")).toBe("mock");
  });

  it("drops duplicate legacy mock config when a VolcEngine config already exists", () => {
    const configs = normalizeImageConfigs([
      {
        id: "volcengine-ark",
        name: "火山方舟 Seedream 5.0",
        apiUrl: "https://ark.cn-beijing.volces.com/api/v3",
        apiKey: "key",
        model: "volcengine-ark",
        enabled: true,
      },
      {
        id: "mock",
        name: "Mock",
        apiUrl: "",
        apiKey: "",
        model: "mock",
        enabled: true,
      },
    ]);

    expect(configs).toHaveLength(1);
    expect(configs[0].model).toBe("volcengine-ark");
    expect(normalizeProviders(configs, ["mock"])).toEqual(["volcengine-ark"]);
    expect(normalizeImageConfigId(configs, "mock")).toBe("volcengine-ark");
  });

  it("excludes disabled image configs from usable providers", () => {
    const configs = normalizeImageConfigs([
      {
        id: "agnes",
        name: "Agnes",
        apiUrl: "https://example.com",
        apiKey: "key",
        model: "agnes",
        enabled: false,
      },
      {
        id: "volcengine-ark",
        name: "火山方舟 Seedream 5.0",
        apiUrl: "https://ark.cn-beijing.volces.com/api/v3",
        apiKey: "key",
        model: "volcengine-ark",
        enabled: true,
      },
    ]);

    expect(normalizeProviders(configs, ["agnes", "volcengine-ark"])).toEqual(["volcengine-ark"]);
  });

  it("maps concrete Agnes model ids back to the Agnes provider", () => {
    const configs = normalizeImageConfigs([
      {
        id: "agnes-card",
        name: "Agnes",
        apiUrl: "https://apihub.agnes-ai.com/v1/images/generations",
        apiKey: "key",
        model: "agnes-image-2.1-flash",
        enabled: true,
      },
    ]);

    expect(normalizeProviders(configs)).toEqual(["agnes"]);
    expect(normalizeProviders(configs, ["agnes-image-2.1-flash"])).toEqual(["agnes"]);
  });
});
