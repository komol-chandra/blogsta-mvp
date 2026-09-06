from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..crud import user as user_crud, post as post_crud
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/{username}", response_model=schemas.UserProfileOut)
def get_profile(username: str, db: Session = Depends(get_db)):
    user = user_crud.get_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    post_count, follower_count, following_count = user_crud.profile_counts(db, user.id)
    return schemas.UserProfileOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        email=user.email,
        post_count=post_count,
        follower_count=follower_count,
        following_count=following_count,
    )


@router.put("/me", response_model=schemas.UserOut)
def update_me(data: schemas.UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return user_crud.update(db, current_user, data)


@router.post("/{user_id}/follow")
def follow_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    target = user_crud.get(db, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    user_crud.follow(db, current_user.id, user_id)
    return {"status": "following"}


@router.delete("/{user_id}/follow")
def unfollow_user(user_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    user_crud.unfollow(db, current_user.id, user_id)
    return {"status": "unfollowed"}


@router.get("/{user_id}/posts", response_model=list[schemas.PostOut])
def user_posts(user_id: int, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return post_crud.by_user(db, user_id, skip, limit)
