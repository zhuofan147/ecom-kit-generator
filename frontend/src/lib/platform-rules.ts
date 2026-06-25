import type { Platform } from "@/types";

export type PlatformRule = {
  id: Platform;
  label: string;
  width: number;
  height: number;
  background: "white" | "scene" | "any";
  requirement: string;
};

export const platformRules: Record<Platform, PlatformRule> = {
  taobao: {
    id: "taobao",
    label: "淘宝/天猫",
    width: 800,
    height: 800,
    background: "white",
    requirement: "800x800 纯白底，商品居中，干净电商质感",
  },
  jd: {
    id: "jd",
    label: "京东",
    width: 800,
    height: 800,
    background: "white",
    requirement: "800x800 纯白底，商品占比 >80%",
  },
  pdd: {
    id: "pdd",
    label: "拼多多",
    width: 800,
    height: 800,
    background: "white",
    requirement: "800x800 白底，可带文案叠加",
  },
  douyin: {
    id: "douyin",
    label: "抖音小店",
    width: 800,
    height: 800,
    background: "white",
    requirement: "1:1 主图，强调生活方式和场景感",
  },
  xiaohongshu: {
    id: "xiaohongshu",
    label: "小红书",
    width: 1080,
    height: 1440,
    background: "scene",
    requirement: "3:4 竖版，生活美学风，文案 ≤20 字",
  },
  amazon: {
    id: "amazon",
    label: "Amazon",
    width: 2000,
    height: 2000,
    background: "white",
    requirement: "2000x2000 纯白底，商品占比 >85%",
  },
  shopify: {
    id: "shopify",
    label: "Shopify",
    width: 2048,
    height: 2048,
    background: "any",
    requirement: "2048x2048，产品突出展示",
  },
  ebay: {
    id: "ebay",
    label: "eBay",
    width: 1600,
    height: 1600,
    background: "white",
    requirement: "1600x1600，推荐白底",
  },
  offline_store: {
    id: "offline_store",
    label: "其他",
    width: 1080,
    height: 1440,
    background: "scene",
    requirement: "1080x1440 线下门店产品海报，突出产品、活动信息和到店转化",
  },
};

export const platformList = Object.values(platformRules);
