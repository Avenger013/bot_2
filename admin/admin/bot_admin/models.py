import random

from django.db import models
from datetime import datetime


class Teacher(models.Model):
    VOCAL = 'Вокал'
    GUITAR = 'Гитара'
    SPECIALISATION_CHOICES = [
        (VOCAL, 'Вокал'),
        (GUITAR, 'Гитара'),
    ]

    id = models.AutoField(primary_key=True, verbose_name='ID')
    name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    specialisation = models.CharField(
        max_length=6,
        choices=SPECIALISATION_CHOICES,
        default=VOCAL,
        verbose_name='Специализация'
    )
    password_teacher = models.CharField(max_length=5, default=lambda: str(random.randint(10000, 99999)),
                                        verbose_name='Пароль')

    class Meta:
        managed = False
        db_table = 'teachers'
        verbose_name = 'Преподавателя'
        verbose_name_plural = 'Преподаватели'

    def __str__(self):
        return f"{self.name} {self.last_name}"


class Student(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    tg_id = models.BigIntegerField(verbose_name='Телеграмм ID')
    date_of_registration = models.DateTimeField(default=datetime.now, verbose_name='Дата регистрации')
    name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Имя')
    last_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Фамилия')
    phone = models.CharField(max_length=255, null=True, blank=True, verbose_name='Телефон')
    specialisation_student = models.CharField(max_length=255, null=True, blank=True, verbose_name='Специализация')
    point = models.IntegerField(null=True, blank=True, verbose_name='Количество баллов')

    class Meta:
        managed = False
        db_table = 'students'
        verbose_name = 'Ученика'
        verbose_name_plural = 'Ученики'

    def __str__(self):
        return f"{self.name} {self.last_name}"


class StudentTeacher(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, db_column='student_id')
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, db_column='teacher_id', null=True)

    class Meta:
        managed = False
        db_table = 'student_teacher'
        verbose_name = 'Связь'
        verbose_name_plural = 'Связи учеников и преподавателей'


class TgIdPhone(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    tg_id = models.BigIntegerField(verbose_name='Телеграмм ID')
    phone = models.CharField(max_length=255, null=True, blank=True, verbose_name='Телефон')

    class Meta:
        managed = False
        db_table = 'tg_id_phone'
        verbose_name = 'Связь'
        verbose_name_plural = 'Связи номеров телефонов и telegram id'


class StudentGift(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    student_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Имя ученика')
    student_last_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Фамилия ученика')
    student_phone = models.CharField(max_length=255, null=True, blank=True, verbose_name='Телефон ученика')
    date_received = models.DateTimeField(default=datetime.now, verbose_name='Дата обмена баллов')
    gift_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='Список подарков для вручения')
    is_approved = models.BooleanField(default=False, verbose_name='Отметка о получении всех подарков')

    class Meta:
        managed = False
        db_table = 'student_gifts'
        verbose_name = 'Подарок'
        verbose_name_plural = 'Список подарков для вручения ученикам'


class Homework(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, db_column='student_id')
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, db_column='teacher_id')
    file_hash = models.CharField(max_length=255, null=True, blank=True)
    file_type = models.CharField(max_length=255, null=True, blank=True)
    submission_time = models.DateTimeField()
    feedback_sent = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'homeworks'
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'


class PointsHistoryManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def create_points_history(self, student, points_added, date_added):
        points_history = self.create(student=student, points_added=points_added, date_added=date_added)
        return points_history


class PointsHistory(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, db_column='student_id')
    points_added = models.IntegerField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    objects = PointsHistoryManager()

    class Meta:
        managed = False
        db_table = 'points_history'
        verbose_name = 'Историю'
        verbose_name_plural = 'История получения баллов'


