import { describe, expect, it } from "vitest";

import { buildGenerationPayload, buildPlanPayload } from "./api";

describe("API payload builders", () => {
  it("builds a plan payload from product planning fields", () => {
    const payload = buildPlanPayload({
      productId: "product-1",
      productInfo: {
        name: "无线蓝牙耳机",
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
      imageConfig: {
        apiUrl: "https://ark.cn-beijing.volces.com/api/v3",
        apiKey: "image-key",
        model: "doubao-seedream-5-0-260128"
      },
      visionConfig: {
        apiUrl: "https://api.siliconflow.cn",
        apiKey: "vision-key",
        model: "Qwen/Qwen3-VL-32B-Instruct"
      }
    });

    expect(payload.image_config).toEqual({
      apiUrl: "https://ark.cn-beijing.volces.com/api/v3",
      apiKey: "image-key",
      model: "doubao-seedream-5-0-260128"
    });
    expect(payload.vision_config).toEqual({
      apiUrl: "https://api.siliconflow.cn",
      apiKey: "vision-key",
      model: "Qwen/Qwen3-VL-32B-Instruct"
    });
  });
});
