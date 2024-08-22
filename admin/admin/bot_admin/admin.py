import requests
import pytz

from datetime import datetime

from django.contrib import admin
from django.conf import settings

from .models import Teacher, Student, StudentTeacher, Homework, PointsHistory, Administrator, Password, \
    MonetizationSystem, MonetizationSystemPoints, PointsExchange, SupportInfo, InfoBot, TasksForTheWeek, \
    TasksForTheWeekVocal, DailyCheckIn, Task1, Task2, Task3, Task4, Task5, Task6, Task7, TgIdPhone, StudentGift


class TeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'last_name', 'specialisation', 'password_teacher')
    search_fields = ('name', 'last_name')
    list_filter = ('specialisation',)


admin.site.register(Teacher, TeacherAdmin)


class StudentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'tg_id', 'date_of_registration', 'name', 'last_name', 'phone', 'specialisation_student', 'point'
    )
    search_fields = ('name', 'last_name', 'phone')
    list_filter = ('specialisation_student',)

    def has_add_permission(self, request):
        return False


admin.site.register(Student, StudentAdmin)


class StudentGiftAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student_name', 'student_last_name', 'student_phone', 'date_received', 'gift_name', 'is_approved'
    )
    search_fields = ('student_name', 'student_last_name', 'student_phone')

    def has_add_permission(self, request):
        return False


admin.site.register(StudentGift, StudentGiftAdmin)


class StudentTeacherAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_id', 'teacher_id')

    def has_add_permission(self, request):
        return False


admin.site.register(StudentTeacher, StudentTeacherAdmin)


class TgIdPhoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'tg_id', 'phone')

    def has_add_permission(self, request):
        return False


admin.site.register(TgIdPhone, TgIdPhoneAdmin)


class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_id', 'teacher_id', 'file_hash', 'file_type', 'submission_time', 'feedback_sent')

    def has_add_permission(self, request):
        return False


admin.site.register(Homework, HomeworkAdmin)


class PointsHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_id', 'points_added', 'date_added')

    def has_add_permission(self, request):
        return False


admin.site.register(PointsHistory, PointsHistoryAdmin)


class AdministratorAdmin(admin.ModelAdmin):
    list_display = ('id', 'administrator_tg_id')


admin.site.register(Administrator, AdministratorAdmin)


class PasswordAdmin(admin.ModelAdmin):
    list_display = ('id', 'password_newsletter')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


admin.site.register(Password, PasswordAdmin)


class MonetizationSystemAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'number_of_points')


admin.site.register(MonetizationSystem, MonetizationSystemAdmin)


class MonetizationSystemPointsAdmin(admin.ModelAdmin):
    list_display = ('id', 'task', 'number_of_points')


admin.site.register(MonetizationSystemPoints, MonetizationSystemPointsAdmin)


class PointsExchangeAdmin(admin.ModelAdmin):
    list_display = ('id', 'present', 'number_of_points')


admin.site.register(PointsExchange, PointsExchangeAdmin)


class SupportInfoAdmin(admin.ModelAdmin):
    list_display = ('id', 'instruction_support')


admin.site.register(SupportInfo, SupportInfoAdmin)


class InfoBotAdmin(admin.ModelAdmin):
    list_display = ('id', 'instruction')


admin.site.register(InfoBot, InfoBotAdmin)


class TasksForTheWeekAdmin(admin.ModelAdmin):
    list_display = ('id', 'quest', 'attachment')


admin.site.register(TasksForTheWeek, TasksForTheWeekAdmin)


class TasksForTheWeekVocalAdmin(admin.ModelAdmin):
    list_display = ('id', 'quest_vocal', 'attachment_vocal')


admin.site.register(TasksForTheWeekVocal, TasksForTheWeekVocalAdmin)


class DailyCheckInAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_id', 'check_in_count', 'date')

    def has_add_permission(self, request):
        return False


admin.site.register(DailyCheckIn, DailyCheckInAdmin)


def send_telegram_message(chat_id, text):
    token = settings.TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, data=payload)
    return response.json()


def make_approve_task(points):
    @admin.action(description='Подтвердить выполнение задания')
    def approve_task(modeladmin, request, queryset):
        for task in queryset:
            if not task.is_approved:
                task.is_approved = True
                task.save()

                student = task.student
                if student.point is None:
                    student.point = 0
                student.point += points
                student.save()

                PointsHistory.objects.create_points_history(student=student, points_added=points,
                                                            date_added=datetime.now())

                send_telegram_message(student.tg_id, text=f"✅Вам добавлено +{points} баллов за выполнение задания.")

    return approve_task


class Task1Admin(admin.ModelAdmin):
    list_display = ('id', 'student', 'phone', 'date', 'is_approved')
    actions = [make_approve_task(3)]

    def save_model(self, request, obj, form, change):
        if change:
            original_obj = self.model.objects.get(pk=obj.pk)
            if not original_obj.is_approved and obj.is_approved:
                student = obj.student
                if student.point is None:
                    student.point = 0
                points_added = 3
                student.point += points_added
                student.save()

                PointsHistory.objects.create_points_history(student=student, points_added=points_added,
                                                            date_added=obj.date)

                send_telegram_message(student.tg_id, text="✅Вам добавлено +3 балла за выполнение задания от школы!")

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False


