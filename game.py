# -*- coding: utf-8 -*-

# # pip install -r requirements.txt

from stage_04_soldiers.devastator import DevastatorDrone
from astrobox.space_field import SpaceField
from kovalev import KovalevDrone
from sivkov import SivkovDrone
from okhotnikov_f_n import OkhotnikovFNDrone

NUMBER_OF_DRONES = 5

if __name__ == '__main__':
    scene = SpaceField(
        field=(1200, 1200),
        speed=5,
        asteroids_count=15,
        can_fight=True,
    )
    team_1 = [KovalevDrone() for _ in range(NUMBER_OF_DRONES)]
    team_2 = [SivkovDrone() for _ in range(NUMBER_OF_DRONES)]
    team_3 = [DevastatorDrone() for _ in range(NUMBER_OF_DRONES)]
    team_4 = [OkhotnikovFNDrone() for _ in range(NUMBER_OF_DRONES)]
    scene.go()


# Первый этап: зачёт!
# Второй этап: зачёт!
# Третий этап: зачёт!
# Четвертый этап: зачёт!
