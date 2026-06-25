"use client";

import { Download, Type } from "lucide-react";
import { useEffect, useRef } from "react";

type ImageCanvasProps = {
  imageUrl?: string;
};

export function ImageCanvas({ imageUrl }: ImageCanvasProps) {
  const canvasElementRef = useRef<HTMLCanvasElement>(null);
  const canvasRef = useRef<any>(null);

  useEffect(() => {
    let disposed = false;

    async function setupCanvas() {
      const fabric = await import("fabric");
      if (!canvasElementRef.current || disposed) return;

      if (!canvasRef.current) {
        canvasRef.current = new fabric.Canvas(canvasElementRef.current, {
          width: 800,
          height: 800,
          backgroundColor: "#ffffff",
          preserveObjectStacking: true
        });
      }

      const canvas = canvasRef.current;
      canvas.clear();
      canvas.backgroundColor = "#ffffff";

      if (imageUrl) {
        const img = await fabric.FabricImage.fromURL(imageUrl, { crossOrigin: "anonymous" });
        const scale = Math.min(760 / (img.width || 800), 760 / (img.height || 800));
        img.scale(scale);
        img.set({
          left: (800 - (img.width || 800) * scale) / 2,
          top: (800 - (img.height || 800) * scale) / 2,
          selectable: true
        });
        canvas.add(img);
      }

      canvas.renderAll();
    }

    setupCanvas();

    return () => {
      disposed = true;
    };
  }, [imageUrl]);

  useEffect(() => {
    return () => {
      canvasRef.current?.dispose();
      canvasRef.current = null;
    };
  }, []);

  const addText = async () => {
    const fabric = await import("fabric");
    const canvas = canvasRef.current;
    if (!canvas) return;
    const text = new fabric.Textbox("新品上市", {
      left: 48,
      top: 48,
      width: 260,
      fontSize: 42,
      fontWeight: "bold",
      fill: "#b45309"
    });
    canvas.add(text);
    canvas.setActiveObject(text);
    canvas.renderAll();
  };

  const download = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement("a");
    link.download = "taobao-main-white.png";
    link.href = canvas.toDataURL({ format: "png", multiplier: 1 });
    link.click();
  };

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">文字叠加</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={addText}
            className="inline-flex items-center gap-2 rounded bg-white px-3 py-2 text-sm font-medium text-ink ring-1 ring-line hover:bg-slate-50"
          >
            <Type size={16} />
            加文字
          </button>
          <button
            type="button"
            onClick={download}
            className="inline-flex items-center gap-2 rounded bg-action px-3 py-2 text-sm font-medium text-white hover:bg-teal-800"
          >
            <Download size={16} />
            下载
          </button>
        </div>
      </div>
      <div className="w-full overflow-auto rounded border border-line bg-white p-3">
        <canvas ref={canvasElementRef} className="h-auto max-w-full" />
      </div>
    </section>
  );
}
