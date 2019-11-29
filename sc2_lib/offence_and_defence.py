from sc2.units import Units
# from scipy.optimize import curve_fit
from sc2.constants import *
import numpy as np
from sc2.position import Point2
import random
"""We prioritize defence force, when we have enough defence force, we will consider build offence force"""
async def smart_defence(self, composition, iteration):
    update_denfence_army(self, composition)
    defence_army_tag = []
    for army in self.defence_army_info_list:
        defence_army_tag.extend(list(army.current))
    defence_army = Units([self.units.find_by_tag(x) for x in defence_army_tag])
    enemy_army = self.known_enemy_units.not_structure.filter(lambda u: self.townhalls.closest_distance_to(u) < 20)
    if enemy_army:
        if defence_army.amount >= enemy_army.amount:
            attack_location = enemy_army.center if enemy_army else None
            await self.do_actions([army.attack(attack_location) for army in defence_army]) if iteration % 10 == 0 else None
        else:
            gather_location = self.townhalls.furthest_to(enemy_army.center).position
            await self.do_actions([army.move(gather_location) for army in defence_army]) if iteration % 20 == 0 else None
    else:
        gather_location = self.townhalls.closest_to(self.game_info.map_center).position
        await self.do_actions([army.move(gather_location) for army in defence_army]) if iteration % 40 == 0 else None

"""composition should be a list of lists, for example composition = [[ZEALOT, 20], [STALKER, 7]]"""

def update_denfence_army(self, composition):
    if all([self.units.of_type({army[0]}).amount == 0 for army in composition]):
        self.defence_army_info_list = [army_info(army[0], army[1], self.units.of_type({army[0]}).amount, set()) for army in composition]
    else:
        for army in self.defence_army_info_list:
            category = army.category
            ideal = army.ideal
            avaliable = self.units.of_type({category}).amount
            # update army_info.avaliable
            army.avaliable = avaliable
            # get all the tags in army.current that are currently alive
            current = army.current & set([unit.tag for unit in self.units])
            # update army_info.current
            army.current = current
            if avaliable <= ideal:
                [current.add(unit.tag) for unit in self.units.of_type({category})]
                continue
            elif avaliable > ideal:
                if len(current) < ideal:
                    replenish = self.units.of_type({category}).tags_not_in(current)
                    [current.add(unit.tag) for unit in replenish]
                    continue


def update_offence_army(self, composition):
    if all([self.units.of_type({army[0]}).amount == 0 for army in composition]):
        self.offence_army_info_list = [army_info(army[0], army[1], self.units.of_type({army[0]}).amount, set()) for army in composition]
    else:
        for army in self.offence_army_info_list:
            category = army.category
            ideal = army.ideal
            # next() is used to find the first target in the list that satisfies the condition
            offence_info_class = next(x for x in self.defence_army_info_list if x.category == category)
            avaliable = self.units.of_type({category}).amount - offence_info_class.ideal
            # update offence_army_info_list.avaliable
            army.avaliable = avaliable if avaliable > 0 else 0
            # get all the tags in army.current that are currently alive
            current = army.current & set([unit.tag for unit in self.units])
            # update offence_army_info_list.current
            army.current = current
            if avaliable <= ideal:
                [current.add(unit.tag) for unit in self.units.of_type({category}).tags_not_in(offence_info_class.current)]
                continue
            elif avaliable > ideal:
                if len(current) < ideal:
                    replenish = self.units.of_type({category}).tags_not_in(current.union(offence_info_class.current)).take(ideal - len(current))
                    [current.add(unit.tag) for unit in replenish]
                    continue

class army_info:
    def __init__(self, category, ideal, avaliable, current):
        self.category = category
        self.ideal = ideal # int
        self.avaliable = avaliable # int
        self.current = current # set
    def __str__(self):
            return f"category: {self.category}, ideal: {self.ideal}, avaliable: {self.avaliable}, current: {self.current}"


async def smart_offence(self, composition, iteration, attack_signal):
    update_offence_army(self, composition)
    offence_army_tag = []
    for army in self.offence_army_info_list:
        offence_army_tag.extend(list(army.current))
    offence_army = Units([self.units.find_by_tag(x) for x in offence_army_tag])
    if attack_signal:
        enemy_army = self.known_enemy_units
        random_army_1 = random.choice(offence_army)
        random_army_2 = random.choice(offence_army)
        if enemy_army and iteration % 5 == 0:
            if offence_army.amount >= enemy_army.amount:
                await self.do_actions([army.attack(enemy_army.center) for army in offence_army])
            else:
                await pull_back(self, enemy_army, offence_army)
        if random_army_1.distance_to(random_army_2) > 15:
            await self.do_actions([army.move(offence_army.center) for army in offence_army]) if iteration % 66 == 0 else None
        if offence_army.idle.amount > 0.9 * offence_army.amount:
            attack_location = random.choice(self.possible_enemy_base_location)
            await self.do_actions([army.move(attack_location) for army in offence_army]) if iteration % 5 == 2 else None

async def pull_back(self, enemy, army):
    enemy_location = np.array(enemy.center)
    army_location = np.array(army.center)
    pull_back_location = 2 * army_location - enemy_location
    pull_back_location = Point2(pull_back_location.tolist())
    await self.do_actions([u.move(pull_back_location) for u in army])
