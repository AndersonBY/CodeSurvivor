# -*- coding: utf-8 -*-
# @Author: Anderson
# @Date:   2019-04-02 19:22:08
# @Last Modified by:   Anderson
# @Last Modified time: 2019-04-17 11:40:49
import random

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
# count_down: 还有几次tick后就开始缩圈，当tick为0时表示正在缩圈。
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

class Agent(object):
	"""docstring for Agent"""
	def __init__(self):
		# 给你的玩家起个名字
		self.name = 'Player4'

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
	
	def take_action(self):
		x = self.pos[0] + random.randint(-1, 1)
		y = self.pos[1] + random.randint(-1, 1)
		actions = [('move', (x, y))]

		victim_pos = self.players_pos[0]
		i = 1
		while victim_pos==(-1,-1) or victim_pos==self.pos and i<len(self.players_pos):
			victim_pos = self.players_pos[i]
			i += 1

		actions.append(('shoot', victim_pos))

		return random.choice(actions)
		