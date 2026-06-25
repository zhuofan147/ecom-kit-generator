import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { KitTypeSelector } from "./KitTypeSelector";
import { PlatformSelector } from "./PlatformSelector";

describe("selector controls", () => {
  it("renders platform choices as radio inputs", () => {
    const markup = renderToStaticMarkup(
      <PlatformSelector value="taobao" onChange={vi.fn()} />
    );

    expect(markup).toContain('type="radio"');
    expect(markup).toContain('name="platform"');
    expect(markup).toContain("selected-card");
    expect(markup).not.toContain("bg-teal-50");
    expect(markup).not.toMatch(/<button[\s\S]*选择平台/);
  });

  it("renders kit type choices as checkbox inputs", () => {
    const markup = renderToStaticMarkup(
      <KitTypeSelector
        platform="taobao"
        value={["main_white"]}
        kitSizes={{ main_white: { w: 1080, h: 1080 } }}
        onToggle={vi.fn()}
        onSizeChange={vi.fn()}
      />
    );

    expect(markup).toContain('type="checkbox"');
    expect(markup).toContain('name="kitTypes"');
    expect(markup).toContain('name="kitSize-main_white"');
    expect(markup).toContain("1080×1080 正方形");
    expect(markup).toContain("selected-card");
    expect(markup).not.toContain("bg-teal-50");
    expect(markup).not.toMatch(/<button[\s\S]*套图类型/);
  });
});
