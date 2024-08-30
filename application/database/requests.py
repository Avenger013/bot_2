from datetime import datetime
from sqlalchemy import select, update, func, extract
from sqlalchemy.orm import selectinload
from typing import Optional

from application.database.models import Teacher, Student, Administrator, Password, PointsHistory, StudentTeacher, \
    MonetizationSystem, PointsExchange, SupportInfo, InfoBot, TasksForTheWeek, DailyCheckIn, Homework, \
    TasksForTheWeekVocal, MonetizationSystemPoints, DailyCheckInVocal, async_session


async def get_teachers():
    async with async_session() as session:
        result = await session.scalars(select(Teacher))
        return result


async def get_teachers1(student_id: int):
    async with async_session() as session:
        result = await session.scalars(
            select(Teacher).join(StudentTeacher).where(StudentTeacher.student_id == student_id)
        )
        return result.all()


async def get_money():
    async with async_session() as session:
        result = await session.scalars(select(MonetizationSystem))
        return result.all()


async def get_money_points():
    async with async_session() as session:
        result = await session.scalars(select(MonetizationSystemPoints))
        return result.all()


async def get_gifts():
    async with async_session() as session:
        result = await session.scalars(select(PointsExchange))
        return result.all()


async def get_info():
    async with async_session() as session:
        result = await session.scalars(select(InfoBot))
        return result


async def get_tasks_for_the_week(date_of_registration, specialisation):
    today = datetime.now().date()
    date_of_registration = date_of_registration.date()
    days_since_registration = (today - date_of_registration).days
    current_week = days_since_registration // 7

    async with async_session() as session:
        if specialisation == 'Гитара':
            total_tasks = await session.scalar(select(func.count()).select_from(TasksForTheWeek))
            task_class = TasksForTheWeek
        else:
            total_tasks = await session.scalar(select(func.count()).select_from(TasksForTheWeekVocal))
            task_class = TasksForTheWeekVocal

        task_index = current_week % total_tasks if total_tasks > 0 else 0
        result = await session.execute(
            select(task_class).offset(task_index).limit(1)
        )
        task = result.scalars().first()
        return task, task_index + 1 if task else None


async def get_support():
    async with async_session() as session:
        result = await session.scalars(select(SupportInfo))
        return result


async def get_teachers_vocal():
    async with async_session() as session:
        query = select(Teacher).where(Teacher.specialisation == "Вокал")
        result = await session.scalars(query)
        return result.all()


async def get_teachers_guitar():
    async with async_session() as session:
        query = select(Teacher).where(Teacher.specialisation == "Гитара")
        result = await session.scalars(query)
        return result.all()


async def get_users():
    async with async_session() as session:
        users = await session.scalars(select(Student))
        return users


async def get_users_by_ids(ids=None):
    async with async_session() as session:
        query = select(Student)
        if ids is not None:
            query = query.where(Student.id.in_(ids))
        users = await session.scalars(query)
        return users


async def get_student_info(session, tg_id):
    try:
        student = await session.scalar(select(Student).filter(Student.tg_id == tg_id))
        if student:
            teacher_result = await session.execute(
                select(Teacher).join(StudentTeacher).filter(StudentTeacher.student_id == student.id))
            teachers = teacher_result.scalars().all()

            last_check_in_record = await session.execute(
                select(DailyCheckIn)
                .where(DailyCheckIn.student_id == student.id)
                .order_by(DailyCheckIn.date.desc())
                .limit(1)
            )
            last_check_in = last_check_in_record.scalars().first()
            check_in_count = last_check_in.check_in_count if last_check_in else 0

            last_check_in_record_vocal = await session.execute(
                select(DailyCheckInVocal)
                .where(DailyCheckInVocal.student_id == student.id)
                .order_by(DailyCheckInVocal.date.desc())
                .limit(1)
            )
            last_check_in_vocal = last_check_in_record_vocal.scalars().first()
            check_in_count_vocal = last_check_in_vocal.check_in_count if last_check_in_vocal else 0

            return student, teachers, check_in_count, check_in_count_vocal
        else:
            return None, [], 0
    except Exception as e:
        print(f"Error in get_student_info: {e}")
        return None, [], 0


async def get_student(session, tg_id):
    try:
        student = await session.scalar(select(Student).filter(Student.tg_id == tg_id))
        return student
    except Exception as e:
        print(f"Error in get_student: {e}")
        return None


