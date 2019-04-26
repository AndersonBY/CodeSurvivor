# -*- coding: utf-8 -*-
# @Author: Anderson
# @Date:   2019-04-02 19:22:08
# @Last Modified by:   Anderson
# @Last Modified time: 2019-04-17 11:36:36
#import pygame
import numpy as np
from func_timeout import func_set_timeout
import random
import os
import math
import importlib
import glob
import math
# 注意事项
# 每个单位时间消耗一点食物和水分，即饥饿值和口渴值都减一
# 饥饿值或口渴值将为0时每个单位时间消耗一点HP
# 在水边每个单位时间增加5点口渴值
# 在森林里每个单位时间增加5点饥饿值
# 在水里每个单位时间减少1点HP
# 在毒圈里每个单位时间减少2点HP
# 玩家初始HP为100，初始饥饿值和口渴值都为20

# 系统通过调用get_info()函数来给你更新当前场上信息
# get_info()函数的输入参数info_dict为一个字典
# pos: 一个元组储存你当前的位置(x, y)
# ground_map: 一个numpy数组储存地形。0：草地，1：岩石，2：树林，3：水源
# safe_mask: 当前安全的区域，有毒区域标记为0，无毒区域标记为1
# next_safe_mask: 下一次缩圈后的安全区域，有毒区域标记为0，无毒区域标记为1
# next_safe_center: 下一个安全圈中心点坐标
# tick: 游戏开始以来的tick数
# count_down: 还有几次tick后就开始缩圈，当tick为0时表示正在缩圈
# players_pos: 一个列表储存所有玩家的位置，形如[(1,2), (3,4), (5,6)]。每个玩家在列表中的编号位置不变
# hp: 玩家当前血量
# hunger: 玩家当前饥饿值，100为最不饥饿
# thirst: 玩家当前口渴值，100位最不口渴

# 系统通过调用tack_action()函数来获取你要采取的行动
# 目前支持两种行动：移动，射击
# 返回格式为('move', (x, y))或('shoot', (x, y))
# 仅可移动到自己周围八个格子内
# 射击距离超过一半地图宽度时100% miss
# 射击和自己在同一个格子里的玩家时100%射中
# 射击距离在上述两种情况的中间则按照概率计算是否射中（线性），越近则射中的概率越高
# 越近距离射中敌人则扣的HP越多，一次射击最多扣10HP，最少扣1HP

# Agent这个Class名字不要改
class Point(object):
	def __init__(self, x, y):
		self.x = x
		self.y = y

	def __str__(self):
		return '({} {})'.format(self.x, self.y)


class Map(object):
	def __init__(self, n, m, default=None, map=None):
		self.m = m
		self.n = n
		if map is None:
			self.__map = [[default for _ in range(m)] for _ in range(n)]
		else:
			self.__map = map

	def get(self, x, y):
		return self.__map[y][x]

	def set(self, x, y, v):
		self.__map[y][x] = v

	def __str__(self):
		s = ''
		for line in self.__map:
			line = [str(i) for i in line]
			s += ' '.join(line) + '\n'
		return s


