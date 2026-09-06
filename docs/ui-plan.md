# UI Plan (React)

## Pages / Routes
| Route | Page | Auth? | Purpose |
|---|---|---|---|
| `/login` | Login | Public only | Email/username + password form |
| `/register` | Register | Public only | Sign-up form |
| `/` | Timeline | Protected | Reverse-chronological feed + "New post" composer at top |
| `/post/:id` | PostDetail | Protected | Full post + comment thread + comment box |
| `/u/:username` | Profile | Protected | User's bio, avatar, their posts grid/list, follow button |

## Component Tree
```
App
 ├─ AuthProvider (context: user, token, login(), logout())
 ├─ Navbar (logo, search stub, "+ New Post", avatar/profile link, logout)
 ├─ ProtectedRoute (redirects to /login if no token)
 └─ Routes
     ├─ Login
     ├─ Register
     ├─ Timeline
     │   ├─ CreatePostForm
     │   └─ PostCard (repeated)
     │       ├─ ReactionBar (like button + count, opens reaction picker)
     │       ├─ RepostButton
     │       └─ "View comments" link → /post/:id
     ├─ PostDetail
     │   ├─ PostCard (the post itself)
     │   ├─ CommentList
     │   │   └─ CommentItem (repeated)
     │   └─ CommentForm
     └─ Profile
         ├─ ProfileHeader (avatar, bio, follow/unfollow button, counts)
         └─ PostCard (repeated, user's own posts)
```

## Key Screens (wireframe description)

### Timeline (`/`)
```
┌─────────────────────────────────────────┐
│ Navbar: Blogsta   [+ New Post]  [avatar] │
├─────────────────────────────────────────┤
│ [ Write something... ]  [Post]           │  <- CreatePostForm (collapsed textarea)
├─────────────────────────────────────────┤
│ (avatar) username · 2h ago               │
│ Post content text...                     │
│ [image if any]                           │
│ ❤ 12   💬 3   🔁 1                        │  <- ReactionBar / comment count / repost
│ [Like] [Comment] [Repost]                │
├─────────────────────────────────────────┤
│ ... more PostCards, infinite scroll ...  │
└─────────────────────────────────────────┘
```
Reposts render like a normal PostCard with a small "🔁 username reposted" label above the embedded original post preview.

### PostDetail (`/post/:id`)
Same PostCard at top (larger), then a comment list below with a sticky comment input at the bottom.

### Profile (`/u/:username`)
Header band (avatar, name, bio, `Follow`/`Following` button, post/follower/following counts), then that user's posts in a single column feed below.

## State Management
- `AuthContext`: holds `user`, `token`; persists token to `localStorage`; exposes `login()`, `register()`, `logout()`.
- Data fetching: local component state + `useEffect` fetch on mount (kept simple for MVP — no react-query dependency needed, though it's a natural upgrade).
- `api/client.js`: single axios instance with a request interceptor that attaches the bearer token, and a response interceptor that redirects to `/login` on 401.

## Visual style
Minimal Instagram-like card feed: white cards on light-gray background, rounded corners, circular avatars, a red/pink accent for the like icon. Single-column, mobile-first max-width ~600px centered.
