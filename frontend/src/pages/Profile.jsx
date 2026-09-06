import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client";
import PostCard from "../components/PostCard";
import { useAuth } from "../context/AuthContext";

export default function Profile() {
  const { username } = useParams();
  const { user: me } = useAuth();
  const [profile, setProfile] = useState(null);
  const [posts, setPosts] = useState([]);

  async function load() {
    const { data } = await client.get(`/users/${username}`);
    setProfile(data);
    const postsRes = await client.get(`/users/${data.id}/posts`);
    setPosts(postsRes.data);
  }

  useEffect(() => {
    load();
  }, [username]);

  async function toggleFollow() {
    if (profile.is_following) {
      await client.delete(`/users/${profile.id}/follow`);
    } else {
      await client.post(`/users/${profile.id}/follow`);
    }
    load();
  }

  if (!profile) return <p className="muted">Loading...</p>;
  const isMe = me?.username === profile.username;

  return (
    <div className="page profile">
      <div className="card profile-header">
        <div className="avatar-circle large">{profile.username[0].toUpperCase()}</div>
        <div>
          <h2>{profile.full_name || profile.username}</h2>
          <p className="muted">@{profile.username}</p>
          {profile.bio && <p>{profile.bio}</p>}
          <div className="profile-stats">
            <span><b>{profile.post_count}</b> posts</span>
            <span><b>{profile.follower_count}</b> followers</span>
            <span><b>{profile.following_count}</b> following</span>
          </div>
          {!isMe && (
            <button onClick={toggleFollow}>
              {profile.is_following ? "Following" : "Follow"}
            </button>
          )}
        </div>
      </div>
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  );
}
