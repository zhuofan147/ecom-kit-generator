import { describe, expect, it } from "vitest";

import { canCreateStructuredPlan, hasCompleteModelConfig } from "./planning";

const emptyProductInfo = {
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

describe("planning helpers", () => {
  it("allows structured planning from raw product text without an upload", () => {
    expect(canCreateStructuredPlan({ ...emptyProductInfo, rawInfo: "Insta360 X5 售价2999元" }, false)).toBe(true);
  });

  it("allows structured planning from an upload even when product text is empty", () => {
    expect(canCreateStructuredPlan(emptyProductInfo, true)).toBe(true);
  });

  it("requires either product text or an upload", () => {
    expect(canCreateStructuredPlan(emptyProductInfo, false)).toBe(false);
  });

  it("requires base_url, api key, and model for a usable model config", () => {
    expect(hasCompleteModelConfig({ apiUrl: "https://api.example.com", apiKey: "key", model: "model" })).toBe(true);
    expect(hasCompleteModelConfig({ apiUrl: "", apiKey: "key", model: "model" })).toBe(false);
    expect(hasCompleteModelConfig({ apiUrl: "https://api.example.com", apiKey: "", model: "model" })).toBe(false);
    expect(hasCompleteModelConfig({ apiUrl: "https://api.example.com", apiKey: "key", model: "" })).toBe(false);
  });
});
