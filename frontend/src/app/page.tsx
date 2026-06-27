"use client";

import { ClipboardCheck, History, ImageIcon, Loader2, Play, RefreshCw, Settings, Timer, Trash2, UploadCloud } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { KitTypeSelector } from "@/components/KitTypeSelector";
import { GeneratedImageCard } from "@/components/GeneratedImageCard";
import { ImagePreviewModal } from "@/components/ImagePreviewModal";
import { ModelSelector } from "@/components/ModelSelector";
import { PlanView } from "@/components/PlanView";
import { PlatformSelector } from "@/components/PlatformSelector";
import { ProductInfoForm } from "@/components/ProductInfoForm";
import { ProgressBar } from "@/components/ProgressBar";
import { SettingsPanel } from "@/components/SettingsPanel";
import { UploadZone } from "@/components/UploadZone";
import { ApiModelConfig, assetUrl, createGenerationJob, createProductPlan, fetchJob, fetchJobs, uploadProductImage } from "@/lib/api";
import { platformRules } from "@/lib/platform-rules";
import { canCreateStructuredPlan, hasCompleteModelConfig } from "@/lib/planning";
import { useAppStore, normalizeImageProvider } from "@/store";
import type { GeneratedImage, JobResponse, KitType, ModelConfig, ProductInfo, ProductPlan } from "@/types";

const PLAN_DRAFT_STORAGE_KEY = "ecom-kit-generator-plan-draft";

function readPlanDraft(): ProductPlan | undefined {
  if (typeof window === "undefined") return undefined;
  try {
    const raw = window.localStorage.getItem(PLAN_DRAFT_STORAGE_KEY);
    return raw ? JSON.parse(raw) : undefined;
  } catch {
    return undefined;
  }
}

