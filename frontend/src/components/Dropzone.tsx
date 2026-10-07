import { useRef, useState } from "react";
import type { UploadedImage } from "../types";
import { aspectRatioLabel, formatBytes } from "../utils/image";

interface Props {
  image: UploadedImage | null;
  onFile: (file: File) => void;
  onFetchUrl: (url: string) => void;
  disabled: boolean;
  fetchingUrl: boolean;
}

export default function Dropzone({ image, onFile, onFetchUrl, disabled, fetchingUrl }: Props) {
  const [drag, setDrag] = useState(false);
  const [mode, setMode] = useState<"upload" | "url">("upload");
  const [url, setUrl] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const hasImage = image !== null && image.dataUrl !== "";

  if (hasImage) {
    return (
      <div className="dropzone filled">
        <div className="preview-row">
          <img src={image!.dataUrl} alt="Reference preview" className="preview-thumb" />
          <div className="preview-meta">
            <div className="preview-name" title={image!.name}>
              {image!.name}
            </div>
            <div className="preview-dims">
              {image!.width} × {image!.height} px · {aspectRatioLabel(image!.width, image!.height)} ·{" "}
              {formatBytes(image!.size)}
            </div>
          </div>
        </div>
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
        <button className="btn ghost small" disabled={disabled} onClick={() => inputRef.current?.click()}>
          Replace image
        </button>
      </div>
    );
  }

  function submitUrl() {
    const trimmed = url.trim();
    if (!trimmed || fetchingUrl) return;
    onFetchUrl(trimmed);
  }

  return (
    <div className="dropzone-wrap">
      <div className="dz-tabs" role="tablist">
        <button
          className={`dz-tab${mode === "upload" ? " active" : ""}`}
          onClick={() => setMode("upload")}
          role="tab"
          aria-selected={mode === "upload"}
        >
          Upload
        </button>
        <button
          className={`dz-tab${mode === "url" ? " active" : ""}`}
          onClick={() => setMode("url")}
          role="tab"
          aria-selected={mode === "url"}
        >
          Image URL
        </button>
      </div>

      {mode === "upload" ? (
        <div
          className={`dropzone${drag ? " drag" : ""}${disabled ? " disabled" : ""}`}
          onClick={() => !disabled && inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            if (!disabled) setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            if (!disabled) {
              const f = e.dataTransfer.files?.[0];
              if (f) onFile(f);
            }
          }}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if ((e.key === "Enter" || e.key === " ") && !disabled) inputRef.current?.click();
          }}
        >
          <div className="dz-icon">🖼️</div>
          <div className="dz-title">Drop image here</div>
          <div className="dz-sub">or click to upload · PNG, JPG, WEBP · up to 10 MB</div>
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
        </div>
      ) : (
        <div className="dropzone url-mode">
          <div className="dz-title">Paste an image URL</div>
          <div className="dz-sub">Any public image link — we fetch and validate it server-side</div>
          <div className="dz-url-row">
            <input
              type="url"
              placeholder="https://…"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") submitUrl();
              }}
              disabled={disabled || fetchingUrl}
            />
            <button className="btn primary" disabled={disabled || fetchingUrl || !url.trim()} onClick={submitUrl}>
              {fetchingUrl ? "Fetching…" : "Use Image"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
