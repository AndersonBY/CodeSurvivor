# -*- coding: utf-8 -*-
# @Author: Anderson
# @Date:   2019-04-02 19:22:08
# @Last Modified by:   Anderson
# @Last Modified time: 2019-04-26 22:20:40

import pygame
import numpy as np
from func_timeout import func_set_timeout
import random
import os
import math
import importlib
import glob

WIDTH, HEIGHT = 30, 20
TILE_SIZE = 48
STATUS_BOARD_WIDTH = 6*TILE_SIZE
SHOW_LOGS_COUNT = 8
LOGS_FONT_SIZE = int(TILE_SIZE/2)
FPS = 60

# 包含有不同Agent文件的目录
AGENTS_FOLDER = '20190426-02'

# 每秒更新几次状态
TICK_RATE = 0.5

SHRINK_INTERVALS = [20, 20, 20, 10, 10, 10, 5, 5]

RED = (233, 114, 117)
GREEN = (11, 171, 118)
BLUE = (74, 217, 217)
WHITE = (255,255,255)
BLACK = (0, 0, 0)
YELLOW = (249, 194, 5)

tick_count = 0
winner = None
imgs = {}
game_logs = []
last_update_time = pygame.time.get_ticks()

class Player(pygame.sprite.Sprite):
	def __init__(self, agent):
		pygame.sprite.Sprite.__init__(self)
		self.image = imgs['avatars'][0]
		self.image.set_colorkey(BLACK)
		self.origin_image = self.image.copy()
		self.rect = self.image.get_rect()
		self.radius = TILE_SIZE//2
		self.rect.centerx = WIDTH/2
		self.rect.bottom = HEIGHT

		self.hp = 100
		self.hunger_value = 20
		self.thirst_value = 20

		self.agent = agent
		self.id = None
		self.x = None
		self.y = None
		self.vx = 0
		self.vy = 0
		self.to_x = -1
		self.to_y = -1

	def set_image(self, image):
		self.image = image
		self.image.set_colorkey(BLACK)
		self.origin_image = self.image.copy()

	def update_info(self):
		self.image = self.origin_image.copy()
		if self.hp<=0:
			return
		pos = (self.x, self.y)

		# 每个单位时间消耗一点食物和水分
		self.hunger_value -= 1
		if self.hunger_value<0:
			self.hunger_value = 0
		self.thirst_value -= 1
		if self.thirst_value<0:
			self.thirst_value = 0

		# 食物或水分将为0则每个单位时间消耗一点HP
		if self.hunger_value == 0:
			self.hp -= 1
		if self.thirst_value == 0:
			self.hp -= 1

		# 在水边每个单位时间补充5点水分
		if game_map.near_water(self.x, self.y):
			self.thirst_value += 5
			if self.thirst_value>100:
				self.thirst_value = 100

		# 在森林里每个单位时间补充5点食物
		if game_map.in_forest(self.x, self.y):
			self.hunger_value += 5
			if self.hunger_value>100:
				self.hunger_value = 100

		# 在水里每个单位时间减少1点HP
		if game_map.in_water(self.x, self.y):
			self.hp -= 1
			if self.hp<0:
				self.hp = 0

		# 在毒圈里每个单位时间减少2点HP
		if not game_map.in_safe_zone(self.x, self.y):
			self.hp -= 2
			if self.hp<0:
				self.hp = 0

		info_dict = {
			'pos': pos, 
			'ground_map': game_map.get_map('ground'),
			'safe_mask': game_map.get_map('safe_mask'),
			'next_safe_mask': game_map.get_map('next_safe_mask'),
			'next_safe_center': game_map.next_safe_center,
			'tick': tick_count,
			'count_down': game_map.shrink_countdown,
			'players_pos': players_pos.copy(), 
			'hp': self.hp,
			'hunger': self.hunger_value,
			'thirst': self.thirst_value
		}
		try:
			run_function_in_limited_time(self.agent.get_info, info_dict)
		except:
			print('{}函数出问题了'.format(self.agent.name))
		# self.agent.get_info(info_dict)

	def update(self):
		if abs(self.rect.x-self.x*TILE_SIZE)<5 and abs(self.rect.y-self.y*TILE_SIZE)<5:
			self.vx = self.vy = 0
			self.rect.x = self.x*TILE_SIZE
			self.rect.y = self.y*TILE_SIZE
		self.rect.x += self.vx
		self.rect.y += self.vy

	def move(self, to_x, to_y):
		dist = game_map.euclidean_dist(self.x, self.y, to_x, to_y)*TILE_SIZE
		if dist == 0:
			self.vx = 0
			self.vy = 0
		else:
			v = 5 * dist / (FPS/TICK_RATE)
			self.vx = v*(to_x-self.x)*TILE_SIZE/dist
			self.vy = v*(to_y-self.y)*TILE_SIZE/dist

			# 速度绝对值至少为1
			if 0<abs(self.vx)<1:
				self.vx = self.vx/abs(self.vx)
			if 0<abs(self.vy)<1:
				self.vy = self.vy/abs(self.vy)

			# 将速度绝对值处理为整数
			if abs(self.vx)>0:
				self.vx = self.vx/abs(self.vx)*abs(int(self.vx))
			if abs(self.vy)>0:
				self.vy = self.vy/abs(self.vy)*abs(int(self.vy))
			
		self.x = to_x
		self.y = to_y

	def set_pos(self, x, y):
		self.rect.x = x*TILE_SIZE
		self.rect.y = y*TILE_SIZE
		self.x = x
		self.y = y

