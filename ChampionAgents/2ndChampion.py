import math


class Game(object):
    WIDTH, HEIGHT = 30, 20
    HALF_WIDTH = WIDTH / 2
    PATH_WALKABLE = 0
    PATH_BLOCK = 1
    PATH_FOREST = 2
    PATH_WATER = 3
    ALL_DELTAS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    ALL_STEPS = [
        (0, 0),
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
        (-1, 0),
        (0, -1),
        (0, 1),
        (1, 0),
    ]
    ALL_NEXT_STEPS = [
        [(0, 0)],
        [(0, 0), (-1, -1), (-1, 0), (0, -1), (-1, 1), (1, -1)],
        [(0, 0), (-1, 1), (-1, 0), (0, 1), (1, -1), (-1, -1)],
        [(0, 0), (1, -1), (1, 0), (0, -1), (1, 1), (-1, 1)],
        [(0, 0), (1, 1), (1, 0), (0, 1), (-1, -1), (1, 1)],
        [(0, 0), (-1, 0), (-1, -1), (-1, 1)],
        [(0, 0), (0, -1), (1, -1), (-1, -1)],
        [(0, 0), (0, 1), (-1, 1), (1, 1)],
        [(0, 0), (1, 0), (1, -1), (1, 1)],
    ]
    ALL_NEXT_STEPS_INDEX = [
        [0],
        [0, 1, 5, 6, 2, 3],
        [0, 2, 5, 7, 3, 1],
        [0, 3, 8, 6, 4, 2],
        [0, 4, 8, 7, 1, 4],
        [0, 5, 1, 2],
        [0, 6, 3, 1],
        [0, 7, 2, 4],
        [0, 8, 3, 4],
    ]
    DEPTH_ROUTE_LIST_SIZE = []

    @staticmethod
    def init_route_list_size(depth):
        route_list = range(0, 9)
        Game.DEPTH_ROUTE_LIST_SIZE.append(9)
        for i in range(1, depth):
            next_route_list = []
            for route in route_list:
                for step in Game.ALL_NEXT_STEPS_INDEX[route]:
                    next_route_list.append(step)
            route_list = next_route_list
            Game.DEPTH_ROUTE_LIST_SIZE.append(len(route_list))

    agent = None
    players_count = 4
    alive_players_count = 4
    current_circle_size = None
    next_circle_center = None
    next_circle_size = None
    circle_shrink_speed = 0.5
    is_circle_updated = True
    is_shrinking = False
    best_route = None
    best_cost = 99999
    depth = 0
    max_depth = 4
    previous_action_success = True

    @staticmethod
    def get_distance_euc(pos1, pos2):
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    @staticmethod
    def get_closest_enemy(player_id):
        min_distance = 99999
        closest_enemy_id = -1
        for i in range(0, Game.players_count):
            if i == player_id:
                continue
            if Game.agent.players_pos[i][0] == -1:
                continue
            distance = Game.get_distance_euc(
                Game.agent.players_pos[player_id], Game.agent.players_pos[i]
            )
            if distance < min_distance:
                min_distance = distance
                closest_enemy_id = i
        return closest_enemy_id, min_distance

    @staticmethod
    def get_damage_predict(distance):
        shoot_success_prob = 1 - distance / Game.HALF_WIDTH
        if shoot_success_prob <= 0:
            return 0
        return shoot_success_prob * (int(shoot_success_prob * 10) + 1)

    @staticmethod
    def pos_add(pos1, pos2):
        return (pos1[0] + pos2[0], pos1[1] + pos2[1])

    @staticmethod
    def get_pos_path_type(pos):
        return Game.agent.ground_map[pos[0]][pos[1]]

    @staticmethod
    def is_pos_in_map(pos):
        return (
            pos[0] >= 0 and pos[0] < Game.WIDTH and pos[1] >= 0 and pos[1] < Game.HEIGHT
        )

    @staticmethod
    def is_pos_near_water(pos):
        new_pos = None
        for delta in Game.ALL_DELTAS:
            new_pos = Game.pos_add(pos, delta)
            if Game.is_pos_in_map(new_pos):
                if Game.get_pos_path_type(new_pos) == Game.PATH_WATER:
                    return True
        return False

    @staticmethod
    def is_pos_in_safe_zone(pos):
        return Game.agent.safe_mask[pos[0]][pos[1]] == 1

    @staticmethod
    def is_pos_in_next_safe_zone(pos):
        return Game.agent.next_safe_mask[pos[0]][pos[1]] == 1

    @staticmethod
    def get_next_status(pos, hp_cost, food, water, count_down, circle_size):
        if Game.alive_players_count > 2:
            pos_backup = Game.agent.players_pos[Game.agent.id]
            Game.agent.players_pos[Game.agent.id] = pos
            for i in range(0, Game.players_count):
                if Game.agent.id == i:
                    continue
                closest_enemy_id, distance = Game.get_closest_enemy(i)
                if closest_enemy_id == Game.agent.id:
                    hp_cost += Game.get_damage_predict(distance)
            Game.agent.players_pos[Game.agent.id] = pos_backup
        path_type = Game.get_pos_path_type(pos)
        if food <= 1:
            hp_cost += 1
        if water <= 1:
            hp_cost += 1
        if Game.is_pos_near_water(pos):
            water += 5
        elif water > 0:
            water -= 1
        if path_type == Game.PATH_FOREST:
            food += 5
        else:
            if food > 0:
                food -= 1
            if path_type == Game.PATH_WATER:
                hp_cost += 1
        if count_down > 0:
            count_down -= 1
        else:
            circle_size -= Game.circle_shrink_speed
        if not Game.is_pos_in_safe_zone(pos):
            distance_to_safe_area = (
                Game.get_distance_euc(pos, Game.next_circle_center)
                - Game.next_circle_size
            )
            if distance_to_safe_area < 0:
                distance_to_safe_area = 0
            hp_cost += (distance_to_safe_area + 1) * 4
        elif not Game.is_pos_in_next_safe_zone(pos) and (
            Game.get_distance_euc(pos, Game.next_circle_center)
            >= circle_size - Game.circle_shrink_speed
        ):
            distance_to_safe_area = (
                Game.get_distance_euc(pos, Game.next_circle_center)
                - Game.next_circle_size
            )
            if distance_to_safe_area < 0:
                distance_to_safe_area = 0
            hp_cost += (distance_to_safe_area + 1) * 4
        return hp_cost, food, water, count_down, circle_size

    @staticmethod
    def game_init():
        Game.next_circle_size = Game.WIDTH // 2
        Game.next_circle_center = Game.agent.next_safe_center
        Game.current_circle_size = max(
            Game.get_distance_euc(Game.next_circle_center, (0, 0)),
            Game.get_distance_euc(Game.next_circle_center, (Game.WIDTH, 0)),
            Game.get_distance_euc(Game.next_circle_center, (0, Game.HEIGHT)),
            Game.get_distance_euc(Game.next_circle_center, (Game.WIDTH, Game.HEIGHT)),
        )

    @staticmethod
    def get_route():
        Game.best_route = None
        Game.best_cost = 99999
        pos = Game.agent.pos
        hp_cost = 0
        food = Game.agent.hunger
        water = Game.agent.thirst
        count_down = Game.agent.count_down
        circle_size = Game.current_circle_size
        route_list = [None] * Game.DEPTH_ROUTE_LIST_SIZE[0]
        route_list_index = 0
        next_route_list = None
        next_route_list_index = 0
        Game.depth = 1
        for i in range(0, 9):
            step = Game.ALL_STEPS[i]
            new_pos = Game.pos_add(pos, step)
            if not Game.is_pos_in_map(new_pos):
                continue
            if Game.get_pos_path_type(new_pos) == Game.PATH_BLOCK:
                continue
            new_hp_cost, new_food, new_water, new_count_down, new_circle_size = Game.get_next_status(
                new_pos, hp_cost, food, water, count_down, circle_size
            )
            if Game.alive_players_count <= 2:
                if step != (0, 0):
                    new_hp_cost += Game.get_damage_predict(
                        Game.get_distance_euc(
                            new_pos, Game.get_closest_enemy(Game.agent.id)
                        )
                    )
            if new_hp_cost + 0.01 < Game.best_cost:
                Game.best_cost = new_hp_cost
                Game.best_route = new_pos
            route_list[route_list_index] = Route(
                new_pos,
                new_pos,
                i,
                new_hp_cost,
                new_food,
                new_water,
                new_count_down,
                new_circle_size,
            )
            route_list_index += 1
        if len(route_list) == 0:
            return
        while Game.depth < Game.max_depth:
            stage_best_route = None
            stage_best_cost = 99999
            next_route_list = [None] * Game.DEPTH_ROUTE_LIST_SIZE[Game.depth]
            next_route_list_index = 0
            for route in route_list:
                if route == None:
                    continue
                for i in range(0, len(Game.ALL_NEXT_STEPS[route.last_step_index])):
                    step = Game.ALL_NEXT_STEPS[route.last_step_index][i]
                    new_pos = Game.pos_add(route.pos, step)
                    if not Game.is_pos_in_map(new_pos):
                        continue
                    if Game.get_pos_path_type(new_pos) == Game.PATH_BLOCK:
                        continue
                    new_hp_cost, new_food, new_water, new_count_down, new_circle_size = Game.get_next_status(
                        new_pos,
                        route.hp_cost,
                        route.food,
                        route.water,
                        route.count_down,
                        route.circle_size,
                    )
                    if Game.alive_players_count <= 2:
                        if step != (0, 0):
                            new_hp_cost += Game.get_damage_predict(
                                Game.get_distance_euc(
                                    new_pos, Game.get_closest_enemy(Game.agent.id)
                                )
                            )
                    if new_hp_cost + 0.01 < stage_best_cost:
                        stage_best_cost = new_hp_cost
                        stage_best_route = route.first_step
                    next_route_list[next_route_list_index] = Route(
                        new_pos,
                        route.first_step,
                        Game.ALL_NEXT_STEPS_INDEX[route.last_step_index][i],
                        new_hp_cost,
                        new_food,
                        new_water,
                        new_count_down,
                        new_circle_size,
                    )
                    next_route_list_index += 1
            Game.best_route = stage_best_route
            Game.best_cost = stage_best_cost
            Game.depth += 1
            route_list = next_route_list


