import { describe, expect, it } from "vitest";

import { buildPrompt } from "./prompt-builder";
import { platformRules } from "./platform-rules";

describe("Phase 1 platform prompt", () => {
  it("uses Taobao as an 800x800 white background default", () => {
    expect(platformRules.taobao.width).toBe(800);
    expect(platformRules.taobao.height).toBe(800);
    expect(platformRules.taobao.background).toBe("white");
  });

  it("supports offline store poster as the Other platform", () => {
    expect(platformRules.offline_store.label).toBe("其他");
    expect(platformRules.offline_store.width).toBe(1080);
    expect(platformRules.offline_store.height).toBe(1440);
    expect(platformRules.offline_store.requirement).toContain("线下门店");

    const prompt = buildPrompt({
      platform: "offline_store",
      productInfo: {
        name: "门店新品",
        sellingPoints: "到店体验\n限时优惠"
      }
    });

    expect(prompt).toContain("门店新品");
    expect(prompt).toContain("线下门店");
    expect(prompt).toContain("1080x1440");
  });

  it("stitches product info into the prompt", () => {
    const prompt = buildPrompt({
      platform: "taobao",
      productInfo: {
        name: "无线蓝牙耳机",
        material: "哑光黑色塑料",
        sellingPoints: "长续航\n低延迟"
      }
    });

    expect(prompt).toContain("无线蓝牙耳机");
    expect(prompt).toContain("哑光黑色塑料");
    expect(prompt).toContain("长续航");
    expect(prompt).toContain("800x800");
  });
});
