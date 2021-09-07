# -*- coding: utf-8 -*-
import math
from random import shuffle

from astrobox.core import Drone
import logging
from astrobox.themes.default import MOTHERSHIP_HEALING_DISTANCE
from robogame_engine import GameObject
from robogame_engine.geometry import Point, Vector
from robogame_engine.theme import theme

logging.basicConfig(level=logging.DEBUG)


class KovalevDrone(Drone):
    """
    Drone model scanning and harvesting elerium as fast, as he can. Run, drone, run!
    """
    my_team = []
    attack_range = 0
    limit_health = 0.5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drone_number = 0
        self.point_for_stats = 0
        self.moved_loaded = 0
        self.moved_unloaded = 0
        self.moved_almost_loaded = 0
        self.role = None
        self.need_stats = True

    def on_born(self):
        self.drone_number = len(self.my_team)
        self.my_team.append(self)
        if self.have_gun:
            self.attack_range = self.gun.shot_distance
        self.role = Turret(self)
        self.role.on_born()

    def on_stop_at_asteroid(self, asteroid):
        self.role.on_stop_at_asteroid(asteroid)

    def on_load_complete(self):
        self.role.on_load_complete()

    def on_stop_at_mothership(self, mothership):
        if self.cargo.payload > 0:
            self.unload_to(mothership)

    def on_unload_complete(self):
        self.role.on_unload_complete()

    def on_stop_at_target(self, target):
        self.role.on_stop_at_target(target)

    def on_stop(self):
        self.role.on_stop()

    def gather_statistics(self):
        distance_traveled = self.distance_to(self.point_for_stats)
        if self.cargo.is_full:
            self.moved_loaded += distance_traveled
        elif not self.cargo.is_full and self.cargo.free_space == 100:
            self.moved_unloaded += distance_traveled
        elif not self.cargo.is_full and self.cargo.free_space > 0:
            self.moved_almost_loaded += distance_traveled

    def move_at(self, target, speed=None):
        if isinstance(self.role, Harvester):
            self.gather_statistics()
            self.point_for_stats = Point(self.coord.x, self.coord.y)
        super().move_at(target)

    def print_statistics(self, for_drones=False, for_team=False):
        if self.need_stats:
            if for_drones:
                if self.target != self.my_mothership:
                    logging.info(f'Stats for drone №{self.drone_number} \n'
                                 f'Distance travelled loaded: {int(self.moved_loaded)} conventional units \n'
                                 f'Distance travelled unloaded: {int(self.moved_unloaded)} conventional units \n'
                                 f'Distance travelled almost loaded: {int(self.moved_almost_loaded)} conventional units'
                                 f' \n'
                                 f'----------------------***********---------------------------')
            if for_team:
                overall_moved_loaded = 0
                overall_moved_unloaded = 0
                overall_moved_almost_loaded = 0
                for drone in self.my_team:
                    if drone.target != self.my_mothership:
                        return
                    overall_moved_loaded += int(drone.moved_loaded)
                    overall_moved_unloaded += int(drone.moved_unloaded)
                    overall_moved_almost_loaded += int(drone.moved_almost_loaded)
                logging.info(f'Overall moved loaded by team - {overall_moved_loaded} \n'
                             f'Overall moved unloaded by team - {overall_moved_unloaded} \n'
                             f'Overall moved almost loaded by team - {overall_moved_almost_loaded} \n')
            for dr in self.my_team:
                dr.need_stats = False