class Route(object):
    def __init__(
        self,
        pos,
        first_step,
        last_step_index,
        hp_cost,
        food,
        water,
        count_down,
        circle_size,
    ):
        self.pos = pos
        self.first_step = first_step
        self.last_step_index = last_step_index
        self.hp_cost = hp_cost
        self.food = food
        self.water = water
        self.count_down = count_down
        self.circle_size = circle_size


class Agent(object):
    def __init__(self):
        # 给你的玩家起个名字
        self.name = "Myaw OwO"
        self.id = -1
        self.first_round = True
        Game.init_route_list_size(6)

    def get_info(self, info_dict):
        self.pos = info_dict["pos"]
        self.ground_map = info_dict["ground_map"]
        self.safe_mask = info_dict["safe_mask"]
        self.next_safe_mask = info_dict["next_safe_mask"]
        self.next_safe_center = info_dict["next_safe_center"]
        self.tick = info_dict["tick"]
        self.count_down = info_dict["count_down"]
        self.players_pos = info_dict["players_pos"]
        self.hp = info_dict["hp"]
        self.hunger = info_dict["hunger"]
        self.thirst = info_dict["thirst"]

    def take_action(self):
        Game.agent = self
        Game.players_count = len(self.players_pos)
        Game.alive_players_count = 0
        for i in range(0, Game.players_count):
            if self.players_pos[i][0] == -1:
                continue
            Game.alive_players_count += 1
            if self.id == -1 and self.players_pos[i] == self.pos:
                self.id = i
                break
        if self.first_round:
            self.first_round = False
            Game.game_init()
        if Game.agent.count_down == 0:
            Game.is_shrinking = True
            if Game.current_circle_size > Game.next_circle_size:
                Game.current_circle_size -= Game.circle_shrink_speed
        elif Game.is_shrinking:
            Game.is_shrinking = False
            last_circle_center = Game.next_circle_center
            Game.next_circle_center = self.next_safe_center
            Game.next_circle_size /= 2
            Game.current_circle_size += Game.get_distance_euc(
                last_circle_center, Game.next_circle_center
            )
        Game.get_route()
        if Game.best_route == None or Game.best_route == self.pos:
            closest_enemy_id, distance = Game.get_closest_enemy(self.id)
            if closest_enemy_id != -1:
                return ("shoot", self.players_pos[closest_enemy_id])
        else:
            return ("move", Game.best_route)

