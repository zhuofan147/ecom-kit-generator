"use client";

import { CheckCircle2, ClipboardList, ImageIcon, Sparkles } from "lucide-react";

import { KIT_LABELS, type ProductPlan } from "@/types";

type Props = {
  plan?: ProductPlan;
  onPlanChange?: (plan: ProductPlan) => void;
  onGenerate: () => void;
  disabled?: boolean;
};

export function PlanView({ plan, onPlanChange, onGenerate, disabled }: Props) {
  if (!plan) {
    return (
      <section className="rounded border border-dashed border-line bg-white p-4 text-sm text-slate-500">
        填写商品信息后生成方案，可先查看 5 张主图的标题、画面建议和 AI prompt。
      </section>
    );
  }

  return (
    <section className="space-y-4">
      <div className="rounded border border-line bg-white p-4">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
          <Sparkles size={18} className="text-action" />
          方案规划
        </h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {plan.refined_selling_points.map((point) => (
            <span
              key={point}
              className="rounded border border-teal-100 bg-teal-50 px-2.5 py-1 text-xs font-medium text-teal-800"
            >
              {point}
            </span>
          ))}
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        {plan.image_plans.map((imagePlan, planIndex) => (
          <article key={imagePlan.index} className="rounded border border-line bg-white p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
                  <ImageIcon size={14} className="text-action" />
                  第 {imagePlan.index} 张 · {KIT_LABELS[imagePlan.kit_type] ?? imagePlan.kit_type}
                </div>
                <h3 className="mt-2 text-base font-semibold text-ink">{imagePlan.main_title}</h3>
                <p className="mt-1 text-sm text-slate-600">{imagePlan.subtitle}</p>
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-700">{imagePlan.visual_suggestion}</p>
            <details open className="mt-3 rounded border border-slate-100 bg-slate-50 p-3">
              <summary className="cursor-pointer text-xs font-semibold text-slate-600">
                查看 AI prompt
              </summary>
              <textarea
                className="mt-2 min-h-32 w-full resize-y rounded border border-line bg-white px-3 py-2 text-xs leading-5 text-slate-700 outline-none focus:border-action"
                value={imagePlan.ai_prompt}
                onChange={(event) => {
                  if (!onPlanChange) return;
                  const nextPlans = plan.image_plans.map((item, index) => index === planIndex
                    ? { ...item, ai_prompt: event.target.value }
                    : item
                  );
                  onPlanChange({ ...plan, image_plans: nextPlans });
                }}
              />
            </details>
          </article>
        ))}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <Checklist title="手机端检查" items={plan.mobile_checklist} />
        <Checklist title="转化检查" items={plan.conversion_checklist} />
      </div>

      <button
        type="button"
        disabled={disabled}
        onClick={onGenerate}
        className="inline-flex w-full items-center justify-center gap-2 rounded bg-action px-4 py-3 font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
      >
        <CheckCircle2 size={18} />
        确认方案并生成套图
      </button>
    </section>
  );
}

function Checklist({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded border border-line bg-white p-4">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-ink">
        <ClipboardList size={16} className="text-action" />
        {title}
      </h3>
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-sm leading-5 text-slate-600">
            <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-action" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