class BreadFirstPathsA(object):
	def __init__(self, m, s, t):
		self.map = m
		self.s = s
		self.t = t
		self.from_v = Map(self.map.n, self.map.m, None)
		self.min_mps = Map(self.map.n, self.map.m, None)
		self.bfs(s, t)

	def bfs(self, s, t):
		self.fringe = []
		self.fringe.append(s)
		self.min_mps.set(s.x, s.y, 0)
		while self.fringe:
			# print([str(i) for i in self.fringe])
			v = self.fringe.pop(0)
			if v.x == t.x and v.y == t.y:
				break
			if v.x > 0:
				w = Point(v.x - 1, v.y)
				self.try_goto(w, v)
			if v.x < self.map.m -1 :
				w = Point(v.x + 1, v.y)
				self.try_goto(w, v)
			if v.y > 0:
				w = Point(v.x, v.y - 1)
				self.try_goto(w, v)
			if v.y < self.map.n -1:
				w = Point(v.x, v.y + 1)
				self.try_goto(w, v)
			if v.x > 0 and v.y > 0 :
				w = Point(v.x - 1,v.y - 1)
				self.try_goto(w,v)
			if v.x < self.map.m -1 and v.y < self.map.n -1 :
				w = Point(v.x + 1,v.y + 1)
				self.try_goto(w,v)
			if v.x > 0 and v.y < self.map.n -1:
				w = Point(v.x - 1,v.y + 1)
				self.try_goto(w,v)
			if v.x < self.map.m -1 and v.y > 0:
				w = Point(v.x + 1,v.y - 1)
				self.try_goto(w,v)

	def try_goto(self, w, v):
		# try_goto(w, v): 尝试从节点v到节点w

		# 如果要去的w点是墙则直接返回
		if self.map.get(w.x, w.y) == 1 or self.map.get(w.x, w.y) == 3:
			return

		# 如果我们是从w到v节点的那么没必要走回头路了
		v_from = self.from_v.get(v.x, v.y)
		if v_from is not None:
			if v_from.x == w.x and v_from.y == w.y:
				return

		mp = self.min_mps.get(v.x, v.y) + 1

		if self.min_mps.get(w.x, w.y) is not None:
			# 如果之前走过w点且当前这条路的体力消耗更少则更新数据
			if mp < self.min_mps.get(w.x, w.y):
				self.fringe.append(w)
				self.from_v.set(w.x, w.y, v)
				self.min_mps.set(w.x, w.y, mp)
		else:
			self.fringe.append(w)
			self.from_v.set(w.x, w.y, v)
			self.min_mps.set(w.x, w.y, mp)

	def count_mp(self):
		return self.min_mps.get(self.t.x, self.t.y)

	def find_path(self):
		path = []
		mid_x = self.t.x 
		mid_y = self.t.y
		path.append([mid_x,mid_y])
		while True:
			mid = self.from_v.get(mid_x,mid_y)
			if mid.x == self.s.x and mid.y == self.s.y:
				break
			path.append([mid.x,mid.y])
			mid_x = mid.x
			mid_y = mid.y
		return path

class BreadFirstPathsB(object):
	def __init__(self, m, s,t):
		self.map = m
		self.s = s
		self.t = t
		self.d = None
		self.deltas = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
		self.from_v = Map(self.map.n, self.map.m, None)
		self.min_mps = Map(self.map.n, self.map.m, None)
		self.bfs(s)

	def bfs(self, s):
		self.fringe = []
		self.fringe.append(s)
		self.min_mps.set(s.x, s.y, 0)
		while self.fringe:
			# print([str(i) for i in self.fringe])
			v = self.fringe.pop(0)
			if self.t == 'find_forest':
				if self.map.get(v.x,v.y) == 2:
					self.d = v
					break
			elif self.t == 'find_near_water':
				if self.near_water(v):
					self.d = v
					break
			else:
				if self.map.get(v.x,v.y) != 1 and self.map.get(v.x,v.y) != 3:
					self.d = v 
					break
			if v.x > 0:
				w = Point(v.x - 1, v.y)
				self.try_goto(w, v)
			if v.x < self.map.m -1 :
				w = Point(v.x + 1, v.y)
				self.try_goto(w, v)
			if v.y > 0:
				w = Point(v.x, v.y - 1)
				self.try_goto(w, v)
			if v.y < self.map.n -1:
				w = Point(v.x, v.y + 1)
				self.try_goto(w, v)
			if v.x > 0 and v.y > 0 :
				w = Point(v.x - 1,v.y - 1)
				self.try_goto(w,v)
			if v.x < self.map.m -1 and v.y < self.map.n -1 :
				w = Point(v.x + 1,v.y + 1)
				self.try_goto(w,v)
			if v.x > 0 and v.y < self.map.n -1:
				w = Point(v.x - 1,v.y + 1)
				self.try_goto(w,v)
			if v.x < self.map.m -1 and v.y > 0:
				w = Point(v.x + 1,v.y - 1)
				self.try_goto(w,v)

	def try_goto(self, w, v):
		# try_goto(w, v): 尝试从节点v到节点w

		# 如果要去的w点是墙则直接返回
		if self.map.get(w.x, w.y) == 1 or self.map.get(w.x, w.y) == 3:
			return

		# 如果我们是从w到v节点的那么没必要走回头路了
		v_from = self.from_v.get(v.x, v.y)
		if v_from is not None:
			if v_from.x == w.x and v_from.y == w.y:
				return

		mp = self.min_mps.get(v.x, v.y) + 1

		if self.min_mps.get(w.x, w.y) is not None:
			# 如果之前走过w点且当前这条路的体力消耗更少则更新数据
			if mp < self.min_mps.get(w.x, w.y):
				self.fringe.append(w)
				self.from_v.set(w.x, w.y, v)
				self.min_mps.set(w.x, w.y, mp)
		else:
			self.fringe.append(w)
			self.from_v.set(w.x, w.y, v)
			self.min_mps.set(w.x, w.y, mp)

	def count_mp(self):
		return self.min_mps.get(self.t.x, self.t.y)

	def get_d(self):
		return self.d

	def near_water(self,v):
		for delta in self.deltas:
			delta_x, delta_y = delta
			new_x = v.x+delta_x
			new_y = v.y+delta_y
			if new_x >=  0 and new_x < self.map.m and new_y >= 0 and new_y < self.map.n:
				if self.map.get(new_x,new_y) ==3:
					return True
		return False

