import { useRef } from "react";
import type { UploadedImage } from "../types";
import { aspectRatioLabel } from "../utils/image";

interface Props {
  image: UploadedImage | null;
  onFile: (file: File) => void;
  disabled: boolean;
}

export default function ReferencePanel({ image, onFile, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  return (
    <section className="card reference">
      <div className="card-head">
        <h2>Reference Image</h2>
        <button className="btn ghost small" disabled={disabled} onClick={() => inputRef.current?.click()}>
          Replace
        </button>
      </div>
      {image?.dataUrl ? (
        <>
          <img src={image.dataUrl} alt="Reference" className="reference-img" />
          {image.width > 0 && (
            <div className="reference-meta">
              {image.width} × {image.height} px · {aspectRatioLabel(image.width, image.height)}
            </div>
          )}
        </>
      ) : (
        <div className="reference-empty">No image in this session.</div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = "";
        }}
      />
    </section>
  );
}
