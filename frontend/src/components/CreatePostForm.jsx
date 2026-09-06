import { useState } from "react";
import client from "../api/client";

export default function CreatePostForm({ onCreated }) {
  const [content, setContent] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!content.trim()) return;
    setBusy(true);
    try {
      const { data } = await client.post("/posts", {
        content,
        image_url: imageUrl || null,
      });
      setContent("");
      setImageUrl("");
      onCreated?.(data);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card create-post" onSubmit={submit}>
      <textarea
        placeholder="Write something..."
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={3}
      />
      <input
        type="text"
        placeholder="Image URL (optional)"
        value={imageUrl}
        onChange={(e) => setImageUrl(e.target.value)}
      />
      <button type="submit" disabled={busy}>Post</button>
    </form>
  );
}
