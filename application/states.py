from aiogram.fsm.state import StatesGroup, State


class PasswordCheck(StatesGroup):
    EnterPassword = State()


class RegistrationState(StatesGroup):
    EnterPhone = State()
    EnterName = State()
    EnterLastName = State()
    ChoiceSpecialisation = State()
    ChoiceIDTeacher = State()


class UpdateRegistrationState(StatesGroup):
    UpdateName = State()
    UpdateLastName = State()
    UpdatePhone = State()
    UpdateIDTeacher = State()
    UpdateChoiceSpecialisation = State()


class HomeworkState(StatesGroup):
    ChoiceTeacher = State()
    ChoosingDZType = State()
    WaitingForPhoto = State()
    WaitingForVideo = State()
    WaitingForTextAndLinks = State()
    WaitingForVoice = State()


class HomeworkState2(StatesGroup):
    ChoiceTeacher2 = State()
    ChoosingDZType2 = State()
    WaitingForVideo2 = State()
    WaitingForLinks2 = State()


class Newsletter(StatesGroup):
    Text = State()


class AdminVerification(StatesGroup):
    Awaiting_password = State()


class UpdateParts(StatesGroup):
    UpdatePartsName = State()
    UpdatePartsLastName = State()
    UpdatePartsPhone = State()
    UpdatePartsIDTeacher = State()
    UpdatePartsChoiceSpecialisation = State()


class Gifts(StatesGroup):
    Gift = State()


class Systems(StatesGroup):
    System = State()


class FeedbackState(StatesGroup):
    WaitingForText = State()


class CalendarState(StatesGroup):
    Waiting_for_date = State()
    Waiting_for_month = State()
    Waiting_for_performance = State()
    Waiting_for_link = State()
    Waiting_for_link_review = State()
    Waiting_for_date_event = State()
    Waiting_for_phone = State()
