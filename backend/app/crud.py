import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate, Submission, SubmissionCreate, SubmissionUpdate
from fastapi import HTTPException, status


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

def create_submission(db: Session, submission_data: SubmissionCreate) -> Submission:
    new_submission = Submission(**submission_data.dict())
    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)
    return new_submission


def get_submission_by_id(db: Session, submission_id: uuid.UUID) -> Submission:
    submission = db.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission with ID {submission_id} not found",
        )
    return submission


def get_submissions(db: Session, skip: int = 0, limit: int = 10) -> list[Submission]:
    statement = select(Submission).offset(skip).limit(limit)
    results = db.exec(statement).all()
    return results


def update_submission(
    db: Session, submission_id: uuid.UUID, submission_data: SubmissionUpdate
) -> Submission:
    submission = get_submission_by_id(db, submission_id)
    update_data = submission_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(submission, key, value)
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def delete_submission(db: Session, submission_id: uuid.UUID) -> None:
    submission = get_submission_by_id(db, submission_id)
    db.delete(submission)
    db.commit()