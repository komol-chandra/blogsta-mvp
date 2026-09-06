export default function CommentList({ comments }) {
  if (!comments.length) return <p className="muted">No comments yet.</p>;
  return (
    <div className="comment-list">
      {comments.map((c) => (
        <div key={c.id} className="comment-item">
          <div className="avatar-circle small">{c.author.username[0].toUpperCase()}</div>
          <div>
            <span className="username">{c.author.username}</span>{" "}
            <span>{c.content}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