export default function Home() {
  const {
    upload, job, productInfo, platform, kitTypes, kitSizes, providers, theme,
    llmConfigs, imageConfigs, selectedLlmConfigId, selectedImageConfigId,
    visionConfigs, selectedVisionConfigId,
    setUpload, setJob, setProductInfo, setPlatform, setKitTypes, toggleKitType, toggleProvider,
    setKitSize, setTheme, addLlmConfig, addImageConfig, addVisionConfig,
    updateLlmConfig, updateImageConfig, updateVisionConfig,
    removeLlmConfig, removeImageConfig, removeVisionConfig,
    selectLlmConfig, selectImageConfig, selectVisionConfig, hydrateFromStorage, clearDraft
  } = useAppStore();
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [planning, setPlanning] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [plan, setPlan] = useState<ProductPlan | undefined>();
  const [historyItems, setHistoryItems] = useState<JobResponse[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [previewIndex, setPreviewIndex] = useState<number>(-1);
  const [elapsedMs, setElapsedMs] = useState(0);
  const startTimeRef = useRef<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastHydratedJobRefreshRef = useRef<string | null>(null);

  const rule = platformRules[platform];
  const isGenerating = busy && !uploading;
  const canPlan = canCreateStructuredPlan(productInfo, Boolean(upload));

  useEffect(() => {
    hydrateFromStorage();
    setPlan(readPlanDraft());
  }, [hydrateFromStorage]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  // ── timer ──────────────────────────────────────────────────────
  const startTimer = useCallback(() => {
    startTimeRef.current = Date.now();
    setElapsedMs(0);
    timerRef.current = setInterval(() => {
      if (startTimeRef.current) setElapsedMs(Date.now() - startTimeRef.current);
    }, 200);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  const elapsed = useMemo(() => {
    const s = elapsedMs / 1000;
    if (s < 60) return `${s.toFixed(1)}s`;
    return `${Math.floor(s / 60)}m ${(s % 60).toFixed(1)}s`;
  }, [elapsedMs]);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const jobs = await fetchJobs();
      setHistoryItems([...jobs].sort((a, b) =>
        (b.updated_at || b.created_at || "").localeCompare(a.updated_at || a.created_at || "")
      ));
    } catch {
      // Keep the current page usable if history cannot be loaded.
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  useEffect(() => {
    if (!job?.id || jobId) return;
    if (lastHydratedJobRefreshRef.current === job.id) return;
    lastHydratedJobRefreshRef.current = job.id;
    let cancelled = false;
    void fetchJob(job.id)
      .then((nextJob) => {
        if (cancelled) return;
        setJob(nextJob);
        if (nextJob.status === "running" || nextJob.status === "pending") {
          setJobId(nextJob.id);
        }
      })
      .catch(() => {
        lastHydratedJobRefreshRef.current = null;
      });
    return () => { cancelled = true; };
  }, [job?.id, jobId, setJob]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (plan) {
      window.localStorage.setItem(PLAN_DRAFT_STORAGE_KEY, JSON.stringify(plan));
    } else {
      window.localStorage.removeItem(PLAN_DRAFT_STORAGE_KEY);
    }
  }, [plan]);

  // ── polling ────────────────────────────────────────────────────
  useEffect(() => {
    if (!jobId) return;
    if (job?.status === "completed" || job?.status === "failed") {
      stopTimer(); setBusy(false); return;
    }
    const pollTimer = window.setInterval(async () => {
      try {
        const nextJob = await fetchJob(jobId);
        setJob(nextJob);
        if (nextJob.status === "completed" || nextJob.status === "failed") {
          window.clearInterval(pollTimer); stopTimer(); setBusy(false);
          void loadHistory();
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "任务查询失败");
        setBusy(false); stopTimer(); window.clearInterval(pollTimer);
      }
    }, 900);
    return () => window.clearInterval(pollTimer);
  }, [jobId, job?.status, loadHistory, setJob, stopTimer]);

  // ── upload ─────────────────────────────────────────────────────
  const uploadFiles = async (files: File[]) => {
    setUploading(true); setError(null); setJob(undefined); setJobId(null);
    try {
      const uploaded = await uploadProductImage(files);
      setUpload(uploaded);
    } catch (err) {
      setError(err instanceof Error ? err.message : "上传失败");
    } finally { setUploading(false); }
  };

  // ── plan ───────────────────────────────────────────────────────
  const createPlan = async () => {
    if (!canPlan) {
      setError("请先填写商品信息或上传产品图");
      return;
    }
    const selectedLlm = usableModelConfig(llmConfigs, selectedLlmConfigId);
    const selectedVision = usableModelConfig(visionConfigs, selectedVisionConfigId);
    if (!hasCompleteModelConfig(selectedLlm)) {
      setError("请先在设置中配置大语言模型：商家、base_url、API Key 和模型名称都不能为空");
      return;
    }
    if (upload && !hasCompleteModelConfig(selectedVision)) {
      setError("请先在设置中配置视觉模型：商家、base_url、API Key 和模型名称都不能为空");
      return;
    }
    setPlanning(true); setError(null);
    try {
      const nextPlan = await createProductPlan({
        productId: upload?.product_id,
        productInfo,
        platform,
        kitTypes,
        kitSizes,
        llmConfig: selectedLlm ? { apiUrl: selectedLlm.apiUrl, apiKey: selectedLlm.apiKey, model: selectedLlm.model } : undefined,
        visionConfig: selectedVision ? { apiUrl: selectedVision.apiUrl, apiKey: selectedVision.apiKey, model: selectedVision.model } : undefined,
      });
      setPlan(nextPlan);
      if (nextPlan.product_info) {
        setProductInfo(productInfoFromPlan(nextPlan, productInfo));
      }
      setKitTypes(nextPlan.image_plans.map((item) => item.kit_type));
    } catch (err) {
      setError(err instanceof Error ? err.message : "方案规划失败");
    } finally {
      setPlanning(false);
    }
  };

  // ── generate ───────────────────────────────────────────────────
  const generate = async (plannedPlan?: ProductPlan) => {
    if (!upload) return;
    setBusy(true); setError(null); startTimer();
    const plannedKitTypes = plannedPlan?.image_plans.map((item) => item.kit_type) ?? kitTypes;
    const plannedPrompts = plannedPlan?.image_plans.reduce<Partial<Record<KitType, string>>>(
      (acc, item) => {
        acc[item.kit_type] = item.ai_prompt;
        return acc;
      },
      {}
    );
    const effectiveProductInfo = plannedPlan?.product_info ? productInfoFromPlan(plannedPlan, productInfo) : productInfo;
    try {
      const created = await createGenerationJob({
        productId: upload.product_id,
        platform,
        productInfo: effectiveProductInfo,
        kitTypes: plannedKitTypes,
        kitSizes,
        plannedPrompts,
        providers,
        llmConfig: (() => {
          const c = usableModelConfig(llmConfigs, selectedLlmConfigId);
          return c ? { apiUrl: c.apiUrl, apiKey: c.apiKey, model: c.model } : undefined;
        })(),
        imageConfigs: providers.map((p) => {
          const c = imageConfigs.find(c => c.enabled !== false && hasCompleteModelConfig(c) && normalizeImageProvider(c.model || c.id) === p) ??
            imageConfigs.find(c => c.enabled !== false && hasCompleteModelConfig(c) && c.id === selectedImageConfigId);
          return c ? { apiUrl: c.apiUrl, apiKey: c.apiKey, model: c.model } : undefined;
        }).filter((x): x is ApiModelConfig => Boolean(x)),
        visionConfig: (() => {
          const c = usableModelConfig(visionConfigs, selectedVisionConfigId);
          return c ? { apiUrl: c.apiUrl, apiKey: c.apiKey, model: c.model } : undefined;
        })(),
      });
      setJob({
        id: created.job_id,
        product_id: upload.product_id,
        platform,
        status: "running",
        progress: 5,
        message: "任务已创建，正在启动生成…",
        results: [],
      });
      setJobId(created.job_id);
      const firstStatus = await fetchJob(created.job_id);
      setJob(firstStatus);
      void loadHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
      setBusy(false); stopTimer();
    }
  };

  const clearCurrentDraft = () => {
    clearDraft();
    setPlan(undefined);
    setJobId(null);
    setPreviewIndex(-1);
    setError(null);
    stopTimer();
    setBusy(false);
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(PLAN_DRAFT_STORAGE_KEY);
    }
  };

  const openHistoryJob = (item: JobResponse) => {
    setJob(item);
    setJobId(item.status === "running" || item.status === "pending" ? item.id : null);
    setPlatform(item.platform);
    if (item.kit_types?.length) setKitTypes(item.kit_types);
    setProductInfo(productInfoFromJob(item, productInfo));
    setBusy(item.status === "running" || item.status === "pending");
    setError(null);
    setPreviewIndex(-1);
  };

  const retryImage = async (image: GeneratedImage) => {
    if (!upload) return;
    setBusy(true); setError(null); startTimer();
    const plannedPlan = plan;
    const plannedPrompts = plannedPlan?.image_plans?.reduce<Partial<Record<KitType, string>>>(
      (acc, item) => {
        acc[item.kit_type] = item.ai_prompt;
        return acc;
      },
      {}
    );
    const effectiveProductInfo = plannedPlan?.product_info
      ? productInfoFromPlan(plannedPlan, productInfo)
      : productInfo;
    try {
      const created = await createGenerationJob({
        productId: upload.product_id,
        platform,
        productInfo: effectiveProductInfo,
        kitTypes: [image.kit_type as KitType],
        kitSizes,
        plannedPrompts,
        providers,
        llmConfig: (() => {
          const c = usableModelConfig(llmConfigs, selectedLlmConfigId);
          return c ? { apiUrl: c.apiUrl, apiKey: c.apiKey, model: c.model } : undefined;
        })(),
        imageConfigs: providers.map((p) => {
          const c = imageConfigs.find(c => c.enabled !== false && hasCompleteModelConfig(c) && normalizeImageProvider(c.model || c.id) === p) ??
            imageConfigs.find(c => c.enabled !== false && hasCompleteModelConfig(c) && c.id === selectedImageConfigId);
          return c ? { apiUrl: c.apiUrl, apiKey: c.apiKey, model: c.model } : undefined;
        }).filter((x): x is ApiModelConfig => Boolean(x)),
        visionConfig: (() => {
          const c = usableModelConfig(visionConfigs, selectedVisionConfigId);
          return c ? { apiUrl: c.apiUrl, apiKey: c.apiKey, model: c.model } : undefined;
        })(),
      });
      setJobId(created.job_id);
      setJob({
        id: created.job_id,
        product_id: upload.product_id,
        platform,
        status: "running",
        progress: 5,
        message: `正在重新生成 ${image.label || image.kit_type}…`,
        results: [{
          id: created.job_id,
          file_name: "",
          url: "",
          prompt: "",
          provider: providers[0] || "",
          kit_type: image.kit_type,
          label: image.label,
          status: "running",
        }],
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "重新生成失败");
      setBusy(false); stopTimer();
    }
  };

  // ── render ─────────────────────────────────────────────────────
  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-6 px-5 py-6 lg:px-8">
      <header className="flex flex-col gap-3 border-b border-line pb-5 md:flex-row md:items-end md:justify-between">
        <div className="flex items-start gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal text-ink md:text-3xl">
              电商产品套图生成
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              上传产品图 → 选平台 → 勾选套图类型 → 一键批量生成
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex flex-wrap items-center gap-2 rounded border border-line bg-white px-4 py-3 text-sm text-slate-700">
            <span>平台：<strong>{rule.label}</strong></span>
            <span className="text-slate-400">·</span>
            <span>{rule.width}×{rule.height}</span>
            <span className="text-slate-400">·</span>
            <span>已选 <strong>{kitTypes.length}</strong> 类套图</span>
          </div>
          <button
            type="button"
            onClick={() => setSettingsOpen(true)}
            className="inline-flex h-11 items-center gap-2 rounded border border-line bg-white px-4 text-sm font-semibold text-ink hover:border-action"
          >
            <Settings size={17} />
            设置
          </button>
        </div>
      </header>

      <SettingsPanel
        open={settingsOpen}
        theme={theme}
        llmConfigs={llmConfigs}
        imageConfigs={imageConfigs}
        selectedLlmConfigId={selectedLlmConfigId}
        selectedImageConfigId={selectedImageConfigId}
        onClose={() => setSettingsOpen(false)}
        onThemeChange={setTheme}
        onAddLlmConfig={addLlmConfig}
        onAddImageConfig={addImageConfig}
        onUpdateLlmConfig={updateLlmConfig}
        onUpdateImageConfig={updateImageConfig}
        onSelectLlmConfig={selectLlmConfig}
        onSelectImageConfig={selectImageConfig}
        onRemoveLlmConfig={removeLlmConfig}
        onRemoveImageConfig={removeImageConfig}
        onRemoveVisionConfig={removeVisionConfig}
        visionConfigs={visionConfigs}
        selectedVisionConfigId={selectedVisionConfigId}
        onAddVisionConfig={addVisionConfig}
        onUpdateVisionConfig={updateVisionConfig}
        onSelectVisionConfig={selectVisionConfig}
      />

      {error && (
        <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[380px_minmax(0,1fr)]">
        {/* ── left panel ─────────────────────────────────────── */}
        <aside className="space-y-6 rounded border border-line bg-panel p-4">
          <div className="relative">
            <UploadZone disabled={busy || uploading} onFiles={uploadFiles} />
            {uploading && (
              <div className="mt-2 flex items-center gap-2 text-sm text-teal-700">
                <Loader2 size={14} className="animate-spin" />
                正在处理图片，生成白底多视图参考…
              </div>
            )}
          </div>

          <PlatformSelector value={platform} onChange={setPlatform} />
          <KitTypeSelector
            platform={platform}
            value={kitTypes}
            kitSizes={kitSizes}
            onToggle={toggleKitType}
            onSizeChange={setKitSize}
          />
          <ModelSelector
            selected={providers}
            onToggle={toggleProvider}
            onOpenSettings={() => setSettingsOpen(true)}
            enabledModels={imageConfigs
              .filter(c => c.enabled !== false && c.model)
              .map(c => {
                const name = normalizeImageProvider(c.model || c.id);
                return { name, label: c.name || c.model || c.id, model_id: c.model || "", endpoint: c.apiUrl || "" };
              })}
          />
          <ProductInfoForm value={productInfo} onChange={setProductInfo} />

          <section className="space-y-3 rounded border border-line bg-white p-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
                <History size={18} />
                生成记录
              </h2>
              <button
                type="button"
                onClick={loadHistory}
                className="inline-flex h-8 w-8 items-center justify-center rounded border border-line text-slate-600 hover:border-action hover:text-action"
                aria-label="刷新生成记录"
                title="刷新生成记录"
              >
                {historyLoading ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              </button>
            </div>
            <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
              {historyItems.length ? historyItems.slice(0, 12).map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => openHistoryJob(item)}
                  className="w-full rounded border border-line bg-surface px-3 py-2 text-left hover:border-action"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate text-sm font-semibold text-ink">
                      {String(item.product_info?.name || item.product_id || "未命名商品")}
                    </span>
                    <span className={`shrink-0 text-xs ${item.status === "completed" ? "text-teal-700" : item.status === "failed" ? "text-red-600" : "text-slate-600"}`}>
                      {statusLabel(item.status)}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center justify-between gap-2 text-xs text-slate-500">
                    <span>{item.provider || "unknown"} · {item.results?.filter((r) => r.status === "completed").length ?? 0}/{item.total_images || item.results?.length || 0} 张</span>
                    <span>{formatHistoryTime(item.updated_at || item.created_at)}</span>
                  </div>
                </button>
              )) : (
                <div className="rounded border border-dashed border-line bg-surface px-3 py-6 text-center text-sm text-slate-500">
                  暂无生成记录
                </div>
              )}
            </div>
          </section>

          <section className="space-y-3 rounded border border-line bg-white p-4">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">
              <ClipboardCheck size={18} />
              方案规划
            </h2>
            <button
              type="button"
              disabled={!canPlan || busy || planning || kitTypes.length === 0}
              onClick={createPlan}
              className="inline-flex w-full items-center justify-center gap-2 rounded border border-action bg-white px-4 py-2.5 font-semibold text-action transition hover:bg-teal-50 disabled:cursor-not-allowed disabled:border-slate-300 disabled:text-slate-400"
            >
              {planning ? <Loader2 size={18} className="animate-spin" /> : <ClipboardCheck size={18} />}
              {planning ? "规划中…" : "生成结构化方案"}
            </button>
          </section>

          <button
            type="button"
            disabled={!upload || busy || kitTypes.length === 0}
            onClick={() => generate()}
            className="inline-flex w-full items-center justify-center gap-2 rounded bg-action px-4 py-3 font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isGenerating ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
            {isGenerating
              ? `生成中…`
              : `生成 ${kitTypes.length} 类套图`}
          </button>
          <button
            type="button"
            disabled={busy || uploading || planning}
            onClick={clearCurrentDraft}
            className="inline-flex w-full items-center justify-center gap-2 rounded border border-line bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-red-300 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Trash2 size={16} />
            清空当前草稿
          </button>
        </aside>

        {/* ── right panel ────────────────────────────────────── */}
        <section className="space-y-6">
          {/* previews */}
          <div className="grid gap-4 md:grid-cols-3">
            <PreviewPanel title="原图预览" icon={<UploadCloud size={18} />} imageUrl={upload?.original_url} />
            <PreviewPanel title="抠图预览" icon={<ImageIcon size={18} />} imageUrl={upload?.masked_url} checkerboard />
            <PreviewPanel title="多视图参考" icon={<ImageIcon size={18} />} imageUrl={upload?.multi_view_url} />
          </div>

          <PlanView
            plan={plan}
            onPlanChange={setPlan}
            disabled={!upload || busy}
            onGenerate={() => generate(plan)}
          />

          {/* progress */}
          {job && (
            <div className="rounded border border-line bg-white p-4">
              <div className="mb-3 flex items-center justify-between text-sm text-slate-600">
                <div className="flex items-center gap-2">
                  {(job.status === "running" || job.status === "pending") && (
                    <Loader2 size={14} className="animate-spin text-action" />
                  )}
                  <span>{job.message}</span>
                </div>
                <div className="flex items-center gap-3">
                  {elapsedMs > 0 && (
                    <span className="flex items-center gap-1 text-slate-500">
                      <Timer size={14} />{elapsed}
                    </span>
                  )}
                  <span>{job.progress}%</span>
                </div>
              </div>
              <ProgressBar value={job.progress} label="" />
              {job.status === "failed" && (
                <p className="mt-3 text-sm text-red-700">{job.error || "生成失败"}</p>
              )}
              {job.status === "completed" && (
                <p className="mt-3 text-sm text-teal-700">
                  生成完成，耗时 {elapsed}，共 {job.results.length} 张套图
                </p>
              )}
            </div>
          )}

          {/* results grid */}
          {job?.results && job.results.length > 0 ? (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-ink">
                生成结果（{job.results.length} 张）
              </h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {job.results.map((img) => (
                  <GeneratedImageCard
                    key={img.id}
                    image={img}
                    busy={busy}
                    onPreview={() => {
                      const idx = job?.results?.findIndex((r) => r.id === img.id) ?? -1;
                      setPreviewIndex(idx);
                    }}
                    onRetry={() => retryImage(img)}
                  />
                ))}
              </div>
            </div>
          ) : (
            <div className="flex min-h-72 items-center justify-center rounded border border-line bg-white text-sm text-slate-500">
              {isGenerating ? (
                <span className="flex items-center gap-2">
                  <Loader2 size={18} className="animate-spin text-action" />
                  正在生成套图…
                </span>
              ) : (
                "上传产品图，选择平台和套图类型，点击生成"
              )}
            </div>
          )}
        </section>
      </div>
      <ImagePreviewModal
        open={previewIndex >= 0}
        images={(job?.results ?? []).filter((r) => r.status !== "failed" && r.status !== "running").map((r) => ({
          url: assetUrl(r.url),
          label: r.label,
          kit_type: r.kit_type,
          prompt: r.prompt,
        }))}
        currentIndex={Math.max(0, previewIndex)}
        onIndexChange={setPreviewIndex}
        onClose={() => setPreviewIndex(-1)}
      />
    </main>
  );
}

/* ── helpers ──────────────────────────────────────────────────── */

function PreviewPanel({
  title, icon, imageUrl, checkerboard
}: {
  title: string; icon: React.ReactNode; imageUrl?: string; checkerboard?: boolean;
}) {
  return (
    <section className="space-y-3">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-ink">{icon}{title}</h2>
      <div
        className={`flex aspect-square items-center justify-center rounded border border-line p-3 ${
          checkerboard
            ? "bg-[linear-gradient(45deg,#e5e7eb_25%,transparent_25%),linear-gradient(-45deg,#e5e7eb_25%,transparent_25%),linear-gradient(45deg,transparent_75%,#e5e7eb_75%),linear-gradient(-45deg,transparent_75%,#e5e7eb_75%)] bg-[length:24px_24px] bg-[position:0_0,0_12px,12px_-12px,-12px_0]"
            : "bg-white"
        }`}
      >
        {imageUrl ? (
          <img src={assetUrl(imageUrl)} alt={title} className="max-h-full max-w-full object-contain" />
        ) : (
          <span className="text-sm text-slate-500">暂无图片</span>
        )}
      </div>
    </section>
  );
}

function statusLabel(status: JobResponse["status"]) {
  if (status === "completed") return "已完成";
  if (status === "failed") return "失败";
  if (status === "running") return "生成中";
  return "等待中";
}

function formatHistoryTime(value?: string) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function productInfoFromJob(job: JobResponse, fallback: ProductInfo): ProductInfo {
  const info = job.product_info ?? {};
  return {
    ...fallback,
    rawInfo: typeof info.raw_info === "string" ? info.raw_info : typeof info.rawInfo === "string" ? info.rawInfo : fallback.rawInfo,
    name: typeof info.name === "string" ? info.name : fallback.name,
    category: typeof info.category === "string" ? info.category : fallback.category,
    material: typeof info.material === "string" ? info.material : fallback.material,
    dimensions: typeof info.dimensions === "string" ? info.dimensions : fallback.dimensions,
    sellingPoints: typeof info.selling_points === "string" ? info.selling_points : fallback.sellingPoints,
    price: typeof info.price === "string" ? info.price : fallback.price,
    audience: typeof info.audience === "string" ? info.audience : fallback.audience,
    usageScene: typeof info.usage_scene === "string" ? info.usage_scene : fallback.usageScene,
    competitorDiff: typeof info.competitor_diff === "string" ? info.competitor_diff : fallback.competitorDiff,
  };
}

function productInfoFromPlan(plan: ProductPlan, fallback: ProductInfo): ProductInfo {
  const info = plan.product_info ?? {};
  return {
    ...fallback,
    rawInfo: typeof info.raw_info === "string" ? info.raw_info : typeof info.rawInfo === "string" ? info.rawInfo : fallback.rawInfo,
    name: typeof info.name === "string" ? info.name : fallback.name,
    category: typeof info.category === "string" ? info.category : fallback.category,
    material: typeof info.material === "string" ? info.material : fallback.material,
    dimensions: typeof info.dimensions === "string" ? info.dimensions : fallback.dimensions,
    sellingPoints: typeof info.selling_points === "string" ? info.selling_points : typeof info.sellingPoints === "string" ? info.sellingPoints : fallback.sellingPoints,
    price: typeof info.price === "string" ? info.price : fallback.price,
    audience: typeof info.audience === "string" ? info.audience : fallback.audience,
    usageScene: typeof info.usage_scene === "string" ? info.usage_scene : typeof info.usageScene === "string" ? info.usageScene : fallback.usageScene,
    competitorDiff: typeof info.competitor_diff === "string" ? info.competitor_diff : typeof info.competitorDiff === "string" ? info.competitorDiff : fallback.competitorDiff,
  };
}

function usableModelConfig(configs: ModelConfig[], selectedId: string): ModelConfig | undefined {
  const selected = configs.find((config) => config.id === selectedId && config.enabled !== false && hasCompleteModelConfig(config));
  return selected ?? configs.find((config) => config.enabled !== false && hasCompleteModelConfig(config));
}