admin.site.register(Task1, Task1Admin)


class Task2Admin(admin.ModelAdmin):
    list_display = ('id', 'student', 'phone', 'month', 'year', 'is_approved')
    actions = [make_approve_task(2)]

    def save_model(self, request, obj, form, change):
        if change:
            original_obj = self.model.objects.get(pk=obj.pk)
            if not original_obj.is_approved and obj.is_approved:
                student = obj.student
                if student.point is None:
                    student.point = 0
                points_added = 2
                student.point += points_added
                student.save()

                PointsHistory.objects.create_points_history(student=student, points_added=points_added,
                                                            date_added=obj.date)

                send_telegram_message(student.tg_id, text="✅Вам добавлено +2 балла за выполнение задания от школы!")

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False


admin.site.register(Task2, Task2Admin)


class Task3Admin(admin.ModelAdmin):
    list_display = ('id', 'student', 'phone', 'month', 'year', 'is_approved')
    actions = [make_approve_task(1)]

    def save_model(self, request, obj, form, change):
        if change:
            original_obj = self.model.objects.get(pk=obj.pk)
            if not original_obj.is_approved and obj.is_approved:
                student = obj.student
                if student.point is None:
                    student.point = 0
                points_added = 1
                student.point += points_added
                student.save()

                PointsHistory.objects.create_points_history(student=student, points_added=points_added,
                                                            date_added=obj.date)

                send_telegram_message(student.tg_id, text="✅Вам добавлен +1 балл за выполнение задания от школы!")

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False


admin.site.register(Task3, Task3Admin)


class Task4Admin(admin.ModelAdmin):
    list_display = ('id', 'student', 'phone', 'date', 'link', 'is_approved')
    actions = [make_approve_task(1)]

    def save_model(self, request, obj, form, change):
        if change:
            original_obj = self.model.objects.get(pk=obj.pk)
            if not original_obj.is_approved and obj.is_approved:
                student = obj.student
                if student.point is None:
                    student.point = 0
                points_added = 1
                student.point += points_added
                student.save()

                PointsHistory.objects.create_points_history(student=student, points_added=points_added,
                                                            date_added=obj.date)

                send_telegram_message(student.tg_id, text="✅Вам добавлен +1 балл за выполнение задания от школы!")

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False


admin.site.register(Task4, Task4Admin)


class Task5Admin(admin.ModelAdmin):
    list_display = ('id', 'student', 'phone', 'date', 'link', 'is_approved')
    actions = [make_approve_task(1)]

    def save_model(self, request, obj, form, change):
        if change:
            original_obj = self.model.objects.get(pk=obj.pk)
            if not original_obj.is_approved and obj.is_approved:
                student = obj.student
                if student.point is None:
                    student.point = 0
                points_added = 1
                student.point += points_added
                student.save()

                PointsHistory.objects.create_points_history(student=student, points_added=points_added,
                                                            date_added=obj.date)

                send_telegram_message(student.tg_id, text="✅Вам добавлен +1 балл за выполнение задания от школы!")

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False


admin.site.register(Task5, Task5Admin)


class Task6Admin(admin.ModelAdmin):
    list_display = ('id', 'student', 'phone', 'date', 'is_approved')
    actions = [make_approve_task(1)]

    def save_model(self, request, obj, form, change):
        if change:
            original_obj = self.model.objects.get(pk=obj.pk)
            if not original_obj.is_approved and obj.is_approved:
                student = obj.student
                if student.point is None:
                    student.point = 0
                points_added = 1
                student.point += points_added
                student.save()

                PointsHistory.objects.create_points_history(student=student, points_added=points_added,
                                                            date_added=obj.date)

                send_telegram_message(student.tg_id, text="✅Вам добавлен +1 балл за выполнение задания от школы!")

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False


admin.site.register(Task6, Task6Admin)


class Task7Admin(admin.ModelAdmin):
    list_display = ('id', 'student', 'phone', 'phone_friend', 'is_approved')
    actions = [make_approve_task(5)]

    def save_model(self, request, obj, form, change):
        if change:
            original_obj = self.model.objects.get(pk=obj.pk)
            if not original_obj.is_approved and obj.is_approved:
                student = obj.student
                if student.point is None:
                    student.point = 0
                points_added = 5
                student.point += points_added
                student.save()

                PointsHistory.objects.create_points_history(student=student, points_added=points_added,
                                                            date_added=obj.date)

                send_telegram_message(student.tg_id, text="✅Вам добавлено +5 баллов за выполнение задания от школы!")

        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False


admin.site.register(Task7, Task7Admin)

# class MediaFileAdmin(admin.ModelAdmin):
#     list_display = ('id', 'file')
#     search_fields = ('file',)
#
#
# admin.site.register(MediaFile, MediaFileAdmin)
