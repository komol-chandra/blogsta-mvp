import { useState } from "react";
import client from "../api/client";

export default function ReactionBar({ post }) {
  const [myReaction, setMyReaction] = useState(post.my_reaction);
  const [count, setCount] = useState(post.reaction_count);

  async function toggleLike() {
    if (myReaction) {
      await client.delete(`/posts/${post.id}/reactions`);
      setMyReaction(null);
      setCount((c) => c - 1);
    } else {
      await client.post(`/posts/${post.id}/reactions`, { type: "like" });
      setMyReaction("like");
      setCount((c) => c + 1);
    }
  }

  return (
    <button className={`reaction-btn ${myReaction ? "active" : ""}`} onClick={toggleLike}>
      {myReaction ? "❤️" : "🤍"} {count}
    </button>
  );
}
