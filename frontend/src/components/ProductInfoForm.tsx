"use client";

import type { ProductInfo } from "@/types";

type ProductInfoFormProps = {
  value: ProductInfo;
  onChange: (value: ProductInfo) => void;
};

export function ProductInfoForm({ value, onChange }: ProductInfoFormProps) {
  const update = (key: keyof ProductInfo, fieldValue: string) => {
    onChange({ ...value, [key]: fieldValue });
  };

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-ink">商品信息</h2>
        <p className="mt-1 text-sm text-slate-600">选填，用于拼接 Phase 1 提示词。</p>
      </div>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">产品名称</span>
        <input
          className="mt-1 w-full rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.name}
          onChange={(event) => update("name", event.target.value)}
          placeholder="例如：无线蓝牙耳机"
        />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">价格</span>
        <input
          className="mt-1 w-full rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.price}
          onChange={(event) => update("price", event.target.value)}
          placeholder="例如：199"
        />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">类目</span>
        <input
          className="mt-1 w-full rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.category}
          onChange={(event) => update("category", event.target.value)}
          placeholder="例如：3C / 美妆 / 家居"
        />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">目标人群</span>
        <input
          className="mt-1 w-full rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.audience}
          onChange={(event) => update("audience", event.target.value)}
          placeholder="例如：通勤上班族"
        />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">使用场景</span>
        <input
          className="mt-1 w-full rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.usageScene}
          onChange={(event) => update("usageScene", event.target.value)}
          placeholder="例如：地铁通勤 / 办公会议"
        />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">材质/颜色</span>
        <input
          className="mt-1 w-full rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.material}
          onChange={(event) => update("material", event.target.value)}
          placeholder="例如：哑光黑色塑料"
        />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">尺寸/规格</span>
        <input
          className="mt-1 w-full rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.dimensions}
          onChange={(event) => update("dimensions", event.target.value)}
          placeholder="例如：124 x 46 x 38mm，重量 200g"
        />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">核心卖点</span>
        <textarea
          className="mt-1 min-h-24 w-full resize-y rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.sellingPoints}
          onChange={(event) => update("sellingPoints", event.target.value)}
          placeholder={"每行一个卖点\n例如：长续航\n低延迟"}
        />
      </label>
      <label className="block">
        <span className="text-sm font-medium text-slate-700">竞品差异</span>
        <textarea
          className="mt-1 min-h-20 w-full resize-y rounded border border-line bg-white px-3 py-2 outline-none focus:border-action"
          value={value.competitorDiff}
          onChange={(event) => update("competitorDiff", event.target.value)}
          placeholder="例如：同价位续航更久，佩戴更轻"
        />
      </label>
    </section>
  );
}
