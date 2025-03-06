from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlmodel import Session, select
import uuid
from typing import Any

from app.models import Opinion, OpinionCreate, OpinionUpdate, OpinionPublic, OpinionsPublic, Message
from app.api.deps import get_db, get_current_active_superuser

router = APIRouter(prefix="/landing", tags=["landing"])


@router.get("/", response_model=OpinionsPublic)
def read_opinions(*, session: Session = Depends(get_db), skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve opinions.
    """
    count_statement = select(func.count()).select_from(Opinion)
    count = session.exec(count_statement).one()

    statement = select(Opinion).offset(skip).limit(limit)
    opinions = session.exec(statement).all()

    return OpinionsPublic(data=opinions, count=count)


@router.post("/", response_model=OpinionPublic, dependencies=[Depends(get_current_active_superuser)])
def create_opinion(*, session: Session = Depends(get_db), opinion_in: OpinionCreate) -> Any:
    """
    Create a new opinion.
    """
    new_opinion = Opinion(**opinion_in.dict())
    session.add(new_opinion)
    session.commit()
    session.refresh(new_opinion)
    return new_opinion


@router.get("/{opinion_id}", response_model=OpinionPublic)
def read_opinion_by_id(*, session: Session = Depends(get_db), opinion_id: uuid.UUID) -> Any:
    """
    Get a specific opinion by ID.
    """
    opinion = session.get(Opinion, opinion_id)
    if not opinion:
        raise HTTPException(status_code=404, detail="The opinion with this ID does not exist.")
    return opinion


@router.patch("/{opinion_id}", response_model=OpinionPublic, dependencies=[Depends(get_current_active_superuser)])
def update_opinion(
        *, session: Session = Depends(get_db), opinion_id: uuid.UUID, opinion_in: OpinionUpdate
) -> Any:
    """
    Update a specific opinion by ID.
    """
    opinion = session.get(Opinion, opinion_id)
    if not opinion:
        raise HTTPException(status_code=404, detail="The opinion with this ID does not exist.")

    update_data = opinion_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(opinion, key, value)

    session.add(opinion)
    session.commit()
    session.refresh(opinion)
    return opinion


@router.delete("/{opinion_id}", response_model=Message, dependencies=[Depends(get_current_active_superuser)])
def delete_opinion(*, session: Session = Depends(get_db), opinion_id: uuid.UUID) -> Any:
    """
    Delete a specific opinion by ID.
    """
    opinion = session.get(Opinion, opinion_id)
    if not opinion:
        raise HTTPException(status_code=404, detail="The opinion with this ID does not exist.")

    session.delete(opinion)
    session.commit()
    return Message(message="Opinion deleted successfully")
