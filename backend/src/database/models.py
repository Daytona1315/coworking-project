import uuid
from sqlalchemy import Enum
from sqlalchemy import (
    String, Boolean, ForeignKey,
    Text, DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped, mapped_column


class Role(Enum):
    LEADER = "leader"
    MEMBER = "member"


class Base(DeclarativeBase):
    pass


# Таблица пользователей
class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String, nullable=False, default='user')
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    avatar: Mapped[str] = mapped_column(String, nullable=True, default='/path/to/default/avatar.jpg')
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


# Учётные данные пользователей
class Credential(Base):
    __tablename__ = 'credentials'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    email: Mapped[str] = mapped_column(ForeignKey("users.email"))
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    user: Mapped['User'] = relationship(back_populates='credentials')


# Таблица команд
class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    leader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    leader: Mapped["User"] = relationship("User", backref="led_teams")
    members: Mapped[list["TeamMembership"]] = relationship("TeamMembership", back_populates="team")
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="team")


# Промежуточная таблица для хранения участников команды и их ролей
class TeamMembership(Base):
    __tablename__ = "team_memberships"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    role: Mapped[Role] = mapped_column(Role, nullable=False, default=Role.MEMBER)

    user: Mapped["User"] = relationship("User", back_populates="teams")
    team: Mapped["Team"] = relationship("Team", back_populates="members")


# Таблица задач
class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Text] = mapped_column(Text, nullable=True)
    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"))
    assigned_to_all: Mapped[bool] = mapped_column(Boolean, default=True)  # Флаг для назначения всем участникам

    team: Mapped["Team"] = relationship("Team", back_populates="tasks")
    assigned_members: Mapped[list["TaskAssignment"]] = relationship("TaskAssignment", back_populates="task")
    milestones: Mapped[list["Milestone"]] = relationship("Milestone", back_populates="task")


# Таблица назначения задач отдельным пользователям
class TaskAssignment(Base):
    __tablename__ = "task_assignments"

    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)

    task: Mapped["Task"] = relationship("Task", back_populates="assigned_members")
    user: Mapped["User"] = relationship("User")


# Таблица путевых вех
class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    due_date: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    task: Mapped["Task"] = relationship("Task", back_populates="milestones")
