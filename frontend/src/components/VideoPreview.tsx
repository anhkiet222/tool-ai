import { useRef, useState } from "react";
import styles from "./VideoPreview.module.css";

interface Props {
  videoBlob: Blob;
}

export default function VideoPreview({ videoBlob }: Props) {
  const [url] = useState(() => URL.createObjectURL(videoBlob));
  const videoRef = useRef<HTMLVideoElement>(null);

  const handleDownload = () => {
    const a = document.createElement("a");
    a.href = url;
    a.download = "tiktok_review.mp4";
    a.click();
  };

  return (
    <div className={styles.wrapper}>
      <h2 className={styles.title}>🎬 Your Video is Ready!</h2>
      <div className={styles.videoContainer}>
        <video
          ref={videoRef}
          src={url}
          controls
          autoPlay
          loop
          playsInline
          className={styles.video}
        />
      </div>
      <button className={styles.downloadBtn} onClick={handleDownload}>
        ⬇ Download MP4
      </button>
    </div>
  );
}
