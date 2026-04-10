import { useCallback, useRef, useState } from "react";
import styles from "./ImageUploader.module.css";

export interface ImageFile {
  id: string;
  file: File;
  preview: string;
}

interface Props {
  images: ImageFile[];
  onChange: (images: ImageFile[]) => void;
}

export default function ImageUploader({ images, onChange }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      const toAdd: ImageFile[] = [];
      Array.from(files).forEach((file) => {
        if (!file.type.startsWith("image/")) return;
        if (images.length + toAdd.length >= 10) return;
        toAdd.push({
          id: crypto.randomUUID(),
          file,
          preview: URL.createObjectURL(file),
        });
      });
      onChange([...images, ...toAdd]);
    },
    [images, onChange],
  );

  const removeImage = (id: string) => {
    const img = images.find((i) => i.id === id);
    if (img) URL.revokeObjectURL(img.preview);
    onChange(images.filter((i) => i.id !== id));
  };

  const moveImage = (from: number, to: number) => {
    const next = [...images];
    const [item] = next.splice(from, 1);
    next.splice(to, 0, item);
    onChange(next);
  };

  return (
    <div className={styles.wrapper}>
      <div
        className={`${styles.dropzone} ${dragging ? styles.dragging : ""} ${images.length >= 10 ? styles.full : ""}`}
        onClick={() => images.length < 10 && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          addFiles(e.dataTransfer.files);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          hidden
          onChange={(e) => addFiles(e.target.files)}
        />
        {images.length === 0 ? (
          <div className={styles.placeholder}>
            <span className={styles.icon}>🖼️</span>
            <p>Drag & drop images here or click to select</p>
            <p className={styles.hint}>JPEG · PNG · WebP · Max 10 images</p>
          </div>
        ) : (
          <div className={styles.grid}>
            {images.map((img, i) => (
              <div key={img.id} className={styles.thumb}>
                <img src={img.preview} alt={`Image ${i + 1}`} />
                <span className={styles.order}>{i + 1}</span>
                <div className={styles.thumbActions}>
                  {i > 0 && (
                    <button
                      title="Move left"
                      onClick={(e) => {
                        e.stopPropagation();
                        moveImage(i, i - 1);
                      }}
                    >
                      ◀
                    </button>
                  )}
                  {i < images.length - 1 && (
                    <button
                      title="Move right"
                      onClick={(e) => {
                        e.stopPropagation();
                        moveImage(i, i + 1);
                      }}
                    >
                      ▶
                    </button>
                  )}
                  <button
                    className={styles.remove}
                    title="Remove"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeImage(img.id);
                    }}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
            {images.length < 10 && (
              <div
                className={styles.addMore}
                onClick={(e) => {
                  e.stopPropagation();
                  inputRef.current?.click();
                }}
              >
                <span>+</span>
              </div>
            )}
          </div>
        )}
      </div>
      <p className={styles.count}>{images.length} / 10 images</p>
    </div>
  );
}
