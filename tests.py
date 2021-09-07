from unittest import TestCase
from unittest.mock import patch, Mock
from kovalev import Role, Harvester
from astrobox.core import Drone


class TestOne(TestCase):
    drone = Mock()
    drone.cargo = Mock()

    def test_getting_nearest_enemy_many_enemies(self):
        role = Role(self.drone)
        role.get_enemies = Mock()
        role.enemies = [[1, 151.294208024572], [2, 201.294208024572], [3, 251.294208024572],
                   [4, 351.294208024572], [5, 301.294208024572], [6, 451.294208024572],
                   [7, 551.294208024572], [8, 651.294208024572], [9, 751.294208024572]]
        target = role.get_nearest_enemy()
        assert target == 1

    def test_getting_nearest_enemy_one_enemy(self):
        enemy_drone = Mock()
        enemy_drone.distance_to = Mock(return_value=129)
        enemy_drone.my_mothership = Mock()
        enemy_drone.my_mothership.is_alive = True
        role = Role(self.drone)
        role.get_enemies = Mock()
        role.enemies = [[enemy_drone, 151.294208024572]]
        target = role.get_nearest_enemy()
        assert target == enemy_drone.my_mothership

    def test_getting_point_to_harvest_case1(self):
        role = Harvester(self.drone)
        role.get_enemies = Mock()
        role.get_enemies_motherships = Mock()
        role.drone.my_mothership = Mock(return_value='M')
        role.drone.my_mothership.payload = 400
        role.drone.limit_health = 4
        role.drone.meter_2 = 5
        role.get_safe_points_to_harvest = Mock()
        role.enemies = [[1, 151.294208024572], [2, 201.294208024572], [3, 251.294208024572],
                        [4, 351.294208024572], [5, 301.294208024572], [6, 451.294208024572],
                        [7, 551.294208024572], [8, 651.294208024572], [9, 751.294208024572],
                        [10, 751.294208024572], [11, 751.294208024572]]
        role.overall_points_with_elerium = [['a', 151.294208024572], ['b', 201.294208024572], ['c', 251.294208024572],
                                            ['d', 351.294208024572], ['e', 301.294208024572]]
        role.safe_points_with_elerium = [['x', 151.294208024572], ['y', 201.294208024572], ['z', 251.294208024572],
                                         ['u', 351.294208024572], ['w', 301.294208024572]]
        target = role._get_nearest_point_to_harvest()
        assert target == 'a'

    def test_getting_point_to_harvest_case2(self):
        role = Harvester(self.drone)
        role.get_enemies = Mock()
        role.get_enemies_motherships = Mock()
        role.drone.my_mothership = Mock(return_value='M')
        role.drone.my_mothership.payload = 400
        role.drone.limit_health = 5
        role.drone.meter_2 = 4
        role.get_safe_points_to_harvest = Mock()
        role.enemies = [[1, 151.294208024572], [2, 201.294208024572], [3, 251.294208024572],
                        [4, 351.294208024572], [5, 301.294208024572], [6, 451.294208024572],
                        [7, 551.294208024572], [8, 651.294208024572], [9, 751.294208024572],
                        [10, 751.294208024572], [11, 751.294208024572]]
        role.overall_points_with_elerium = [['a', 151.294208024572], ['b', 201.294208024572], ['c', 251.294208024572],
                                            ['d', 351.294208024572], ['e', 301.294208024572]]
        role.safe_points_with_elerium = [['x', 151.294208024572], ['y', 201.294208024572], ['z', 251.294208024572],
                                         ['u', 351.294208024572], ['w', 301.294208024572]]
        target = role._get_nearest_point_to_harvest()
        assert target == role.drone.my_mothership

    def test_getting_point_to_harvest_case3(self):
        role = Harvester(self.drone)
        role.get_enemies = Mock()
        role.get_enemies_motherships = Mock()
        role.drone.my_mothership = Mock(return_value='M')
        role.drone.my_mothership.payload = 600
        role.drone.limit_health = 4
        role.drone.meter_2 = 5
        role.get_safe_points_to_harvest = Mock()
        role.enemies = [[1, 151.294208024572], [2, 201.294208024572], [3, 251.294208024572],
                        [4, 351.294208024572], [5, 301.294208024572], [6, 451.294208024572],
                        [7, 551.294208024572], [8, 651.294208024572], [9, 751.294208024572],
                        [10, 751.294208024572], [11, 751.294208024572]]
        role.overall_points_with_elerium = [['a', 151.294208024572], ['b', 201.294208024572], ['c', 251.294208024572],
                                            ['d', 351.294208024572], ['e', 301.294208024572]]
        role.safe_points_with_elerium = [['x', 151.294208024572], ['y', 201.294208024572], ['z', 251.294208024572],
                                         ['u', 351.294208024572], ['w', 301.294208024572]]
        target = role._get_nearest_point_to_harvest()
        assert target == 'x'