class Agent(object):
	"""docstring for Agent"""
	def __init__(self):
		# 给你的玩家起个名字
		self.name = '55open'
		

	def get_info(self, info_dict):
		self.pos = info_dict['pos']
		self.ground_map = info_dict['ground_map']
		self.safe_mask = info_dict['safe_mask']
		self.next_safe_mask = info_dict['next_safe_mask']
		self.next_safe_center = info_dict['next_safe_center']
		self.tick = info_dict['tick']
		self.count_down = info_dict['count_down']
		self.players_pos = info_dict['players_pos']
		self.hp = info_dict['hp']
		self.hunger = info_dict['hunger']
		self.thirst = info_dict['thirst']

	def find_the_nearest(self,i_pos,players_pos):
		min_dis = 10000
		min_list = []
		for player in players_pos:
			if player != (-1,-1):
				dis = pow((i_pos[0] - player[0]),2) + pow((i_pos[1] - player[1]),2)
				if dis < min_dis and dis != 0:
					min_dis = dis 
					min_list.append(player)
		return min_list.pop()

	def take_action(self):
		i = 0
		while i < len(self.players_pos):
			victim_pos = self.players_pos[i]
			if victim_pos != (-1,-1) and victim_pos != self.pos:
				victim_dist = math.sqrt(pow((self.pos[0] - victim_pos[0]),2) + pow((self.pos[1] - victim_pos[1]),2))
				if victim_dist < 6:
					actions = ('shoot', victim_pos)
					#print(actions)
					return actions
			i += 1 


		n = len(self.ground_map)
		#print(n)
		m = len(self.ground_map[0])
		#print(m)
		map_list = self.ground_map.tolist()
		#print(map_list)
		x1 = self.pos[0]
		y1 = self.pos[1]
		x2 = self.next_safe_center[0]
		y2 = self.next_safe_center[1]
		#print(x1,y1,x2,y2)
		
		if self.hunger < 5:
			bfpb = BreadFirstPathsB(Map(n, m, None, map_list), Point(y2,x2),'find_forest')
		elif self.thirst < 5:
			bfpb = BreadFirstPathsB(Map(n, m, None, map_list), Point(y2,x2),'find_near_water')
		else:
			bfpb = BreadFirstPathsB(Map(n, m, None, map_list), Point(y2,x2),'not_wall_water')
		#print(map_list[x2][y2])
		#if map_list[x2][y2] == 1 or map_list[x2][y2] == 3: 
		#	for delta in self.deltas:
		#			delta_x, delta_y = delta
		#			if map_list[x2+delta_x][y2+delta_y] == 0 or map_list[x2+delta_x][y2+delta_y] == 2:
		#				x2 = x2+delta_x
		#				y2 = y2+delta_y
		#				break
		target = bfpb.get_d()
		x2 = target.y
		y2 = target.x

		target_place =(x2,y2)
		#print(target_place)

		if self.pos != target_place :
			bfp = BreadFirstPathsA(Map(n, m, None, map_list), Point(y1,x1), Point(y2,x2))
			self.path = bfp.find_path()
			if self.path :
			#print(self.path)
				next_pos = self.path.pop()
				next_pos[0] ,next_pos[1] = next_pos[1],next_pos[0]
				actions = ('move',tuple(next_pos))
				#print(actions)
				return actions
			else:
				victim_pos = self.find_the_nearest(self.pos , self.players_pos)
				actions = ('shoot', victim_pos)
				#print('neibusheji')
				return actions
		else:
			victim_pos = self.find_the_nearest(self.pos , self.players_pos)
			actions = ('shoot', victim_pos)
			#print('neibusheji')
			return actions