class Administrator(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    administrator_tg_id = models.BigIntegerField()

    class Meta:
        managed = False
        db_table = 'administrators'
        verbose_name = 'SMM-специалиста'
        verbose_name_plural = 'SMM-специалисты'


class Password(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    password_newsletter = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'passwords'
        verbose_name = 'Пароль'
        verbose_name_plural = 'Пароль SMM-специалистов'


class MonetizationSystem(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    task = models.TextField(null=True, blank=True)
    number_of_points = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'monetization_systems'
        verbose_name = 'Задание для получения баллов'
        verbose_name_plural = 'Общие задания для получения баллов'


class MonetizationSystemPoints(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    task = models.TextField(null=True, blank=True)
    number_of_points = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'monetization_systems_points'
        verbose_name = 'Задание от школы'
        verbose_name_plural = 'Задания от школы для получения баллов'


class PointsExchange(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    present = models.TextField(null=True, blank=True)
    number_of_points = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'points_exchanges'
        verbose_name = 'Подарок'
        verbose_name_plural = 'Список подарков для обмена за баллы'


class SupportInfo(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    instruction_support = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'support_info'
        verbose_name = 'Информацию'
        verbose_name_plural = 'Техническая поддержка'


class InfoBot(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    instruction = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'info_bot'
        verbose_name = 'Информацию'
        verbose_name_plural = 'Информация о боте'


class TasksForTheWeek(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    quest = models.TextField(null=True, blank=True)
    attachment = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tasks_for_the_weeks'
        verbose_name = 'Задание'
        verbose_name_plural = 'Трекер (гитара)'


class TasksForTheWeekVocal(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    quest_vocal = models.TextField(null=True, blank=True)
    attachment_vocal = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'tasks_for_the_week_vocals'
        verbose_name = 'Задание'
        verbose_name_plural = 'Трекер (вокал)'


class DailyCheckIn(models.Model):
    id = models.AutoField(primary_key=True, verbose_name='ID')
    student = models.OneToOneField('Student', on_delete=models.CASCADE, db_column='student_id')
    check_in_count = models.IntegerField(default=1)
    date = models.DateField()

    class Meta:
        managed = False
        db_table = 'daily_check_ins'
        verbose_name = 'Информацию об отметках'
        verbose_name_plural = 'Отметки о выполнении трекера'


class Task1(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=255, null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name='Отметка о выполнении задания')

    class Meta:
        managed = False
        db_table = 'tasks_1'
        verbose_name = 'Посещение урока'
        verbose_name_plural = 'Посещение уроков'


class Task2(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    month = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name='Отметка о выполнении задания')

    class Meta:
        managed = False
        db_table = 'tasks_2'
        verbose_name = 'Отсутствие пропуска'
        verbose_name_plural = 'Отсутствие пропусков'


class Task3(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    month = models.CharField(max_length=255, null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name='Отметка о выполнении задания')

    class Meta:
        managed = False
        db_table = 'tasks_3'
        verbose_name = 'Выступление на квартирнике'
        verbose_name_plural = 'Выступления на квартирниках'


class Task4(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=255, null=True, blank=True)
    link = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name='Отметка о выполнении задания')

    class Meta:
        managed = False
        db_table = 'tasks_4'
        verbose_name = 'Пост/рилс в соц. сетях с упоминанием школы'
        verbose_name_plural = 'Посты/рилсы в соц. сетях с упоминаниями школы'


class Task5(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=255, null=True, blank=True)
    link = models.TextField(null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name='Отметка о выполнении задания')

    class Meta:
        managed = False
        db_table = 'tasks_5'
        verbose_name = 'Отзыв на Яндекс и 2Гис'
        verbose_name_plural = 'Отзывы на Яндекс и 2Гис'


class Task6(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=255, null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name='Отметка о выполнении задания')

    class Meta:
        managed = False
        db_table = 'tasks_6'
        verbose_name = 'Посещение мероприятия'
        verbose_name_plural = 'Посещение мероприятий'


class Task7(models.Model):
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    phone_friend = models.CharField(max_length=255, null=True, blank=True)
    is_approved = models.BooleanField(default=False, verbose_name='Отметка о выполнении задания')

    class Meta:
        managed = False
        db_table = 'tasks_7'
        verbose_name = 'Посещение пробного занятия человеком, которому порекомендовали школу'
        verbose_name_plural = 'Посещения пробных занятий людьми, которым порекомендовали школу'


# class MediaFile(models.Model):
#     file = models.FileField(upload_to='tasks/', verbose_name='Файл')
#
#     class Meta:
#         verbose_name = 'Медиа файл'
#         verbose_name_plural = 'Медиа файлы'
#
#     def __str__(self):
#         return self.file.name
