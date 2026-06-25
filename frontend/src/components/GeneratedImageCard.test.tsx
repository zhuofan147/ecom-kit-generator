import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import type { GeneratedImage } from "@/types";
import { GeneratedImageCard } from "./GeneratedImageCard";

const completedImage: GeneratedImage = {
  id: "image-1",
  file_name: "main-white.png",
  url: "/outputs/generated/main-white.png",
  prompt: "prompt",
  provider: "agnes",
  kit_type: "main_white",
  label: "白底主图",
  status: "completed",
};

describe("GeneratedImageCard", () => {
  it("offers regenerate for completed images", () => {
    const markup = renderToStaticMarkup(
      <GeneratedImageCard
        image={completedImage}
        busy={false}
        onPreview={vi.fn()}
        onRetry={vi.fn()}
      />
    );

    expect(markup).toContain("白底主图");
    expect(markup).toContain("重新生成");
    expect(markup).toContain("下载");
  });
});
