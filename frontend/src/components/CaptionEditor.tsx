import styles from "./CaptionEditor.module.css";

interface Props {
  productName: string;
  bullets: string[];
  description: string;
  aiAvailable: boolean;
  loading: boolean;
  onProductNameChange: (v: string) => void;
  onBulletsChange: (v: string[]) => void;
  onDescriptionChange: (v: string) => void;
  onGenerateAI: () => void;
}

const MAX_BULLETS = 5;

export default function CaptionEditor({
  productName,
  bullets,
  description,
  aiAvailable,
  loading,
  onProductNameChange,
  onBulletsChange,
  onDescriptionChange,
  onGenerateAI,
}: Props) {
  const updateBullet = (index: number, value: string) => {
    const next = [...bullets];
    next[index] = value;
    onBulletsChange(next);
  };

  const addBullet = () => {
    if (bullets.length < MAX_BULLETS) onBulletsChange([...bullets, ""]);
  };

  const removeBullet = (index: number) => {
    onBulletsChange(bullets.filter((_, i) => i !== index));
  };

  return (
    <div className={styles.wrapper}>
      {/* Product name */}
      <div className={styles.field}>
        <label htmlFor="product-name">Product Name</label>
        <input
          id="product-name"
          type="text"
          value={productName}
          maxLength={60}
          placeholder="e.g. Smart Air Fryer Pro"
          onChange={(e) => onProductNameChange(e.target.value)}
        />
      </div>

      {/* Feature bullets */}
      <div className={styles.field}>
        <label>
          Feature Bullets{" "}
          <span className={styles.hint}>
            ({bullets.length}/{MAX_BULLETS})
          </span>
        </label>
        <div className={styles.bullets}>
          {bullets.map((b, i) => (
            <div key={i} className={styles.bulletRow}>
              <span className={styles.bulletIndex}>{i + 1}</span>
              <input
                type="text"
                value={b}
                maxLength={60}
                placeholder={`Feature ${i + 1}`}
                onChange={(e) => updateBullet(i, e.target.value)}
              />
              <button
                className={styles.removeBullet}
                title="Remove"
                onClick={() => removeBullet(i)}
              >
                ✕
              </button>
            </div>
          ))}
          {bullets.length < MAX_BULLETS && (
            <button className={styles.addBullet} onClick={addBullet}>
              + Add feature
            </button>
          )}
        </div>
      </div>

      {/* AI description section */}
      <div className={styles.aiSection}>
        <label htmlFor="description">
          Product Description
          {!aiAvailable && (
            <span className={styles.hint}>
              {" "}
              (add GEMINI_API_KEY to enable AI)
            </span>
          )}
        </label>
        <textarea
          id="description"
          value={description}
          rows={4}
          maxLength={800}
          placeholder="Describe the product — what it does, who it's for, why it stands out..."
          onChange={(e) => onDescriptionChange(e.target.value)}
        />
        <div className={styles.aiRow}>
          <span className={styles.charCount}>{description.length}/800</span>
          <button
            className={styles.aiButton}
            disabled={!aiAvailable || loading || !description.trim()}
            onClick={onGenerateAI}
            title={
              !aiAvailable
                ? "GEMINI_API_KEY not configured"
                : "Auto-fill name & bullets with AI"
            }
          >
            {loading ? "Generating…" : "✨ Generate with AI"}
          </button>
        </div>
      </div>
    </div>
  );
}
