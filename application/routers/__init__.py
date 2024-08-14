__all__ = ("router", )

from aiogram import Router

from .start_router import router as router_start
from .student_router import router as router_student
from .teacher_router import router as router_teacher
from .dz_router import router as router_dz
from .dz_2_router import router as router_dz_2
from .dz_3_router import router as router_dz_3
from .lk_and_commands import router as router_lk_and_commands
from .admin_router import router as router_admin
from .last_router import router as router_last
from .getting_points_router import router as router_getting_points

router = Router(name=__name__)

router.include_routers(
    router_start,
    router_student,
    router_teacher,
    router_dz,
    router_dz_2,
    router_dz_3,
    router_lk_and_commands,
    router_getting_points,
    router_admin,
)

router.include_router(router_last)

