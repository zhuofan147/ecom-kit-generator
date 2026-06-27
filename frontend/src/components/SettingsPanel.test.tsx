import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { nextListModelsResult, nextModelFieldPatch, SettingsPanel } from "./SettingsPanel";

const modelConfigs = [
  {
    id: "llm-default",
    name: "",
    apiUrl: "",
    apiKey: "",
    model: "",
    enabled: true,
  },
];

describe("SettingsPanel", () => {
  it("clears fetched models when editable model credentials change", () => {
    expect(nextModelFieldPatch("apiKey", "")).toEqual({
      apiKey: "",
      availableModels: undefined,
      enabled: false,
    });
  });

  it("clears stale list-model errors when models are fetched successfully", () => {
    expect(
      nextListModelsResult("vision", { models: ["Qwen/Qwen3-VL-32B-Instruct"] })
    ).toBeNull();
  });

  it("renders theme options and separate model configuration sections", () => {
    const markup = renderToStaticMarkup(
      <SettingsPanel
        open
        theme="dark"
        llmConfigs={modelConfigs}
        imageConfigs={modelConfigs}
        visionConfigs={modelConfigs}
        selectedLlmConfigId="llm-default"
        selectedImageConfigId="llm-default"
        selectedVisionConfigId="llm-default"
        onClose={vi.fn()}
        onThemeChange={vi.fn()}
        onAddLlmConfig={vi.fn()}
        onAddImageConfig={vi.fn()}
        onUpdateLlmConfig={vi.fn()}
        onUpdateImageConfig={vi.fn()}
        onRemoveLlmConfig={vi.fn()}
        onRemoveImageConfig={vi.fn()}
        onRemoveVisionConfig={vi.fn()}
        onSelectLlmConfig={vi.fn()}
        onSelectImageConfig={vi.fn()}
        onSelectVisionConfig={vi.fn()}
        onAddVisionConfig={vi.fn()}
        onUpdateVisionConfig={vi.fn()}
      />
    );

    expect(markup).toContain("页面风格");
    expect(markup).toContain("明亮");
    expect(markup).toContain("暗黑");
    expect(markup).toContain("纯白");
    expect(markup).toContain("大语言模型配置");
    expect(markup).toContain("生图模型配置");
    expect(markup).toContain("商家");
    expect(markup).toContain("base_url");
    expect(markup).toContain('name="theme"');
    expect((markup.match(/模型预设/g) ?? []).length).toBe(3);
    expect(markup).not.toContain("默认大模型");
    expect(markup).not.toContain("当前选择");
    expect(markup).toContain("未配置");
    expect(markup).not.toContain("已启用");
    expect((markup.match(/测试连通/g) ?? []).length).toBe(2);
    expect((markup.match(/获取模型/g) ?? []).length).toBe(3);
    expect(markup).toContain(">生图模型</span>");
    expect(markup).toContain("Agnes AI (免费)");
    expect(markup).toContain("火山方舟 Seedream 5.0");
  });

  it("does not show stale fetched model counts when API Key is empty", () => {
    const markup = renderToStaticMarkup(
      <SettingsPanel
        open
        theme="dark"
        llmConfigs={modelConfigs}
        imageConfigs={[{ ...modelConfigs[0], availableModels: ["agnes-image-2.1-flash", "doubao-seedream-5-0"] }]}
        selectedLlmConfigId="llm-default"
        selectedImageConfigId="llm-default"
        onClose={vi.fn()}
        onThemeChange={vi.fn()}
        onAddLlmConfig={vi.fn()}
        onAddImageConfig={vi.fn()}
        onUpdateLlmConfig={vi.fn()}
        onUpdateImageConfig={vi.fn()}
        onRemoveLlmConfig={vi.fn()}
        onRemoveImageConfig={vi.fn()}
        onRemoveVisionConfig={vi.fn()}
        onSelectLlmConfig={vi.fn()}
        onSelectImageConfig={vi.fn()}
        onSelectVisionConfig={vi.fn()}
      />
    );

    expect(markup).not.toContain("获取模型 (2)");
    expect(markup).not.toContain("agnes-image-2.1-flash");
  });

  it("shows enabled only for complete enabled configs", () => {
    const markup = renderToStaticMarkup(
      <SettingsPanel
        open
        theme="dark"
        llmConfigs={[{
          ...modelConfigs[0],
          apiUrl: "https://api.example.com/v1",
          apiKey: "sk-test",
          model: "gpt-4.1",
          enabled: true,
        }]}
        imageConfigs={[]}
        selectedLlmConfigId="llm-default"
        selectedImageConfigId=""
        onClose={vi.fn()}
        onThemeChange={vi.fn()}
        onAddLlmConfig={vi.fn()}
        onAddImageConfig={vi.fn()}
        onUpdateLlmConfig={vi.fn()}
        onUpdateImageConfig={vi.fn()}
        onRemoveLlmConfig={vi.fn()}
        onRemoveImageConfig={vi.fn()}
        onRemoveVisionConfig={vi.fn()}
        onSelectLlmConfig={vi.fn()}
        onSelectImageConfig={vi.fn()}
        onSelectVisionConfig={vi.fn()}
      />
    );

    expect(markup).toContain("已启用");
    expect(markup).toContain("停用");
  });

  it("renders nothing while closed", () => {
    const markup = renderToStaticMarkup(
      <SettingsPanel
        open={false}
        theme="dark"
        llmConfigs={modelConfigs}
        imageConfigs={modelConfigs}
        selectedLlmConfigId="llm-default"
        selectedImageConfigId="llm-default"
        onClose={vi.fn()}
        onThemeChange={vi.fn()}
        onAddLlmConfig={vi.fn()}
        onAddImageConfig={vi.fn()}
        onUpdateLlmConfig={vi.fn()}
        onUpdateImageConfig={vi.fn()}
        onRemoveLlmConfig={vi.fn()}
        onRemoveImageConfig={vi.fn()}
        onRemoveVisionConfig={vi.fn()}
        onSelectLlmConfig={vi.fn()}
        onSelectImageConfig={vi.fn()}
        onSelectVisionConfig={vi.fn()}
      />
    );

    expect(markup).toBe("");
  });
});
