import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, delete, func, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.models import (
    Submission,
    SubmissionCreate,
    SubmissionPublic,
    SubmissionUpdate,
    SubmissionsPublic,
    Message,
)

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get(
    "/",
    response_model=SubmissionsPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def read_submissions(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve submissions.
    """
    count_statement = select(func.count()).select_from(Submission)
    count = session.exec(count_statement).one()

    statement = select(Submission).offset(skip).limit(limit)
    submissions = session.exec(statement).all()

    return SubmissionsPublic(data=submissions, count=count)


@router.post(
    "/",
    response_model=SubmissionPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def create_submission(
    *,
    session: SessionDep,
    submission_in: SubmissionCreate,
) -> Any:
    """
    Create a new submission.
    """
    new_submission = Submission(**submission_in.dict())
    session.add(new_submission)
    session.commit()
    session.refresh(new_submission)
    return new_submission


@router.get("/{submission_id}", response_model=SubmissionPublic)
def read_submission_by_id(
    submission_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get a specific submission by ID.
    """
    submission = session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=404, detail="The submission with this ID does not exist."
        )
    return submission


@router.patch("/{submission_id}", response_model=SubmissionPublic)
def update_submission(
    *,
    session: SessionDep,
    submission_id: uuid.UUID,
    submission_in: SubmissionUpdate,
    current_user: CurrentUser,
) -> Any:
    """
    Update a specific submission by ID.
    """
    submission = session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=404, detail="The submission with this ID does not exist."
        )

    # Update fields
    update_data = submission_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(submission, key, value)

    session.add(submission)
    session.commit()
    session.refresh(submission)
    return submission


@router.delete("/{submission_id}", response_model=Message)
def delete_submission(
    *,
    session: SessionDep,
    submission_id: uuid.UUID,
    current_user: CurrentUser,
) -> Any:
    """
    Delete a specific submission by ID.
    """
    submission = session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=404, detail="The submission with this ID does not exist."
        )

    session.delete(submission)
    session.commit()
    return Message(message="Submission deleted successfully")