class Role:

    def __init__(self, drone):
        self.drone = drone
        self.enemies = []
        self.enemy_motherships = []
        self.asteroids = []
        self.dead_enemies = []
        self.enemy_dead_motherships = []
        self.overall_points_with_elerium = []
        self.safe_points_with_elerium = []

    def on_born(self):
        pass

    def get_enemies(self):
        self.enemies = [[enemy, self.drone.distance_to(enemy)] for enemy in self.drone.scene.drones
                        if enemy.team != self.drone.team and enemy.is_alive and enemy not in self.enemies]
        self.enemies.sort(key=lambda x: x[1])

    def get_enemies_motherships(self):
        self.enemy_motherships = []
        for mothership in self.drone.scene.motherships:
            if mothership not in self.enemy_motherships \
                    and mothership != self.drone.my_mothership \
                    and mothership.is_alive:
                self.enemy_motherships.append(mothership)

    def get_nearest_enemy(self):
        self.get_enemies()
        if self.enemies:
            nearest_enemy = self.enemies[0][0]
            for enemy, distance_to_enemy in self.enemies:
                if len(self.enemies) == 1:
                    if enemy.distance_to(enemy.my_mothership) > 200 or not enemy.my_mothership.is_alive:
                        nearest_enemy = enemy
                    else:
                        nearest_enemy = enemy.my_mothership
        else:
            nearest_enemy = None
        return nearest_enemy

    def get_angle(self, partner: GameObject, target: GameObject):
        """
        Получает угол между векторами self-target и partner-target
        """
        def scalar(vec1, vec2):
            return vec1.x * vec2.x + vec1.y * vec2.y
        v12 = Vector(self.drone.coord.x - target.coord.x, self.drone.coord.y - target.coord.y)
        v32 = Vector(partner.coord.x - target.coord.x, partner.coord.y - target.coord.y)
        _cos = scalar(v12, v32) / (v12.module * v32.module + 1.e-8)
        return math.degrees(math.acos(_cos))

    def attack_the_target(self, target):
        self.drone.turn_to(target)
        self.drone.gun.shot(target)

    def get_position_near_mothership(self):
        base = self.drone.my_mothership.coord
        koefs = []
        angles = []
        if theme.FIELD_WIDTH > theme.FIELD_HEIGHT:
            koefs = [0.5, 0.2, 0.3, 0.7, 1]
            if (base.x == 90 and base.y == 90) or (base.x != 90 and base.y != 90):
                angles = [-110, -120, 100, 130, 140]
            else:
                angles = [110, 120, -120, -120, -135]
        elif theme.FIELD_WIDTH == theme.FIELD_HEIGHT:
            koefs = [1, 0.4, 0, 0.4, 1]
            if (base.x == 90 and base.y == 90) or (base.x != 90 and base.y != 90):
                angles = [-110, -115, 0, 115, 110]
            else:
                angles = [110, 115, 0, -115, -110]
        elif theme.FIELD_WIDTH < theme.FIELD_HEIGHT:
            koefs = [0.7, 0.3, 0.1, 0.5, 0.9]
            if (base.x == 90 and base.y == 90) or (base.x != 90 and base.y != 90):
                angles = [110, 100, -100, -120, -130]
            else:
                angles = [-110, -100, 100, 120, 130]
        center_field = Point(theme.FIELD_WIDTH // 2, theme.FIELD_HEIGHT // 2)
        central_position = self._get_position_from_points(base, center_field, 0.8, None)
        drone_koef = koefs[self.drone.drone_number]
        drone_angle = angles[self.drone.drone_number]
        final_position = self._get_position_from_points(central_position, center_field, drone_koef, drone_angle)
        return final_position

    @staticmethod
    def _get_position_from_points(first_point, second_point, koef, angle):
        vec = Vector.from_points(first_point, second_point)
        dist = vec.module
        first_koef = 1 / dist
        norm_vec = Vector(vec.x * first_koef * koef, vec.y * first_koef * koef)
        vec_position = norm_vec * MOTHERSHIP_HEALING_DISTANCE
        if angle:
            vec_position.rotate(angle)
        position = Point(first_point.x + vec_position.x, first_point.y + vec_position.y)
        return position

    def get_asteroids_with_elerium(self):
        """
        Метод формирует список астероидов с элериумом и сортирует его по расстоянию до дрона
        """
        self.asteroids = [[asteroid, self.drone.distance_to(asteroid)] for asteroid in self.drone.asteroids
                          if asteroid.counter > 0]
        self.asteroids.sort(key=lambda x: x[1])

    def get_dead_enemies_motherships(self):
        """
        Метод формирует список уничтоженных материнских кораблей противника и сортирует его по расстоянию до дрона
        """
        self.enemy_dead_motherships = [[mothership, self.drone.distance_to(mothership)]
                                       for mothership in self.drone.scene.motherships
                                       if mothership != self.drone.my_mothership and not mothership.is_alive
                                       and mothership.cargo.payload > 0]
        self.enemy_dead_motherships.sort(key=lambda x: x[1])

    def get_dead_enemies(self):
        """
        Метод формирует список уничтоженных дронов противника и сортирует его по расстоянию до дрона
        """
        self.dead_enemies = [[enemy, self.drone.distance_to(enemy)] for enemy in self.drone.scene.drones
                             if enemy.team != self.drone.team and not enemy.is_alive and enemy.cargo.payload > 0]
        self.dead_enemies.sort(key=lambda x: x[1])

    def get_safe_points_to_harvest(self):
        """
        Метод формирует список безопасных точек для сбора ресурсов и сортирует его по расстоянию до дрона
        """
        self.safe_points_with_elerium = [[point[0], self.drone.distance_to(point[0])] for point in
                                         self.overall_points_with_elerium
                                         if point[0].distance_to(self.drone.my_mothership) < self.drone.attack_range]
        self.safe_points_with_elerium.sort(key=lambda x: x[1])

    def get_overall_points_to_harvest(self):
        """
        Метод формирует список всех доступных точек для сбора ресурсов и сортирует его по расстоянию до дрона
        """
        self.get_dead_enemies()
        self.get_dead_enemies_motherships()
        self.get_asteroids_with_elerium()
        self.overall_points_with_elerium = list(self.asteroids + self.dead_enemies + self.enemy_dead_motherships)
        self.overall_points_with_elerium.sort(key=lambda x: x[1])

    def change_the_role(self, role, drone):
        """
        :param role: необходимая роль
        :param drone: дрон
        Метод изменяет роль дрона
        """
        self.get_overall_points_to_harvest()
        self.drone.role = role(drone)
        self.drone.role.on_born()

    def __str__(self):
        return 'Role'


class Harvester(Role):
    """
    Дрон сборщик, обнаруживающий и собирающий элериум, так быстро как может с астероидов, уничтоженных
    дронов и материнских кораблей противника
    """
    def on_born(self):
        self.drone.point_for_stats = Point(self.drone.coord.x, self.drone.coord.y)
        if self.drone.distance_to(self.drone.my_mothership) < 200:
            self.on_stop_at_target(target=None)
        else:
            self.drone.on_stop()

    def on_stop_at_asteroid(self, asteroid):
        target = self.get_point()
        if target != asteroid:
            self.drone.turn_to(target)
        self.drone.load_from(asteroid)

    def on_load_complete(self):
        self.drone.target = self.get_point()
        self._update_drones_targets()
        self.drone.move_at(self.drone.target)

    def on_stop_at_mothership(self, mothership):
        self.drone.unload_to(mothership)

    def on_unload_complete(self):
        self.drone.target = self.get_point()
        self._update_drones_targets()
        self.get_safe_points_to_harvest()
        if self.safe_points_with_elerium:
            self.drone.move_at(self.safe_points_with_elerium[0][0])
        else:
            self.change_the_role(Turret, self.drone)

    def on_stop_at_target(self, target):
        if target:
            if target.x == self.drone.my_mothership.coord.x and target.y == self.drone.my_mothership.coord.y:
                self.drone.unload_to(self.drone.my_mothership)
            else:
                self.drone.target = self.get_point()
                self.drone.on_stop_at_asteroid(self.drone.target)
        else:
            self.on_stop()

    def on_stop(self):
        self.drone.target = self.get_point()
        self.drone.move_at(self.drone.target)

    def get_point(self):
        """
        В случае если на карте нет доступных целей с элериумом и живых врагов, метод возвращает в качестве цели
        материнский корабль дрона. Если нет доступных целей с элериумом, но присутствуют дроны или материнские
        корабли противника, происходит переключение на атакующую роль.
        Если присутствуют цели для сбора, то в зависимости от того, присутствуют дроны противника или нет и их
        расстояния от сборщика, возвращает оптимальную цель для сбора.
        :return: obj; type of obj = astrobox.core.MotherShip or astrobox.core.Asteroid or astrobox.core.Drone
        """
        if not self.drone.cargo.is_full:
            self.get_overall_points_to_harvest()
            nearest_point = self._get_nearest_point_to_harvest()
            if nearest_point == self.drone.my_mothership:
                if self.enemies:
                    if self.drone.cargo.payload == 0:
                        if len(self.enemies) < ((len(self.drone.scene.teams) - 1) * 3):
                            self.change_the_role(Destructor, self.drone)
                        else:
                            self.change_the_role(Turret, self.drone)
                elif not self.enemies and not self.enemy_motherships and not self.overall_points_with_elerium:
                    self.drone.print_statistics(for_team=True)
            return nearest_point
        else:
            return self.drone.my_mothership

    def _get_nearest_point_to_harvest(self):
        """
        Определение ближайшей точки для сбора ресурсов
        :return: оптимальная точка с ресурсами или материнский корабль
        """
        self.get_enemies()
        self.get_enemies_motherships()
        nearest_point = self.drone.my_mothership
        if self.drone.meter_2 < self.drone.limit_health:
            nearest_point = self.drone.my_mothership
        else:
            if self.enemies and self.overall_points_with_elerium:
                if len(self.enemies) > 10 and self.drone.my_mothership.payload < 500:
                    nearest_point = self.overall_points_with_elerium[0][0]
                else:
                    self.get_safe_points_to_harvest()
                    if self.safe_points_with_elerium:
                        nearest_point = self.safe_points_with_elerium[0][0]
            elif not self.enemies and self.overall_points_with_elerium:
                nearest_point = self.overall_points_with_elerium[0][0]
        return nearest_point

    def _update_drones_targets(self):
        """
        Обновляет цели для всех живых дронов в команде
        :return: None
        """
        for drone in self.drone.my_team:
            if isinstance(drone.role, Harvester) and drone.is_alive:
                drone.target = drone.role.get_point()
                drone.move_at(drone.target)

    def __str__(self):
        return 'Harvester'


class Destructor(Role):
    """
    Атакующая роль дрона, целью атаки становятся дроны проивника, если дроны противника находятся от материнского
    корабля на дистанции, большей, чем дистанция, при которой восстанавливаются щиты. В противном случае, или в случае
    если на карте отсутствуют дроны противника, целью становятся материнские корабли.
    """
    def on_born(self):
        enemy = self.get_nearest_enemy()
        self._get_position_to_attack(enemy)

    @staticmethod
    def get_place_near(point, target, angle):
        """
        Расчет места рядом с point с отклонением angle от цели target
        :param point: исходная точка
        :param target: предполагаемая цель
        :param angle: угол отклонения
        :return: точка недалеко от цели
        """
        vec = Vector(point.x - target.x, point.y - target.y)
        vec.rotate(angle)
        return Point(target.x + vec.x, target.y + vec.y)

    def valid_place(self, point: Point):
        """
        Подходит ли это место для атаки. Слишком рядом не должно быть партнеров и на линии огня тоже не должно быть
        партнеров.
        :param point: анализируемое место
        :return: True or False
        """
        is_valid = 0 < point.x < theme.FIELD_WIDTH and 0 < point.y < theme.FIELD_HEIGHT
        for partner in self.drone.my_team:
            if not partner.is_alive or partner is self:
                continue
            is_valid = is_valid and (partner.distance_to(point) >= 50)
        return is_valid

    def _ally_on_fire(self, target):
        """
        Проверяет находится ли на линии огня дрон-союзник
        :param target: цель атаки
        :return: True or False
        """
        ally_nearby = False
        for ally in self.drone.my_team:
            if ally is self.drone and ally.is_alive:
                continue
            ally_nearby = ally_nearby or (isinstance(target, GameObject)
                                          and self.drone.distance_to(target) > ally.distance_to(target)
                                          and self.get_angle(ally, target) < 20
                                          and self.drone.distance_to(target) > self.drone.distance_to(ally)
                                          and ally.distance_to(target) > 10
                                          and self.drone.distance_to(ally) < 50)
        return ally_nearby

    def _get_point_nearby_enemy(self, target):
        """
        Находит и возвращает валидную точку, которую можно занять для атаки цели
        :param target: цель атаки
        :return: оптимальную(нет) точку рядом с врагом
        """
        if isinstance(target, GameObject):
            vec = Vector.from_points(target.coord, self.drone.coord)
        elif isinstance(target, Point):
            vec = Vector.from_points(target, self.drone.coord)
        else:
            raise Exception("target must be GameObject or Point!".format(target, ))
        dist = vec.module
        _koef = 1 / dist
        norm_vec = Vector(vec.x * _koef, vec.y * _koef)
        vec_gunshot = norm_vec * min(int(self.drone.attack_range), int(dist))
        purpose = Point(target.coord.x + vec_gunshot.x, target.coord.y + vec_gunshot.y)
        angles = [0, 60, -60, 40, -40, 20, -20]
        shuffle(angles)
        if self.drone.drone_number == 1:
            place = self.get_place_near(purpose, target, angles[self.drone.drone_number])
            return place
        for ang in angles:
            place = self.get_place_near(purpose, target, ang)
            if place and self.valid_place(place):
                return place
        return Point(theme.FIELD_WIDTH // 2, theme.FIELD_HEIGHT // 2)

    def _attack_or_retreat(self, enemy):
        """
        :param enemy: ближайший противник
        Дрон думает, что ему делать, стрелять, занять позицию для  стрельбы или отступить
        """
        if self.drone.meter_2 < self.drone.limit_health:
            self.drone.move_at(self.drone.my_mothership)
        else:
            if self.drone.distance_to(enemy) < self.drone.attack_range \
                    and self.drone.distance_to(self.drone.my_mothership) > 30 \
                    and not self._ally_on_fire(enemy):
                self.attack_the_target(enemy)
            else:
                self._get_position_to_attack(enemy)

    def _get_position_to_attack(self, enemy):
        self.drone.target = self._get_point_nearby_enemy(enemy)
        self.drone.move_at(self.drone.target)

    def on_stop_at_target(self, target):
        self.get_enemies()
        self.get_enemies_motherships()
        if self.enemies:
            self.get_overall_points_to_harvest()
            self.get_safe_points_to_harvest()
            if self.safe_points_with_elerium:
                self.change_the_role(Harvester, self.drone)
            allies_alive = [ally for ally in self.drone.my_team if ally.is_alive]
            if len(allies_alive) <= len(self.enemies) / (len(self.drone.scene.teams) - 1) \
                    and self.enemy_motherships:
                self.change_the_role(Turret, self.drone)
            else:
                nearest_enemy = self.get_nearest_enemy()
                self._attack_or_retreat(nearest_enemy)
        elif not self.enemies and self.enemy_motherships:
            nearest_enemy = self.enemy_motherships[0]
            self._attack_or_retreat(nearest_enemy)
        elif not self.enemies and not self.enemy_motherships:
            self.change_the_role(Harvester, self.drone)

    def on_stop(self):
        if self.drone.coord.x == self.drone.my_mothership.x and self.drone.coord.y == self.drone.my_mothership.y \
                and self.drone.cargo.payload > 0:
            self.drone.unload_to(self.drone.my_mothership)
        else:
            self.on_stop_at_target(target=None)

    def on_unload_complete(self):
        self.on_stop_at_target(target=None)

    def on_load_complete(self):
        self.on_stop_at_target(target=None)

    def on_stop_at_asteroid(self, asteroid):
        self.on_stop_at_target(target=asteroid)

    def __str__(self):
        return 'Destructor'


class Turret(Role):
    """
    Оборонная роль дрона, занимает исходную позицию рядом с материнским кораблем, следит за дронами противника.
    В случае приближения открывает по ним огонь
    """
    def on_born(self):
        target = self.get_position_near_mothership()
        if self.drone.coord.x == target.x and self.drone.coord.y == target.y:
            self.on_stop_at_target(target=None)
        else:
            self.drone.move_at(target)

    def on_stop_at_target(self, target):
        allies_alive = [ally for ally in self.drone.my_team if ally.is_alive]
        nearest_enemy = self.get_nearest_enemy()
        if nearest_enemy:
            if self.drone.distance_to(nearest_enemy) < self.drone.attack_range + 100:
                self.attack_the_target(nearest_enemy)
            else:
                self.get_overall_points_to_harvest()
                self.get_safe_points_to_harvest()
                if self.safe_points_with_elerium:
                    self.change_the_role(Harvester, self.drone)
                elif len(self.enemies) < len(allies_alive):
                    self.change_the_role(Destructor, self.drone)
                else:
                    self.drone.turn_to(nearest_enemy)

    def on_stop_at_asteroid(self, asteroid):
        self.on_stop_at_target(target=asteroid)

    def on_stop(self):
        self.on_stop_at_target(target=None)

    def on_unload_complete(self):
        self.on_born()

    def __str__(self):
        return 'Turret'