async def get_homework_with_details(session, file_hash):
    try:
        result = await session.execute(
            select(Homework)
            .options(selectinload(Homework.student))
            .where(Homework.file_hash == file_hash)
        )
        homework = result.scalar_one_or_none()

        if homework:
            student = homework.student
            return homework, student
        else:
            return None, None, None

    except Exception as e:
        print(f"Error in get_homework_with_details: {e}")
        return None, None, None


async def get_student_by_id(session, student_id):
    try:
        student = await session.scalar(select(Student).where(Student.id == student_id))
        return student
    except Exception as e:
        print(f"Error in get_student_by_id: {e}")
        return None


async def get_teacher_by_id(session, teacher_id):
    try:
        teacher = await session.scalar(select(Teacher).where(Teacher.id == teacher_id))
        return teacher
    except Exception as e:
        print(f"Error in get_teacher_by_id: {e}")
        return None


async def get_homework_by_file_hash(session, file_hash):
    try:
        result = await session.execute(
            select(Homework)
            .options(selectinload(Homework.student))
            .where(Homework.file_hash == file_hash)
        )
        homework = result.scalar_one_or_none()
        return homework
    except Exception as e:
        print(f"Error in get_homework_by_file_hash: {e}")
        return None


async def update_student_points(session, student_id, new_points):
    try:
        await session.execute(
            update(Student)
            .where(Student.id == student_id)
            .values(point=new_points)
        )
        await session.commit()
    except Exception as e:
        print(f"Error in update_student_points: {e}")
        await session.rollback()


async def update_feedback_sent(session, homework_id):
    try:
        await session.execute(
            update(Homework)
            .where(Homework.id == homework_id)
            .values(feedback_sent=Homework.feedback_sent + 1)
        )
        await session.commit()
    except Exception as e:
        print(f"Error in update_feedback_sent: {e}")
        await session.rollback()


async def get_top_students_2(limit: int = 10):
    async with async_session() as session:
        result = await session.execute(
            select(Student)
            .order_by(Student.point.desc())
            .limit(limit)
        )
        top_students = result.scalars().all()
        return top_students


async def get_top_students(limit: int = 10):
    async with async_session() as session:
        subquery_sum = (
            select(
                PointsHistory.student_id,
                func.sum(PointsHistory.points_added).label('total_points')
            )
            .group_by(PointsHistory.student_id)
            .subquery()
        )

        subquery_max = (
            select(
                subquery_sum.c.student_id,
                func.max(subquery_sum.c.total_points).label('max_points')
            )
            .group_by(subquery_sum.c.student_id)
            .subquery()
        )

        result = await session.execute(
            select(Student)
            .join(subquery_max, Student.id == subquery_max.c.student_id)
            .order_by(subquery_max.c.max_points.desc())
            .limit(limit)
        )

        top_students = result.scalars().all()
        return top_students


async def get_admin():
    async with async_session() as session:
        result = await session.scalars(select(Administrator.administrator_tg_id))
        admins_tg_id = result.all()
        return admins_tg_id


async def get_gift_by_id(gift_id: int):
    async with async_session() as session:
        result = await session.execute(select(PointsExchange).where(PointsExchange.id == gift_id))
        gift = result.scalars().first()
        return gift


async def get_task_by_id(task_id: int):
    async with async_session() as session:
        result = await session.execute(select(MonetizationSystem).where(MonetizationSystem.id == task_id))
        task = result.scalars().first()
        return task


async def get_newsletter_password() -> str:
    async with async_session() as session:
        result = await session.scalar(select(Password.password_newsletter))
        return result


async def add_administrator(admin_tg_id: int):
    async with async_session() as session:
        new_admin = Administrator(administrator_tg_id=admin_tg_id)
        session.add(new_admin)
        await session.commit()


async def get_teacher_by_password(input_password: str) -> Optional[Teacher]:
    async with async_session() as session:
        result = await session.execute(select(Teacher).where(Teacher.password_teacher == input_password))
        return result.scalars().first()


async def get_leader_of_the_month(year: int, month: int):
    async with async_session() as session:
        result = await session.execute(
            select(
                PointsHistory.student_id,
                func.sum(PointsHistory.points_added).label('total_points')
            )
            .join(PointsHistory.student)
            .filter(extract('year', PointsHistory.date_added) == year)
            .filter(extract('month', PointsHistory.date_added) == month)
            .group_by(PointsHistory.student_id)
            .order_by(func.sum(PointsHistory.points_added).desc())
            .limit(1)
        )
        leader = result.first()
        if leader:
            student = await session.get(Student, leader[0])
            return {
                'name': student.name,
                'last_name': student.last_name,
                'total_points': leader[1]
            }
        else:
            return None
