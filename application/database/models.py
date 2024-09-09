from sqlalchemy import BigInteger, ForeignKey, Date, Text, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import DateTime

from config import SQLALCHEMY_URL

engine = create_async_engine(SQLALCHEMY_URL, echo=True)

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Teacher(Base):
    __tablename__: str = 'teachers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    last_name: Mapped[str] = mapped_column()
    specialisation: Mapped[str] = mapped_column()
    password_teacher: Mapped[str] = mapped_column()

    students = relationship(argument='Student', secondary='student_teacher', back_populates='teachers',
                            cascade="all, delete")
    homeworks = relationship(argument='Homework', back_populates='teacher', cascade="all, delete-orphan")


class Student(Base):
    __tablename__: str = 'students'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    date_of_registration = mapped_column(DateTime)
    name: Mapped[str | None] = mapped_column()
    last_name: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    specialisation_student: Mapped[str | None] = mapped_column()
    point: Mapped[int | None] = mapped_column()

    homeworks = relationship(argument='Homework', back_populates='student', cascade="all, delete-orphan")
    points_history = relationship(argument='PointsHistory', back_populates='student', cascade="all, delete-orphan")
    teachers = relationship(argument='Teacher', secondary='student_teacher', back_populates='students',
                            cascade="all, delete")
    daily_check_ins = relationship(argument='DailyCheckIn', back_populates='student', cascade="all, delete-orphan")
    daily_check_ins_vocal = relationship(argument='DailyCheckInVocal', back_populates='student',
                                         cascade="all, delete-orphan")
    tasks1 = relationship(argument='Task1', back_populates='student', cascade="all, delete-orphan")
    tasks2 = relationship(argument='Task2', back_populates='student', cascade="all, delete-orphan")
    tasks3 = relationship(argument='Task3', back_populates='student', cascade="all, delete-orphan")
    tasks4 = relationship(argument='Task4', back_populates='student', cascade="all, delete-orphan")
    tasks5 = relationship(argument='Task5', back_populates='student', cascade="all, delete-orphan")
    tasks6 = relationship(argument='Task6', back_populates='student', cascade="all, delete-orphan")
    tasks7 = relationship(argument='Task7', back_populates='student', cascade="all, delete-orphan")


class StudentGift(Base):
    __tablename__ = 'student_gifts'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_name: Mapped[str | None] = mapped_column()
    student_last_name: Mapped[str | None] = mapped_column()
    student_phone: Mapped[str | None] = mapped_column()
    gift_name: Mapped[str | None] = mapped_column()
    date_received = mapped_column(DateTime)
    is_approved = mapped_column(Boolean)


class TgIdPhone(Base):
    __tablename__ = 'tg_id_phone'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    phone: Mapped[str | None] = mapped_column()


class StudentTeacher(Base):
    __tablename__ = 'student_teacher'
    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'))
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey('teachers.id'))


class Homework(Base):
    __tablename__: str = 'homeworks'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'))
    teacher_id: Mapped[int] = mapped_column(ForeignKey('teachers.id'))
    file_hash: Mapped[str | None] = mapped_column()
    file_type: Mapped[str | None] = mapped_column()
    submission_time = mapped_column(DateTime)
    feedback_sent: Mapped[int] = mapped_column(default=0)
    is_checked = mapped_column(Boolean, default=False)

    student = relationship(argument='Student', back_populates='homeworks')
    teacher = relationship(argument='Teacher', back_populates='homeworks')


class PointsHistory(Base):
    __tablename__: str = 'points_history'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'))
    points_added: Mapped[int | None] = mapped_column()
    date_added = mapped_column(DateTime)

    student = relationship(argument='Student', back_populates='points_history')


class Administrator(Base):
    __tablename__: str = 'administrators'

    id: Mapped[int] = mapped_column(primary_key=True)
    administrator_tg_id = mapped_column(BigInteger)


class Password(Base):
    __tablename__: str = 'passwords'

    id: Mapped[int] = mapped_column(primary_key=True)
    password_newsletter: Mapped[str | None] = mapped_column()


class MonetizationSystem(Base):
    __tablename__: str = 'monetization_systems'

    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str | None] = mapped_column()
    number_of_points: Mapped[int | None] = mapped_column()


class MonetizationSystemPoints(Base):
    __tablename__: str = 'monetization_systems_points'

    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str | None] = mapped_column()
    number_of_points: Mapped[int | None] = mapped_column()


