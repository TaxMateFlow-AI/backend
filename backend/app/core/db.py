from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, Submission

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    submission_count = session.exec(select(Submission)).count()
    if submission_count == 0:
        submission_1 = Submission(
            date="2025-02-20T00:00:00",
            time="13:45",
            document="Document_1.pdf",
            status="Completed",
            owner="User_1",
            size="2.5MB",
            type="PDF",
            priority="High",
        )
        submission_2 = Submission(
            date="2025-02-19T00:00:00",
            time="09:30",
            document="Document_2.docx",
            status="Pending",
            owner="User_2",
            size="1.2MB",
            type="DOCX",
            priority="Medium",
        )
        session.add_all([submission_1, submission_2])
        session.commit()