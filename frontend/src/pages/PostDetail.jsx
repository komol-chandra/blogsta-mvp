import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client";
import PostCard from "../components/PostCard";
import CommentList from "../components/CommentList";

export default function PostDetail() {
  const { id } = useParams();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState("");

  async function load() {
    const [postRes, commentsRes] = await Promise.all([
      client.get(`/posts/${id}`),
      client.get(`/posts/${id}/comments`),
    ]);
    setPost(postRes.data);
    setComments(commentsRes.data);
  }

  useEffect(() => {
    load();
  }, [id]);

  async function submitComment(e) {
    e.preventDefault();
    if (!newComment.trim()) return;
    const { data } = await client.post(`/posts/${id}/comments`, { content: newComment });
    setComments((prev) => [...prev, data]);
    setNewComment("");
  }

  if (!post) return <p className="muted">Loading...</p>;

  return (
    <div className="page post-detail">
      <PostCard post={post} linkToDetail={false} />
      <div className="card">
        <h4>Comments</h4>
        <CommentList comments={comments} />
        <form onSubmit={submitComment} className="comment-form">
          <input
            placeholder="Write a comment..."
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
          />
          <button type="submit">Send</button>
        </form>
      </div>
    </div>
  );
}
