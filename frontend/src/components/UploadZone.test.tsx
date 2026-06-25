import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

import { UploadZone } from "./UploadZone";

describe("UploadZone", () => {
  it("does not nest the file input inside the clickable button surface", () => {
    const markup = renderToStaticMarkup(<UploadZone onFiles={vi.fn()} />);

    expect(markup).not.toMatch(/<button[\s\S]*<input/);
  });
});
