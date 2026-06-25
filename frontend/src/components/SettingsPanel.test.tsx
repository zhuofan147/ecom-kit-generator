import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { SettingsPanel } from "./SettingsPanel";

const modelConfigs = [
  {
    id: "llm-default",
    name: "默认大模型",
    apiUrl: "https://api.example.com/v1",
    apiKey: "",
    model: "gpt-4.1",
    enabled: true,
  },
];

describe("SettingsPanel", () => {
  it("renders theme options and separate model configuration sections", () => {
    const markup = renderToStaticMarkup(
      <SettingsPanel
        open
        theme="green"
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
        onSelectLlmConfig={vi.fn()}
        onSelectImageConfig={vi.fn()}
      />
    );

    expect(markup).toContain("页面风格");
    expect(markup).toContain("黑色");
    expect(markup).toContain("蓝色");
    expect(markup).toContain("绿色");
    expect(markup).toContain("白色");
    expect(markup).toContain("大语言模型配置");
    expect(markup).toContain("生图模型配置");
    expect(markup).toContain('name="theme"');
  });

  it("renders nothing while closed", () => {
    const markup = renderToStaticMarkup(
      <SettingsPanel
        open={false}
        theme="green"
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
        onSelectLlmConfig={vi.fn()}
        onSelectImageConfig={vi.fn()}
      />
    );

    expect(markup).toBe("");
  });
});
