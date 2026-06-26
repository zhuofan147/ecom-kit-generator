import type { JobResponse, KitSizeMap, KitType, ModelConfig, Platform, ProductInfo, ProductPlan, UploadResponse } from "@/types";

type ApiModelConfig = Pick<ModelConfig, "apiUrl" | "apiKey" | "model">;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ||
  (typeof window !== "undefined" ? `http://${window.location.hostname}:8000` : "http://localhost:8000");

export function assetUrl(path: string) {
  if (path.startsWith("http")) return path;
  return `${API_BASE_URL}${path}`;
}

export async function uploadProductImage(files: File | File[]): Promise<UploadResponse> {
  const formData = new FormData();
  const imageFiles = Array.isArray(files) ? files : [files];
  for (const file of imageFiles) {
    formData.append("files", file);
  }

  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: formData
  });
  return parseResponse(response);
}

export async function createGenerationJob(input: {
  productId: string;
  platform: Platform;
  productInfo: ProductInfo;
  kitTypes: KitType[];
  kitSizes?: KitSizeMap;
  plannedPrompts?: Partial<Record<KitType, string>>;
  provider?: string;
  llmConfig?: ApiModelConfig;
  imageConfig?: ApiModelConfig;
  visionConfig?: ApiModelConfig;
}) {
  const response = await fetch(`${API_BASE_URL}/api/generate/kit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({...buildGenerationPayload(input), provider: input.provider || "agnes", run_plan: false, llm_config: modelConfigPayload(input.llmConfig)})
  });
  return parseResponse<{ job_id: string; status: string; total_images: number }>(response);
}

export async function createProductPlan(input: {
  productId?: string;
  productInfo: ProductInfo;
  platform: Platform;
  kitTypes: KitType[];
  kitSizes?: KitSizeMap;
  llmConfig?: ApiModelConfig;
  visionConfig?: ApiModelConfig;
}): Promise<ProductPlan> {
  const response = await fetch(`${API_BASE_URL}/api/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({...buildPlanPayload(input), llm_config: modelConfigPayload(input.llmConfig), vision_config: modelConfigPayload(input.visionConfig)})
  });
  return parseResponse(response);
}

export async function fetchJob(jobId: string): Promise<JobResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, { cache: "no-store" });
  return parseResponse(response);
}

export async function fetchJobs(): Promise<JobResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/jobs`, { cache: "no-store" });
  return parseResponse(response);
}

export async function retryGeneratedImage(input: {
  jobId: string;
  kitType: string;
}) {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${input.jobId}/retry/${input.kitType}`, {
    method: "POST",
  });
  return parseResponse<{ job_id: string; status: string; kit_type: string }>(response);
}

export async function retouchImage(input: {
  imageUrl: string;
  prompt: string;
  provider?: string;
  width?: number;
  height?: number;
}): Promise<{ url: string; provider: string; prompt: string }> {
  const response = await fetch(`${API_BASE_URL}/api/images/retouch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      image_url: input.imageUrl,
      prompt: input.prompt,
      provider: input.provider || "agnes",
      width: input.width || 1024,
      height: input.height || 1024,
    }),
  });
  return parseResponse(response);
}

export async function testLlmConnection(config: {
  apiUrl: string;
  apiKey: string;
  model: string;
}): Promise<{ success: boolean; latency_ms?: number; response?: string; error?: string }> {
  const resp = await fetch(`${API_BASE_URL}/api/test-llm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_url: config.apiUrl, api_key: config.apiKey, model: config.model }),
  });
  return parseResponse(resp);
}

export async function listModels(config: {
  apiUrl: string;
  apiKey: string;
}): Promise<{ models: string[]; error?: string }> {
  const resp = await fetch(`${API_BASE_URL}/api/list-models`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_url: config.apiUrl, api_key: config.apiKey, model: "" }),
  });
  return parseResponse(resp);
}

async function parseResponse<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(body?.detail || "请求失败");
  }
  return body as T;
}

export function buildPlanPayload(input: {
  productId?: string;
  productInfo: ProductInfo;
  platform: Platform;
  kitTypes: KitType[];
  kitSizes?: KitSizeMap;
}) {
  return {
    product_id: input.productId ?? "",
    product_name: input.productInfo.name,
    product_dimensions: input.productInfo.dimensions,
    product_price: input.productInfo.price,
    target_audience: input.productInfo.audience,
    usage_scene: input.productInfo.usageScene,
    selling_points: input.productInfo.sellingPoints,
    competitor_diff: input.productInfo.competitorDiff,
    platform: input.platform,
    kit_types: input.kitTypes,
    kit_sizes: input.kitSizes ?? {},
  };
}

export function buildGenerationPayload(input: {
  productId: string;
  platform: Platform;
  productInfo: ProductInfo;
  kitTypes: KitType[];
  kitSizes?: KitSizeMap;
  plannedPrompts?: Partial<Record<KitType, string>>;
  imageConfig?: ApiModelConfig;
  visionConfig?: ApiModelConfig;
}) {
  return {
    product_id: input.productId,
    platform: input.platform,
    product_info: {
      name: input.productInfo.name,
      category: input.productInfo.category,
      material: input.productInfo.material,
      dimensions: input.productInfo.dimensions,
      audience: input.productInfo.audience,
      usage_scene: input.productInfo.usageScene,
      selling_points: input.productInfo.sellingPoints,
      price: input.productInfo.price,
      competitor_diff: input.productInfo.competitorDiff,
      planned_prompts: input.plannedPrompts ?? {},
    },
    kit_types: input.kitTypes,
    kit_sizes: input.kitSizes ?? {},
    image_config: modelConfigPayload(input.imageConfig),
    vision_config: modelConfigPayload(input.visionConfig),
  };
}

function modelConfigPayload(config?: ApiModelConfig) {
  return config ? { apiUrl: config.apiUrl, apiKey: config.apiKey, model: config.model } : {};
}
