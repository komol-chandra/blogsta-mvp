import { useEffect, useState } from "react";
import client from "../api/client";
import CreatePostForm from "../components/CreatePostForm";
import PostCard from "../components/PostCard";

export default function Timeline() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  async function loadFeed() {
    const { data } = await client.get("/feed");
    setPosts(data);
    setLoading(false);
  }

  useEffect(() => {
    loadFeed();
  }, []);

  function handleCreated(newPost) {
    setPosts((prev) => [newPost, ...prev]);
  }

  return (
    <div className="page timeline">
      <CreatePostForm onCreated={handleCreated} />
      {loading && <p className="muted">Loading feed...</p>}
      {!loading && posts.length === 0 && <p className="muted">No posts yet. Be the first!</p>}
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  );
}
