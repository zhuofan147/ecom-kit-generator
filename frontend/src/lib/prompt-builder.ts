import type { Platform, ProductInfo } from "@/types";
import { platformRules } from "./platform-rules";

export function buildPrompt(input: { platform: Platform; productInfo: Partial<ProductInfo> }) {
  const rule = platformRules[input.platform];
  const points = (input.productInfo.sellingPoints || "")
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean)
    .join(", ");

  return [
    `Commercial ecommerce product photo of ${input.productInfo.name || "产品"}`,
    input.productInfo.category ? `category: ${input.productInfo.category}` : "",
    input.productInfo.material ? `material and texture: ${input.productInfo.material}` : "",
    points ? `selling points: ${points}` : "",
    "preserve exact product identity, shape, material, color, logo, and texture",
    "studio lighting, soft natural shadow, realistic img2img refinement",
    rule.requirement,
    `${rule.width}x${rule.height}`
  ]
    .filter(Boolean)
    .join(", ");
}
