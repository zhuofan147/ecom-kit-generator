import type { ModelConfig, ProductInfo } from "@/types";

export function canCreateStructuredPlan(productInfo: ProductInfo, hasUpload: boolean) {
  return hasUpload || Boolean(productInfo.rawInfo?.trim());
}

export function hasCompleteModelConfig(config?: Pick<ModelConfig, "apiUrl" | "apiKey" | "model">) {
  return Boolean(config?.apiUrl.trim() && config.apiKey.trim() && config.model.trim());
}
