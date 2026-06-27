"use client";

import type { ProductInfo } from "@/types";

type ProductInfoFormProps = {
  value: ProductInfo;
  onChange: (value: ProductInfo) => void;
};

export function ProductInfoForm({ value, onChange }: ProductInfoFormProps) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ink">商品信息</h2>
        <p className="mt-1 text-sm text-slate-600">
          整体填写商品资料，点击生成结构化方案后 AI 会识别名称、价格、卖点和使用场景。
        </p>
      </div>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">整体填写</span>
        <textarea
          className="mt-1 min-h-44 w-full resize-y rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.rawInfo ?? ""}
          onChange={(event) => onChange({ ...value, rawInfo: event.target.value })}
          placeholder={"例如：Insta360 X5 运动全景相机，售价2999元。主打8K全景、防抖、防水、夜景增强，适合户外、旅行、骑行、vlog。"}
        />
      </label>
    </section>
  );
}
