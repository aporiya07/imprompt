import { AppError } from "../services/errors";
import type { UploadedImage } from "../types";

export const MAX_MB = 10;

export async function loadImageFile(file: File): Promise<UploadedImage> {
  if (!/^image\/(png|jpe?g|webp)$/i.test(file.type)) {
    throw new AppError("unsupported_format", "Only PNG, JPG/JPEG and WEBP images are supported.");
  }
  if (file.size > MAX_MB * 1024 * 1024) {
    throw new AppError("image_too_large", `That image is ${(file.size / 1048576).toFixed(1)} MB; the limit is ${MAX_MB} MB.`);
  }
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(new AppError("invalid_image", "Could not read that file."));
    reader.readAsDataURL(file);
  });
  const dims = await new Promise<{ w: number; h: number }>((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve({ w: img.naturalWidth, h: img.naturalHeight });
    img.onerror = () => reject(new AppError("invalid_image", "That file doesn't look like a valid image."));
    img.src = dataUrl;
  });
  return { dataUrl, width: dims.w, height: dims.h, name: file.name, size: file.size };
}

export function aspectRatioLabel(width: number, height: number): string {
  if (!width || !height) return "";
  const common: Array<[number, number]> = [
    [1, 1], [3, 2], [2, 3], [4, 3], [3, 4], [16, 9], [9, 16], [5, 4], [4, 5], [16, 10], [10, 16], [21, 9],
  ];
  const ratio = width / height;
  for (const [w, h] of common) {
    if (Math.abs(ratio - w / h) <= 0.015) return `${w}:${h}`;
  }
  const g = gcd(width, height);
  return `${width / g}:${height / g}`;
}

function gcd(a: number, b: number): number {
  return b === 0 ? a : gcd(b, a % b);
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

export async function thumbnailOf(dataUrl: string, max = 320): Promise<string> {
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const i = new Image();
      i.onload = () => resolve(i);
      i.onerror = reject;
      i.src = dataUrl;
    });
    const scale = Math.min(1, max / Math.max(img.naturalWidth, img.naturalHeight));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
    canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
    const ctx = canvas.getContext("2d");
    if (!ctx) return "";
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.72);
  } catch {
    return "";
  }
}

/** Crop a panel thumbnail from the reference using normalized bounds (0..1). */
export async function cropPanelThumb(
  dataUrl: string,
  bounds: { x: number; y: number; w: number; h: number },
  max = 160
): Promise<string> {
  try {
    const img = await new Promise<HTMLImageElement>((resolve, reject) => {
      const i = new Image();
      i.onload = () => resolve(i);
      i.onerror = reject;
      i.src = dataUrl;
    });
    const sx = Math.max(0, Math.round(bounds.x * img.naturalWidth));
    const sy = Math.max(0, Math.round(bounds.y * img.naturalHeight));
    const sw = Math.max(1, Math.round(bounds.w * img.naturalWidth));
    const sh = Math.max(1, Math.round(bounds.h * img.naturalHeight));
    const scale = Math.min(1, max / Math.max(sw, sh));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(sw * scale));
    canvas.height = Math.max(1, Math.round(sh * scale));
    const ctx = canvas.getContext("2d");
    if (!ctx) return "";
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", 0.7);
  } catch {
    return "";
  }
}
