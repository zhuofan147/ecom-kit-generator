import { afterEach, describe, expect, it, vi } from "vitest";

import { buildGenerationPayload, buildPlanPayload, listModels, loadModelSettings, saveModelSettings } from "./api";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe("API payload builders", () => {
  it("builds a plan payload from product planning fields", () => {
    const payload = buildPlanPayload({
      productId: "product-1",
      productInfo: {
        name: "无线蓝牙耳机",
        rawInfo: "无线蓝牙耳机，售价199元，适合通勤，主打降噪和长续航。",
        category: "3C",
        material: "哑光黑",
        dimensions: "",
        sellingPoints: "降噪\n长续航",
        price: "199",
        audience: "通勤上班族",
        usageScene: "地铁通勤",
        competitorDiff: "续航更久"
      },
      platform: "taobao",
      kitTypes: ["main_white", "detail_page"],
      kitSizes: {
        detail_page: { w: 1080, h: 1920 }
      }
    });

    expect(payload.product_id).toBe("product-1");
    expect(payload.product_name).toBe("无线蓝牙耳机");
    expect(payload.product_raw_info).toContain("无线蓝牙耳机，售价199元");
    expect(payload.product_price).toBe("199");
    expect(payload.target_audience).toBe("通勤上班族");
    expect(payload.usage_scene).toBe("地铁通勤");
    expect(payload.selling_points).toContain("降噪");
    expect(payload.competitor_diff).toBe("续航更久");
    expect(payload.kit_types).toEqual(["main_white", "detail_page"]);
    expect(payload.kit_sizes.detail_page).toEqual({ w: 1080, h: 1920 });
  });

  it("includes planned prompts in generation payload", () => {
    const payload = buildGenerationPayload({
      productId: "product-1",
      platform: "taobao",
      productInfo: {
        name: "无线蓝牙耳机",
        category: "3C",
        material: "哑光黑",
        dimensions: "",
        sellingPoints: "降噪",
        price: "199",
        audience: "通勤上班族",
        usageScene: "地铁通勤",
        competitorDiff: ""
      },
      kitTypes: ["main_white"],
      kitSizes: {
        main_white: { w: 1080, h: 1080 }
      },
      plannedPrompts: {
        main_white: "六段式提示词"
      }
    });

    expect(payload.kit_types).toEqual(["main_white"]);
    expect(payload.kit_sizes.main_white).toEqual({ w: 1080, h: 1080 });
    expect(payload.product_info.planned_prompts.main_white).toBe("六段式提示词");
  });

  it("keeps planned prompts as Chinese strings before backend translation", () => {
    const payload = buildGenerationPayload({
      productId: "product-1",
      platform: "taobao",
      productInfo: {
        name: "无线蓝牙耳机",
        category: "3C",
        material: "哑光黑",
        dimensions: "",
        sellingPoints: "降噪",
        price: "199",
        audience: "通勤上班族",
        usageScene: "地铁通勤",
        competitorDiff: ""
      },
      kitTypes: ["main_white"],
      plannedPrompts: {
        main_white: "中文生图提示词",
      }
    });

    expect(payload.product_info.planned_prompts.main_white).toBe("中文生图提示词");
  });

  it("includes selected image and vision configs in generation payload", () => {
    const payload = buildGenerationPayload({
      productId: "product-1",
      platform: "taobao",
      productInfo: {
        name: "无线蓝牙耳机",
        category: "3C",
        material: "哑光黑",
        dimensions: "",
        sellingPoints: "降噪",
        price: "199",
        audience: "通勤上班族",
        usageScene: "地铁通勤",
        competitorDiff: ""
      },
      kitTypes: ["main_white"],
      imageConfigs: [{
        apiUrl: "https://ark.cn-beijing.volces.com/api/v3",
        apiKey: "image-key",
        model: "doubao-seedream-5-0-260128"
      }],
      visionConfig: {
        apiUrl: "https://api.siliconflow.cn",
        apiKey: "vision-key",
        model: "Qwen/Qwen3-VL-32B-Instruct"
      }
    });

    expect(payload.image_configs).toEqual([{
      apiUrl: "https://ark.cn-beijing.volces.com/api/v3",
      apiKey: "image-key",
      model: "doubao-seedream-5-0-260128"
    }]);
    expect(payload.vision_config).toEqual({
      apiUrl: "https://api.siliconflow.cn",
      apiKey: "vision-key",
      model: "Qwen/Qwen3-VL-32B-Instruct"
    });
  });

  it("sends model type when listing vision models", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ models: [] }), { status: 200 }));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await listModels({
      apiUrl: "https://api.example.com/v1",
      apiKey: "key",
      modelType: "vision",
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const call = (fetchMock as any).mock.calls[0];
    expect(JSON.parse(call[1].body)).toMatchObject({
      api_url: "https://api.example.com/v1",
      api_key: "key",
      model_type: "vision",
    });
  });

  it("sends model type when listing image models", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ models: [] }), { status: 200 }));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await listModels({
      apiUrl: "https://api.example.com/v1",
      apiKey: "key",
      modelType: "image",
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const call = (fetchMock as any).mock.calls[0];
    expect(JSON.parse(call[1].body)).toMatchObject({
      api_url: "https://api.example.com/v1",
      api_key: "key",
      model_type: "image",
    });
  });

  it("loads shared model settings from the backend", async () => {
    const settings = {
      settingsVersion: 2,
      theme: "light",
      llmConfigs: [{ id: "llm-1", name: "LLM", apiUrl: "https://api.example.com/v1", apiKey: "key", model: "model", enabled: true }],
      imageConfigs: [],
      visionConfigs: [],
      selectedLlmConfigId: "llm-1",
      selectedImageConfigId: "",
      selectedVisionConfigId: "",
      providers: [],
    };
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ settings }), { status: 200 }));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await expect(loadModelSettings()).resolves.toEqual(settings);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    expect((fetchMock as any).mock.calls[0][0]).toBe("http://localhost:8000/api/settings");
  });

  it("saves shared model settings to the backend", async () => {
    const fetchMock = vi.fn(async () => new Response(JSON.stringify({ ok: true }), { status: 200 }));
    globalThis.fetch = fetchMock as unknown as typeof fetch;
    const settings = {
      settingsVersion: 2,
      theme: "light" as const,
      llmConfigs: [{ id: "llm-1", name: "LLM", apiUrl: "https://api.example.com/v1", apiKey: "key", model: "model", enabled: true }],
      imageConfigs: [],
      visionConfigs: [],
      selectedLlmConfigId: "llm-1",
      selectedImageConfigId: "",
      selectedVisionConfigId: "",
      providers: [],
    };

    await saveModelSettings(settings);

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const call = (fetchMock as any).mock.calls[0];
    expect(call[0]).toBe("http://localhost:8000/api/settings");
    expect(call[1].method).toBe("POST");
    expect(JSON.parse(call[1].body)).toEqual(settings);
  });
});
