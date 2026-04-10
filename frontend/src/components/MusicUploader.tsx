import { useRef } from "react";
import styles from "./MusicUploader.module.css";

interface Props {
  music: File | null;
  onChange: (file: File | null) => void;
}

export default function MusicUploader({ music, onChange }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className={styles.wrapper}>
      <label className={styles.label}>
        Background Music <span className={styles.optional}>(optional)</span>
      </label>
      {music ? (
        <div className={styles.selected}>
          <span className={styles.icon}>🎵</span>
          <span className={styles.name}>{music.name}</span>
          <span className={styles.size}>
            ({(music.size / 1024 / 1024).toFixed(1)} MB)
          </span>
          <button className={styles.remove} onClick={() => onChange(null)}>
            ✕ Remove
          </button>
        </div>
      ) : (
        <button
          className={styles.selectBtn}
          onClick={() => inputRef.current?.click()}
        >
          🎵 Choose MP3 / WAV
        </button>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="audio/mpeg,audio/wav,audio/mp3"
        hidden
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
    </div>
  );
}
