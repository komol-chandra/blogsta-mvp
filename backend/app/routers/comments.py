from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..crud import comment as comment_crud, post as post_crud
from ..deps import get_current_user

router = APIRouter(prefix="/api/v1", tags=["comments"])


@router.post("/posts/{post_id}/comments", response_model=schemas.CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(post_id: int, data: schemas.CommentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    post = post_crud.get(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return comment_crud.create(db, post_id, current_user.id, data)


@router.get("/posts/{post_id}/comments", response_model=list[schemas.CommentOut])
def list_comments(post_id: int, skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return comment_crud.list_for_post(db, post_id, skip, limit)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(comment_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    comment = comment_crud.get(db, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your comment")
    comment_crud.delete(db, comment)
