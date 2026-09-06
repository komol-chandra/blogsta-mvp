import { Link } from "react-router-dom";
import { useState } from "react";
import client from "../api/client";
import ReactionBar from "./ReactionBar";

function timeAgo(dateStr) {
  const seconds = Math.floor((Date.now() - new Date(dateStr)) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

export default function PostCard({ post, linkToDetail = true }) {
  const [repostCount, setRepostCount] = useState(post.repost_count);
  const [reposted, setReposted] = useState(false);

  async function doRepost() {
    await client.post(`/posts/${post.id}/repost`, { content: "" });
    setReposted(true);
    setRepostCount((c) => c + 1);
  }

  const Body = (
    <>
      {post.repost_of && (
        <div className="repost-label">🔁 reposted</div>
      )}
      <div className="post-header">
        <div className="avatar-circle">{post.author.username[0].toUpperCase()}</div>
        <div>
          <div className="username">{post.author.username}</div>
          <div className="timestamp">{timeAgo(post.created_at)} ago</div>
        </div>
      </div>
      {post.content && <p className="post-content">{post.content}</p>}
      {post.image_url && <img className="post-image" src={post.image_url} alt="" />}
      {post.repost_of && (
        <div className="embedded-post">
          <div className="username">{post.repost_of.author.username}</div>
          <p>{post.repost_of.content}</p>
        </div>
      )}
    </>
  );

  return (
    <div className="card post-card">
      {linkToDetail ? (
        <Link to={`/post/${post.id}`} className="post-link">{Body}</Link>
      ) : (
        Body
      )}
      <div className="post-actions">
        <ReactionBar post={post} />
        <Link to={`/post/${post.id}`} className="link-btn">💬 {post.comment_count}</Link>
        <button className="link-btn" onClick={doRepost} disabled={reposted}>
          🔁 {repostCount}
        </button>
      </div>
    </div>
  );
}