class PointsExchange(Base):
    __tablename__: str = 'points_exchanges'

    id: Mapped[int] = mapped_column(primary_key=True)
    present: Mapped[str | None] = mapped_column()
    number_of_points: Mapped[int | None] = mapped_column()


class SupportInfo(Base):
    __tablename__: str = 'support_info'

    id: Mapped[int] = mapped_column(primary_key=True)
    instruction_support: Mapped[str | None] = mapped_column()


class InfoBot(Base):
    __tablename__: str = 'info_bot'

    id: Mapped[int] = mapped_column(primary_key=True)
    instruction: Mapped[str | None] = mapped_column()


class TasksForTheWeek(Base):
    __tablename__: str = 'tasks_for_the_weeks'

    id: Mapped[int] = mapped_column(primary_key=True)
    quest: Mapped[str | None] = mapped_column()
    attachment: Mapped[str | None] = mapped_column()


class TasksForTheWeekVocal(Base):
    __tablename__: str = 'tasks_for_the_week_vocals'

    id: Mapped[int] = mapped_column(primary_key=True)
    quest_vocal: Mapped[str | None] = mapped_column()
    attachment_vocal: Mapped[str | None] = mapped_column()


class DailyCheckIn(Base):
    __tablename__ = 'daily_check_ins'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'), unique=True)
    check_in_count: Mapped[int] = mapped_column(default=1)
    date = mapped_column(Date)

    student = relationship(argument='Student', back_populates='daily_check_ins')


class DailyCheckInVocal(Base):
    __tablename__ = 'daily_check_ins_vocal'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'), unique=True)
    check_in_count: Mapped[int] = mapped_column(default=1)
    date = mapped_column(Date)

    student = relationship(argument='Student', back_populates='daily_check_ins_vocal')


class Task1(Base):
    __tablename__: str = 'tasks_1'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'), unique=False)
    name: Mapped[str | None] = mapped_column()
    last_name: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    date: Mapped[str] = mapped_column()
    is_approved = mapped_column(Boolean)

    student = relationship(argument='Student', back_populates='tasks1')


class Task2(Base):
    __tablename__: str = 'tasks_2'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'), unique=False)
    name: Mapped[str | None] = mapped_column()
    last_name: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    month: Mapped[str | None] = mapped_column()
    year: Mapped[int] = mapped_column()
    is_approved = mapped_column(Boolean)

    student = relationship(argument='Student', back_populates='tasks2')


class Task3(Base):
    __tablename__: str = 'tasks_3'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'), unique=False)
    name: Mapped[str | None] = mapped_column()
    last_name: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    month: Mapped[str | None] = mapped_column()
    year: Mapped[int] = mapped_column()
    is_approved = mapped_column(Boolean)

    student = relationship(argument='Student', back_populates='tasks3')


class Task4(Base):
    __tablename__: str = 'tasks_4'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'), unique=False)
    name: Mapped[str | None] = mapped_column()
    last_name: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    date: Mapped[str | None] = mapped_column()
    link: Mapped[str | None] = mapped_column(Text)
    is_approved = mapped_column(Boolean)

    student = relationship(argument='Student', back_populates='tasks4')


class Task5(Base):
    __tablename__: str = 'tasks_5'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'), unique=False)
    name: Mapped[str | None] = mapped_column()
    last_name: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    date: Mapped[str | None] = mapped_column()
    link: Mapped[str | None] = mapped_column(Text)
    is_approved = mapped_column(Boolean)

    student = relationship(argument='Student', back_populates='tasks5')


class Task6(Base):
    __tablename__: str = 'tasks_6'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'), unique=False)
    name: Mapped[str | None] = mapped_column()
    last_name: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    date: Mapped[str] = mapped_column()
    is_approved = mapped_column(Boolean)

    student = relationship(argument='Student', back_populates='tasks6')


class Task7(Base):
    __tablename__: str = 'tasks_7'

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id'), unique=False)
    name: Mapped[str | None] = mapped_column()
    last_name: Mapped[str | None] = mapped_column()
    phone: Mapped[str | None] = mapped_column()
    phone_friend: Mapped[str | None] = mapped_column()
    is_approved = mapped_column(Boolean)

    student = relationship(argument='Student', back_populates='tasks7')


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
