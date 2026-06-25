import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { ImagePreviewModal } from "./ImagePreviewModal";

describe("ImagePreviewModal", () => {
  it("renders enlarged image with download and close actions", () => {
    const markup = renderToStaticMarkup(
      <ImagePreviewModal
        open
        images={[
          { url: "http://localhost:8000/outputs/generated/demo.png", label: "白底主图" },
          { url: "http://localhost:8000/outputs/generated/scene.png", label: "场景图" },
        ]}
        currentIndex={0}
        onIndexChange={vi.fn()}
        onClose={vi.fn()}
      />
    );

    expect(markup).toContain("白底主图");
    expect(markup).toContain("demo.png");
    expect(markup).toContain("download");
    expect(markup).toContain('aria-label="关闭预览"');
    // navigation arrows
    expect(markup).toContain('aria-label="上一张"');
    expect(markup).toContain('aria-label="下一张"');
    // thumbnail strip
    expect(markup).toContain("1 / 2");
  });
});
