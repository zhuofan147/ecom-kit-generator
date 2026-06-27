export const PLATFORMS = [
  "taobao", "jd", "pdd", "douyin", "xiaohongshu",
  "amazon", "shopify", "ebay", "offline_store"
] as const;

export type Platform = (typeof PLATFORMS)[number];

export const KIT_TYPES = [
  "main_white", "main_scene", "selling_point", "size_compare",
  "detail", "usage_scene", "sku_variants",
  "detail_page", "carousel", "video_cover"
] as const;

export type KitType = (typeof KIT_TYPES)[number];

export type KitSize = {
  w: number;
  h: number;
};

export type KitSizeMap = Partial<Record<KitType, KitSize>>;

export const KIT_LABELS: Record<KitType, string> = {
  main_white: "白底主图",
  main_scene: "场景主图",
  selling_point: "卖点主图",
  size_compare: "尺寸对比图",
  detail: "细节特写图",
  usage_scene: "使用场景图",
  sku_variants: "颜色/款式图",
  detail_page: "详情页长图",
  carousel: "轮播图",
  video_cover: "视频封面图",
};

export const KIT_DESCRIPTIONS: Record<KitType, string> = {
  main_white: "产品居中，纯白背景，标准电商主图",
  main_scene: "产品融入生活/办公场景",
  selling_point: "产品+核心卖点文案叠加",
  size_compare: "产品+参照物+尺寸标注",
  detail: "材质/局部放大特写",
  usage_scene: "产品+人物使用场景",
  sku_variants: "多色/多款式并列展示",
  detail_page: "多段拼接详情长图",
  carousel: "首页轮播图",
  video_cover: "视频封面图16:9",
};

export const KIT_DIMENSIONS: Record<string, Record<KitType, { w: number; h: number }>> = {
  taobao: {
    main_white: { w: 800, h: 800 },
    main_scene: { w: 800, h: 800 },
    selling_point: { w: 800, h: 800 },
    size_compare: { w: 800, h: 800 },
    detail: { w: 750, h: 1000 },
    usage_scene: { w: 800, h: 800 },
    sku_variants: { w: 800, h: 800 },
    detail_page: { w: 750, h: 2000 },
    carousel: { w: 750, h: 352 },
    video_cover: { w: 1280, h: 720 },
  },
  amazon: {
    main_white: { w: 2000, h: 2000 },
    main_scene: { w: 2000, h: 2000 },
    selling_point: { w: 2000, h: 2000 },
    size_compare: { w: 2000, h: 2000 },
    detail: { w: 1500, h: 2000 },
    usage_scene: { w: 2000, h: 2000 },
    sku_variants: { w: 2000, h: 2000 },
    detail_page: { w: 1500, h: 3000 },
    carousel: { w: 1920, h: 600 },
    video_cover: { w: 1920, h: 1080 },
  },
  offline_store: {
    main_white: { w: 1080, h: 1440 },
    main_scene: { w: 1080, h: 1440 },
    selling_point: { w: 1080, h: 1440 },
    size_compare: { w: 1080, h: 1440 },
    detail: { w: 1080, h: 1440 },
    usage_scene: { w: 1080, h: 1440 },
    sku_variants: { w: 1080, h: 1440 },
    detail_page: { w: 1080, h: 1920 },
    carousel: { w: 1920, h: 800 },
    video_cover: { w: 1280, h: 720 },
  },
};

export const KIT_SIZE_PRESETS = [
  { label: "平台默认", value: "default" },
  { label: "800×800 正方形", value: "800x800", w: 800, h: 800 },
  { label: "1000×1000 正方形", value: "1000x1000", w: 1000, h: 1000 },
  { label: "1080×1080 正方形", value: "1080x1080", w: 1080, h: 1080 },
  { label: "1080×1440 竖版海报", value: "1080x1440", w: 1080, h: 1440 },
  { label: "1080×1920 竖版长图", value: "1080x1920", w: 1080, h: 1920 },
  { label: "1200×1600 详情竖图", value: "1200x1600", w: 1200, h: 1600 },
  { label: "750×2000 淘宝详情", value: "750x2000", w: 750, h: 2000 },
  { label: "1920×800 横版轮播", value: "1920x800", w: 1920, h: 800 },
  { label: "1920×1080 视频封面", value: "1920x1080", w: 1920, h: 1080 },
] as const;

export type ProductInfo = {
  rawInfo?: string;
  name: string;
  category: string;
  material: string;
  dimensions: string;
  sellingPoints: string;
  price: string;
  audience: string;
  usageScene: string;
  competitorDiff: string;
};

export type ImagePlan = {
  index: number;
  main_title: string;
  subtitle: string;
  visual_suggestion: string;
  ai_prompt: string;
  kit_type: KitType;
};

export type ProductPlan = {
  product_info?: Partial<ProductInfo> & Record<string, unknown>;
  refined_selling_points: string[];
  image_plans: ImagePlan[];
  mobile_checklist: string[];
  conversion_checklist: string[];
};

export type UploadResponse = {
  product_id: string;
  original_url: string;
  masked_url: string;
  mask_url: string;
  reference_urls?: string[];
  multi_view_url?: string;
};

export type GeneratedImage = {
  id: string;
  file_name: string;
  url: string;
  prompt: string;
  provider: string;
  kit_type: string;
  label: string;
  status?: "completed" | "failed" | "running";
  error?: string | null;
};

export type JobStatus = "pending" | "running" | "completed" | "failed";

export type JobResponse = {
  id: string;
  product_id: string;
  platform: Platform;
  provider?: string;
  kit_types?: KitType[];
  total_images?: number;
  created_at?: string;
  updated_at?: string;
  product_info?: Partial<ProductInfo> & Record<string, unknown>;
  status: JobStatus;
  progress: number;
  message: string;
  results: GeneratedImage[];
  error?: string | null;
};

/** 默认尺寸（非 KIT_DIMENSIONS 中的平台回退到淘宝） */
export function getKitDimension(platform: Platform, kitType: KitType): { w: number; h: number } {
  const platDims = KIT_DIMENSIONS[platform];
  if (platDims?.[kitType]) return platDims[kitType];
  return KIT_DIMENSIONS.taobao[kitType] ?? { w: 800, h: 800 };
}

/** 后端 /api/providers 返回的模型信息 */
export type ProviderInfo = {
  name: string;
  label: string;
  description: string;
  available: boolean;
  is_default: boolean;
};

export type ThemeStyle = "light" | "dark" | "white";

export type ModelConfig = {
  id: string;
  name: string;
  apiUrl: string;
  apiKey: string;
  model: string;
  enabled: boolean;
  availableModels?: string[];  // 从 /v1/models 获取的模型列表
};