class Bullet(pygame.sprite.Sprite):
	def __init__(self, x, y, to_x, to_y, shoot_success):
		pygame.sprite.Sprite.__init__(self)
		self.image = imgs['bullet']
		self.rect = self.image.get_rect()
		self.rect.centerx = x*TILE_SIZE + TILE_SIZE/2
		self.rect.centery = y*TILE_SIZE + TILE_SIZE/2
		self.destination = (to_x*TILE_SIZE + TILE_SIZE/2, to_y*TILE_SIZE + TILE_SIZE/2)
		self.vx = (to_x-x)/game_map.euclidean_dist(x, y, to_x, to_y)*TILE_SIZE
		self.vy = (to_y-y)/game_map.euclidean_dist(x, y, to_x, to_y)*TILE_SIZE
		self.shoot_success = shoot_success

	def update(self):
		if self.shoot_success and\
			abs(self.rect.centerx - self.destination[0])<TILE_SIZE/2 and\
			abs(self.rect.centery - self.destination[1])<TILE_SIZE/2:
			self.kill()

		if self.rect.centerx<0 or self.rect.centery<0 or\
			self.rect.centerx>WIDTH*TILE_SIZE or self.rect.centery>HEIGHT*TILE_SIZE:
			self.kill()
		
		self.rect.x += self.vx
		self.rect.y += self.vy

