import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { ProductInfoForm } from "./ProductInfoForm";

const productInfo = {
  rawInfo: "Insta360 X5，售价2999元，主打8K全景、防抖，适合旅行vlog。",
  name: "",
  category: "",
  material: "",
  dimensions: "",
  sellingPoints: "",
  price: "",
  audience: "",
  usageScene: "",
  competitorDiff: "",
};

describe("ProductInfoForm", () => {
  it("renders one customer-filled product info textarea instead of separate fields", () => {
    const markup = renderToStaticMarkup(
      <ProductInfoForm value={productInfo} onChange={vi.fn()} />
    );

    expect(markup).toContain("商品信息");
    expect(markup).toContain("整体填写");
    expect(markup).toContain("Insta360 X5");
    expect(markup).toMatch(/<textarea[\s\S]*<\/textarea>/);
    expect(markup).not.toContain("产品名称");
    expect(markup).not.toContain("核心卖点");
  });
});
