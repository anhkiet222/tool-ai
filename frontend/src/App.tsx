import { useEffect, useState } from "react";
import { fetchStatus, generateCaptions, generateVideo } from "./api/client";
import CaptionEditor from "./components/CaptionEditor";
import ImageUploader, { type ImageFile } from "./components/ImageUploader";
import MusicUploader from "./components/MusicUploader";
import VideoPreview from "./components/VideoPreview";
import styles from "./App.module.css";

export default function App() {
  const [aiAvailable, setAiAvailable] = useState(false);
  const [images, setImages] = useState<ImageFile[]>([]);
  const [productName, setProductName] = useState("");
  const [bullets, setBullets] = useState<string[]>(["", "", ""]);
  const [description, setDescription] = useState("");
  const [music, setMusic] = useState<File | null>(null);

  const [aiLoading, setAiLoading] = useState(false);
  const [rendering, setRendering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);

  useEffect(() => {
    fetchStatus()
      .then((s) => {
        console.log("🚀 ~ App ~ s.ai_available:", s.ai_available);
        return setAiAvailable(s.ai_available);
      })
      .catch(() => setAiAvailable(false));
  }, []);

  const handleGenerateAI = async () => {
    if (!description.trim()) return;
    setAiLoading(true);
    setError(null);
    try {
      const result = await generateCaptions(description);
      setProductName(result.product_name);
      setBullets(result.bullets);
    } catch (e) {
      setError(e instanceof Error ? e.message : "AI generation failed.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleRender = async () => {
    setError(null);
    if (images.length === 0) {
      setError("Please add at least one image.");
      return;
    }
    if (!productName.trim()) {
      setError("Please enter a product name.");
      return;
    }

    const activeBullets = bullets.filter((b) => b.trim());
    setRendering(true);
    try {
      const blob = await generateVideo({
        images: images.map((i) => i.file),
        productName: productName.trim(),
        bullets: activeBullets,
        music,
      });
      setVideoBlob(blob);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Video generation failed.");
    } finally {
      setRendering(false);
    }
  };

  const handleReset = () => {
    setVideoBlob(null);
    setImages([]);
    setProductName("");
    setBullets(["", "", ""]);
    setDescription("");
    setMusic(null);
    setError(null);
  };

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <h1>🎬 TikTok Review Maker</h1>
        <p>Turn product photos into a scroll-stopping TikTok video</p>
      </header>

      {videoBlob ? (
        <main className={styles.main}>
          <VideoPreview videoBlob={videoBlob} />
          <button className={styles.resetBtn} onClick={handleReset}>
            ← Create Another Video
          </button>
        </main>
      ) : (
        <main className={styles.main}>
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>1 · Product Images</h2>
            <ImageUploader images={images} onChange={setImages} />
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>2 · Captions</h2>
            <CaptionEditor
              productName={productName}
              bullets={bullets}
              description={description}
              aiAvailable={aiAvailable}
              loading={aiLoading}
              onProductNameChange={setProductName}
              onBulletsChange={setBullets}
              onDescriptionChange={setDescription}
              onGenerateAI={handleGenerateAI}
            />
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>3 · Music</h2>
            <MusicUploader music={music} onChange={setMusic} />
          </section>

          {error && <div className={styles.error}>⚠ {error}</div>}

          <button
            className={styles.renderBtn}
            disabled={rendering}
            onClick={handleRender}
          >
            {rendering ? (
              <span className={styles.spinner}>
                <span className={styles.dot} />
                Rendering video…
              </span>
            ) : (
              "🎬 Generate TikTok Video"
            )}
          </button>

          {rendering && (
            <p className={styles.renderHint}>
              This takes 30–90 seconds depending on image count. Please wait…
            </p>
          )}
        </main>
      )}
    </div>
  );
}