class GameMap(object):
	"""docstring for GameMap"""
	# 0：草地
	# 1：岩石
	# 2：树林
	# 3：水源
	def __init__(self):
		self.ground_map = None
		self.safe_mask = None
		self.deltas = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
		self.next_safe_center = None
		self.next_safe_mask = None
		self.last_shrink_time = 0
		self.shrink_time_intervals = SHRINK_INTERVALS
		self.shrink_countdown = self.shrink_time_intervals[0]
		self.next_safe_radius = WIDTH//2
		self.cur_safe_radius = 1.414*WIDTH
		self.shrink_done = False

	def init_map(self):
		self.ground_map = np.zeros((WIDTH, HEIGHT), dtype = int)

		for x in range(len(self.ground_map)):
			for y in range(len(self.ground_map[0])):
				current_type = self.ground_map[x][y]
				nearby_count = [0, 0, 0, 0]
				for delta in self.deltas:
					delta_x, delta_y = delta
					if self.reachable(x+delta_x, y+delta_y):
						nearby_count[self.ground_map[x+delta_x][y+delta_y]] += 1

				# 生成各种地形的初始概率
				prob_count = np.array([37, 10, 21, 16])
				# 对于每个点的地形，更倾向于生成和周围8个点一样类型的地形
				prob_count += np.array(nearby_count)*2

				ground_type_choice = []
				for index, value in enumerate(prob_count):
					ground_type_choice += [index for _ in range(value)]

				self.ground_map[x][y] = random.choice(ground_type_choice)
	
		self.safe_mask = np.ones((WIDTH, HEIGHT), dtype = int)
		self.next_safe_center = (random.randint(WIDTH//4, WIDTH*3//4), random.randint(HEIGHT//4, HEIGHT*3//4))

		# 设定当前安全圈半径为距离最远顶点的距离
		self.cur_safe_radius = max(
				self.euclidean_dist(self.next_safe_center[0], self.next_safe_center[1], 0, 0),
				self.euclidean_dist(self.next_safe_center[0], self.next_safe_center[1], WIDTH, 0),
				self.euclidean_dist(self.next_safe_center[0], self.next_safe_center[1], 0, HEIGHT),
				self.euclidean_dist(self.next_safe_center[0], self.next_safe_center[1], WIDTH, HEIGHT)
			)
		self.next_safe_mask = np.zeros((WIDTH, HEIGHT), dtype = int)
		for x in range(len(self.next_safe_mask)):
			for y in range(len(self.next_safe_mask[0])):
				dist = self.euclidean_dist(x, y, self.next_safe_center[0], self.next_safe_center[1])
				if dist<self.next_safe_radius:
					self.next_safe_mask[x][y] = 1
	
	def reachable(self, x, y):
		return x>=0 and x<WIDTH and y>=0 and y<HEIGHT

	def can_stand(self, x, y):
		return self.reachable(x, y) and self.ground_map[x][y] != 1

	def near_water(self, x, y):
		for delta in self.deltas:
			delta_x, delta_y = delta
			if self.reachable(x+delta_x, y+delta_y):
				if self.ground_map[x+delta_x][y+delta_y] == 3:
					return True
		return False

	def in_forest(self, x, y):
		return self.ground_map[x][y] == 2

	def in_water(self, x, y):
		return self.ground_map[x][y] == 3

	def in_safe_zone(self, x, y):
		return self.safe_mask[x][y] == 1

	def get_map(self, map_type):
		if map_type == 'ground':
			return self.ground_map.copy()
		elif map_type == 'safe_mask':
			return self.safe_mask.copy()
		elif map_type == 'next_safe_mask':
			return self.next_safe_mask.copy()

	def euclidean_dist(self, x1, y1, x2, y2):
		return math.sqrt((x1-x2)**2+(y1-y2)**2)

	def __generate_next_safe_circle(self):
		safe_count = self.next_safe_mask.sum()
		if safe_count <= 1:
			self.shrink_done = True
			self.safe_mask = np.zeros((WIDTH, HEIGHT), dtype = int)
			self.next_safe_mask = np.zeros((WIDTH, HEIGHT), dtype = int)
			return

		last_safe_center = self.next_safe_center
		# 找到在安全圈内的一个新的中心点
		lx, ly = last_safe_center
		self.next_safe_center = (
			random.randint(
				max(0, int(lx-self.next_safe_radius)), 
				min(WIDTH-1, int(lx+self.next_safe_radius))), 
			random.randint(
				max(0, int(ly-self.next_safe_radius)), 
				min(HEIGHT-1, int(ly+self.next_safe_radius))))

		nx, ny = self.next_safe_center
		while not self.next_safe_mask[nx][ny]:
			self.next_safe_center = (
				random.randint(
					max(0, int(lx-self.next_safe_radius)), 
					min(WIDTH-1, int(lx+self.next_safe_radius))), 
				random.randint(
					max(0, int(ly-self.next_safe_radius)), 
					min(HEIGHT-1, int(ly+self.next_safe_radius))))
			nx, ny = self.next_safe_center

		# 安全圈半径缩小为二分之一
		self.next_safe_radius /= 2

		# 以新安全圈中心为圆心重新调整半径
		self.cur_safe_radius += self.euclidean_dist(*last_safe_center, *self.next_safe_center)

		for x in range(len(self.next_safe_mask)):
			for y in range(len(self.next_safe_mask[0])):
				dist = self.euclidean_dist(x, y, *self.next_safe_center)
				if dist>self.next_safe_radius:
					self.next_safe_mask[x][y] = 0

	def __print_console_map(self, print_map):
		for x in range(len(print_map)):
			s = []
			for y in range(len(print_map[0])):
				if print_map[x][y]:
					s.append('o')
				else:
					s.append('X')
			print(' '.join(s))

	def update(self):
		if self.shrink_time_intervals and not self.shrink_done:
			if tick_count - self.last_shrink_time > self.shrink_time_intervals[0]:
				if self.cur_safe_radius>self.next_safe_radius:
					self.cur_safe_radius -= 0.5

				if self.cur_safe_radius<self.next_safe_radius:
					self.safe_mask = self.next_safe_mask.copy()
					self.__generate_next_safe_circle()
					self.last_shrink_time = tick_count
					self.shrink_time_intervals.pop(0)
				else:
					for x in range(len(self.ground_map)):
						for y in range(len(self.ground_map[0])):
							dist = self.euclidean_dist(x, y, *self.next_safe_center)
							if dist>self.cur_safe_radius:
								self.safe_mask[x][y] = 0
			else:
				self.shrink_countdown = self.shrink_time_intervals[0] - (tick_count - self.last_shrink_time)

def import_imgs():
	global imgs
	img_dir = os.path.join(os.path.dirname(__file__), 'img')
	grass_dir = os.path.join(img_dir, 'grass.png')
	imgs['grass'] = pygame.transform.scale(
		pygame.image.load(grass_dir).convert(),
		(TILE_SIZE, TILE_SIZE))
	water_dir = os.path.join(img_dir, 'water.png')
	imgs['water'] = pygame.transform.scale(
		pygame.image.load(water_dir).convert(),
		(TILE_SIZE, TILE_SIZE))
	forest_dir = os.path.join(img_dir, 'forest.png')
	imgs['forest'] = pygame.transform.scale(
		pygame.image.load(forest_dir).convert(),
		(TILE_SIZE, TILE_SIZE))
	stone_dir = os.path.join(img_dir, 'stone.png')
	imgs['stone'] = pygame.transform.scale(
		pygame.image.load(stone_dir).convert(),
		(TILE_SIZE, TILE_SIZE))
	dark_stone_dir = os.path.join(img_dir, 'dark_stone.png')
	imgs['dark_stone'] = pygame.transform.scale(
		pygame.image.load(dark_stone_dir).convert(),
		(TILE_SIZE, TILE_SIZE))
	bullet_dir = os.path.join(img_dir, 'bullet.png')
	imgs['bullet'] = pygame.transform.scale(
		pygame.image.load(bullet_dir).convert_alpha(),
		(TILE_SIZE//6, TILE_SIZE//6))

	avatar_dir = os.path.join(img_dir, 'avatars')
	imgs['avatars'] = []
	for avatar_path in os.listdir(avatar_dir):
		avatar_path = os.path.join(avatar_dir, avatar_path)
		imgs['avatars'].append(
			pygame.transform.scale(
				pygame.image.load(avatar_path).convert(),
				(TILE_SIZE, TILE_SIZE)))

def init_players_pos(game_map):
	players_pos = []
	for player in players:
		x = random.randint(1, WIDTH-2)
		y = random.randint(1, HEIGHT-2)
		while game_map[x][y] == 1 or game_map[x][y] == 3 or (x,y) in players_pos:
			x = random.randint(1, WIDTH-2)
			y = random.randint(1, HEIGHT-2)
		players_pos.append((x, y))
		player.set_pos(x, y)

	return players_pos

def draw_text(text, surface, color, font_size, x, y, align='center'):
	font = pygame.font.Font('./font/zhankukuaile.ttf', font_size)
	text_surface = font.render(text, True, color)
	text_rect = text_surface.get_rect()
	if align=='center':
		text_rect.midtop = (x, y)
	elif align=='left':
		text_rect.left = x
		text_rect.top = y
	elif align=='right':
		text_rect.right = x
		text_rect.top = y
	surface.blit(text_surface, text_rect)

def draw_map():
	global screen
	g_map = game_map.get_map('ground')
	for x in range(len(g_map)):
		for y in range(len(g_map[0])):
			if g_map[x][y]==0:
				screen.blit(imgs['grass'], (x*TILE_SIZE, y*TILE_SIZE))
			elif g_map[x][y]==1:
				screen.blit(imgs['stone'], (x*TILE_SIZE, y*TILE_SIZE))
			elif g_map[x][y]==2:
				screen.blit(imgs['grass'], (x*TILE_SIZE, y*TILE_SIZE))
				screen.blit(imgs['forest'], (x*TILE_SIZE, y*TILE_SIZE))
			elif g_map[x][y]==3:
				screen.blit(imgs['water'], (x*TILE_SIZE, y*TILE_SIZE))
			
			if not game_map.safe_mask[x][y]:
				overlay = pygame.Surface((TILE_SIZE,TILE_SIZE))
				overlay.set_alpha(50)
				overlay.fill((0,0,0))
				screen.blit(overlay, (x*TILE_SIZE, y*TILE_SIZE))

			if game_map.next_safe_mask[x][y]:
				overlay = pygame.Surface((TILE_SIZE,TILE_SIZE))
				overlay.set_alpha(100)
				overlay.fill(BLUE)
				screen.blit(overlay, (x*TILE_SIZE, y*TILE_SIZE))

def draw_status_board():
	global screen
	for x in range(WIDTH, WIDTH+6):
		for y in range(HEIGHT):
			screen.blit(imgs['dark_stone'], (x*TILE_SIZE, y*TILE_SIZE))

	x = (WIDTH+1)*TILE_SIZE
	dh = 2*HEIGHT*TILE_SIZE/(3*len(players)+1)
	y = dh/2
	for index, player in enumerate(players):
		screen.blit(player.origin_image, (x, y))
		draw_text(player.agent.name, screen, WHITE, int(TILE_SIZE/2), x+TILE_SIZE+5, y+TILE_SIZE/4, 'left')
		pygame.draw.rect(screen, RED, (x, y+TILE_SIZE+5, TILE_SIZE*4*player.hp/100, 5))
		pygame.draw.rect(screen, BLUE, (x, y+TILE_SIZE+13, TILE_SIZE*4*player.hunger_value/100, 5))
		pygame.draw.rect(screen, GREEN, (x, y+TILE_SIZE+21, TILE_SIZE*4*player.thirst_value/100, 5))
		y += 1.5*dh

def draw_game_logs():
	global screen

	x = WIDTH*TILE_SIZE
	y = 10
	for index, game_log in enumerate(game_logs[-SHOW_LOGS_COUNT:]):
		draw_text(game_log, screen, WHITE, LOGS_FONT_SIZE, x, y, 'right')
		y += LOGS_FONT_SIZE + 5

# 限制玩家函数运行时间，超时则报错
@func_set_timeout(0.5)
def run_function_in_limited_time(f, *args):
	result = f(*args)
	return result


pygame.init()
screen = pygame.display.set_mode((WIDTH*TILE_SIZE+STATUS_BOARD_WIDTH, HEIGHT*TILE_SIZE))
pygame.display.set_caption("Code Survivor")
clock = pygame.time.Clock()

import_imgs()

players = pygame.sprite.Group()
bullets = pygame.sprite.Group()

# 从包含有Agent的目录下将所有Agent文件中的Agent类批量import进来
# 此处暂未做任何安全性检查，请自行辨别文件内容是否安全！
for file_path in glob.glob('{}/*.py'.format(AGENTS_FOLDER)):
	if os.path.isfile(file_path):
		module_spec = importlib.util.spec_from_file_location('Agent', file_path)
		module = importlib.util.module_from_spec(module_spec)
		module_spec.loader.exec_module(module)
		player = Player(module.Agent())
		players.add(player)

# 如果想采用普通import方法导入Agent则用下面方法
# from DemoAgent import Agent
# player = Player(Agent())
# players.add(player)

for index, player in enumerate(players):
	player.id = index
	avatar = imgs['avatars'].pop(random.randint(0, len(imgs['avatars'])-1))
	player.set_image(avatar)

game_map = GameMap()
game_map.init_map()

players_pos = init_players_pos(game_map.get_map('ground'))
players.update()
print(players_pos)

game_continue = False
game_over = False
while not game_continue:
	clock.tick(FPS)
	event_list = pygame.event.get()
	for event in event_list:
		if event.type == pygame.QUIT:
			game_over = True
			game_continue = True
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_SPACE:
				game_continue = True

	draw_map()
	players.draw(screen)
	for index, player in enumerate(players):
		name = player.agent.name
		x, y = player.x, player.y
		draw_text(name, screen, WHITE, 40, x*TILE_SIZE+TILE_SIZE/2, (y+1)*TILE_SIZE)
	
	draw_status_board()
	
	pygame.display.flip()

while not game_over:
	clock.tick(FPS)
	event_list = pygame.event.get()
	for event in event_list:
		if event.type == pygame.QUIT:
			game_over = True

	now = pygame.time.get_ticks()
	if now - last_update_time > 1000/TICK_RATE and winner is None:
		for player in players:
			player.update_info()
		for index, player in enumerate(players):
			if player.hp > 0:
				try:
					action_type, action_value = run_function_in_limited_time(player.agent.take_action)
					if action_type == 'move':
						x, y = action_value
						if abs(x-player.x)<=1 and abs(y-player.y)<=1 and\
							game_map.can_stand(x, y):
								player.move(x, y)
								players_pos[index] = action_value
								game_logs.append('{}移动到了{}'.format(player.agent.name, (x,y)))
					elif action_type == 'shoot':
						x, y = action_value

						shoot_success_prob = 1 - game_map.euclidean_dist(x, y, player.x, player.y)/(WIDTH/2)
						if shoot_success_prob<0:
							shoot_success_prob = 0
						if random.random()<shoot_success_prob:
							shoot_success = True
						else:
							shoot_success = False

						bullet = Bullet(player.x, player.y, x, y, shoot_success)
						bullets.add(bullet)

						if shoot_success:
							for victim in players:
								if (x, y) == (victim.x, victim.y) and victim != player:
									game_logs.append('{0}击中{1}！{1}的HP-{2}!'.format(
										player.agent.name, victim.agent.name, int(shoot_success_prob*10)+1))
									# print('{0}击中{1}！{1}的HP-{2}!'.format(
									# 	player.agent.name, victim.agent.name, int(shoot_success_prob*10)+1))
									victim.hp -= int(shoot_success_prob*10)+1
									if victim.hp<0:
										victim.hp = 0
									break
						else:
							game_logs.append('{}开枪未中！'.format(player.agent.name))
							# print('{} miss the shot!'.format(player.agent.name))
				except:
					game_logs.append('{}函数出问题了'.format(player.agent.name))
					print('{}函数出问题了'.format(player.agent.name))

		game_map.update()
		last_update_time = now
		tick_count += 1

	players.update()
	bullets.update()

	draw_map()
	alive_players = []
	for index, player in enumerate(players):
		if player.hp > 0:
			alive_players.append(player)
			screen.blit(player.image, player.rect)
			pygame.draw.rect(player.image, RED, (0, 0, player.rect.w*player.hp/100, 3))
			pygame.draw.rect(player.image, BLUE, (0, 4, player.rect.w*player.hunger_value/100, 3))
			pygame.draw.rect(player.image, GREEN, (0, 8, player.rect.w*player.thirst_value/100, 3))
			name = player.agent.name
			draw_text(name, screen, WHITE, 40, player.rect.x+TILE_SIZE/2, player.rect.y+TILE_SIZE)
		else:
			players_pos[index] = (-1, -1)

	if len(alive_players) == 1:
		winner = alive_players[0]

	bullets.draw(screen)
	draw_status_board()
	draw_game_logs()

	if winner is not None:
		draw_text(
			winner.agent.name,
			screen, YELLOW, 80, WIDTH*TILE_SIZE/2, HEIGHT*TILE_SIZE/2-100)
		draw_text(
			'WINNER WINNER'.format(game_map.shrink_countdown),
			screen, YELLOW, 80, WIDTH*TILE_SIZE/2, HEIGHT*TILE_SIZE/2)
		draw_text(
			'CHICKEN DINNER!'.format(game_map.shrink_countdown),
			screen, YELLOW, 80, WIDTH*TILE_SIZE/2, HEIGHT*TILE_SIZE/2+85)

	if game_map.shrink_countdown>0:
		draw_text(
			'缩圈倒计时：{}'.format(game_map.shrink_countdown),
			screen, WHITE, 40, WIDTH*TILE_SIZE/2, 10)

	pygame.display.flip()
