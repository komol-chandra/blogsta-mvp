# API Plan (FastAPI)

Base URL: `/api/v1`
Auth: JWT Bearer token (`Authorization: Bearer <token>`) unless marked Public.
All list endpoints support `?skip=0&limit=20` pagination.

## Auth
| Method | Path | Auth | Body / Params | Response |
|---|---|---|---|---|
| POST | /auth/register | Public | `{username, email, password, full_name?}` | `UserOut` |
| POST | /auth/login | Public | form: `username, password` (OAuth2PasswordRequestForm) | `{access_token, token_type}` |
| GET | /auth/me | Required | - | `UserOut` |

## Users
| Method | Path | Auth | Body / Params | Response |
|---|---|---|---|---|
| GET | /users/{username} | Public | - | `UserProfileOut` (incl. post/follower counts) |
| PUT | /users/me | Required | `{full_name?, bio?, avatar_url?}` | `UserOut` |
| POST | /users/{user_id}/follow | Required | - | `{status}` |
| DELETE | /users/{user_id}/follow | Required | - | `{status}` |
| GET | /users/{user_id}/followers | Public | pagination | `List[UserOut]` |
| GET | /users/{user_id}/following | Public | pagination | `List[UserOut]` |
| GET | /users/{user_id}/posts | Public | pagination | `List[PostOut]` |

## Posts / Timeline
| Method | Path | Auth | Body / Params | Response |
|---|---|---|---|---|
| POST | /posts | Required | `{content, image_url?}` | `PostOut` |
| GET | /posts/{post_id} | Public | - | `PostOut` |
| PUT | /posts/{post_id} | Required (owner) | `{content?, image_url?}` | `PostOut` |
| DELETE | /posts/{post_id} | Required (owner) | - | `204` |
| GET | /feed | Public (better with auth) | pagination | `List[PostOut]` — global reverse-chronological timeline |
| POST | /posts/{post_id}/repost | Required | `{content?}` (optional caption) | `PostOut` (new post row) |

`PostOut` shape:
```json
{
  "id": 12,
  "content": "string",
  "image_url": null,
  "created_at": "2026-09-07T10:00:00Z",
  "author": {"id": 1, "username": "komol", "avatar_url": null},
  "reaction_count": 4,
  "my_reaction": "like",
  "comment_count": 2,
  "repost_count": 1,
  "repost_of": null
}
```

## Comments
| Method | Path | Auth | Body / Params | Response |
|---|---|---|---|---|
| POST | /posts/{post_id}/comments | Required | `{content}` | `CommentOut` |
| GET | /posts/{post_id}/comments | Public | pagination | `List[CommentOut]` |
| DELETE | /comments/{comment_id} | Required (owner) | - | `204` |

## Reactions
| Method | Path | Auth | Body / Params | Response |
|---|---|---|---|---|
| POST | /posts/{post_id}/reactions | Required | `{type: "like"\|"love"\|"haha"\|"wow"\|"sad"\|"angry"}` | `ReactionOut` (creates or updates the caller's reaction) |
| DELETE | /posts/{post_id}/reactions | Required | - | `204` (removes the caller's reaction) |
| GET | /posts/{post_id}/reactions | Public | pagination | `List[ReactionOut]` |

## Error format
All errors use FastAPI's default `{"detail": "message"}` with standard HTTP status codes (400/401/403/404/409/422).

## Auth flow
1. `POST /auth/register` → creates user.
2. `POST /auth/login` → returns JWT (`sub` = user id, expiry from `ACCESS_TOKEN_EXPIRE_MINUTES`).
3. Frontend stores token (localStorage) and attaches it as `Authorization: Bearer` on every request via an axios interceptor.
