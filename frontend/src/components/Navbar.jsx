import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout } = useAuth();
  return (
    <div className="navbar">
      <Link to="/" className="brand">Blogsta</Link>
      {user && (
        <div className="nav-right">
          <Link to={`/u/${user.username}`}>{user.username}</Link>
          <button onClick={logout} className="link-btn">Logout</button>
        </div>
      )}
    </div>
  );
}
