from numpy import linalg
import numpy as np
from sc2.position import Point2
from sc2.constants import *

"""The mineral cluster and vespens gas field should be in RADIUS of the townhall.
   the number 10 might be different in different maps"""
RADIUS = 10

"""This function will replace the self.build() function in sc2.botAI class. Right now it only works for Protoss.
   Common usage: if you want to expand(build a new Nexus), use 'await build(self, NEXUS)';
                 if you want to build pylon near the townhall, use 'await build(self, PYLON, townhall)';
                 if you want to build other buildings like Gateway near the townhall, use 'await build(self, GATEWAY, townhall)';
                 if you provide the position argument, building will be placed in the position you asked. For example,
                 if you want to build a Photon Cannons in enemy base, use 'await build(self, PHOTONCANNON, position=self.enemy_start_locations[0])'"""
async def build(self, building=None, townhall=None, position=None, max_distance=15, in_mineral=False, distance_to_other_pylon=7, near_distance=5):
    if not position:
        if building in {NEXUS}:
            position = await self.get_next_expansion()
            await build_subroutine(self, building, position) if position else None
        elif building == PYLON:
            townhall = self.townhalls.random if not townhall and self.townhalls else townhall
            position = await desired_pylon_location(self, townhall=townhall, max_distance=max_distance, in_mineral=in_mineral, distance_to_other_pylon=distance_to_other_pylon) if townhall else None
            await build_subroutine(self, building, position) if position else None
        else:
            townhall = self.townhalls.random if not townhall and self.townhalls else townhall
            position = await desired_location(self, building=building, townhall=townhall, max_distance=max_distance, in_mineral=in_mineral) if townhall else None
            await build_subroutine(self, building, position) if position else None
    elif position:
        if await self.can_place(building, position):
            await build_subroutine(self, building, position)
        else:
            """The default near_distance=5 may not be enough, consider make it larger if you must"""
            position = await self.find_placement(building, near=position, max_distance=near_distance)
            await build_subroutine(self, building, position) if position else None

"""This function is used as a subroutine of main function build"""
async def build_subroutine(self, building, position):
    if self.can_afford(building) and self.workers:
        worker = self.workers.closest_to(position)
        await self.do(worker.build(building, position))

"""This function will find desired location for building near the townhall"""
async def desired_location(self, building, townhall, max_distance=15, in_mineral=False):
    for i in range(100):
        point = circular_point(townhall.position, max_distance)
        if point_in_resource_field(self, point, townhall) != in_mineral:
            continue
        return await self.find_placement(building, near=point, max_distance=4)
    """If we try for 100 times and can't find a place, we will lower the standard"""
    return await self.find_placement(building, near=point, max_distance=new_max_distance) if i == 99 else None

"""This function will used to build pylon near the townhall, distance_to_other_pylon is used to control how close should pylons be placed"""
async def desired_pylon_location(self, townhall, max_distance=20, in_mineral=False, distance_to_other_pylon=7):
    for i in range(100):
        point = circular_point(townhall.position, max_distance)
        if self.units.of_type({PYLON}):
            closest_pylon_distance = self.units.of_type({PYLON}).closest_distance_to(point)
            if closest_pylon_distance < distance_to_other_pylon:
                continue
        if point_in_resource_field(self, point, townhall) != in_mineral:
            continue
        return await self.find_placement(PYLON, near=point, max_distance=4)
    """If we try for 100 times and can't find a place, we will lower the standard"""
    return await self.find_placement(PYLON, near=townhall.position) if i == 99 else None

"""This function will test whether the point is in the mineral field or not"""
def point_in_resource_field(self, point, townhall):
    matrix = outmost_resource(self, townhall)
    # If the vector(starting from townhall ending with the point) =  a * out_most_1.t2r + b * out_most_2.t2r where a , b > 0 , then it is in resource field
    test_array = linalg.solve(np.array(matrix).transpose(), np.array(point) - np.array(townhall.position))
    return all(test_array > 0)

"""This function finds the two outmost resource(gas or mineral pack) position near the townhall"""
def outmost_resource(self, townhall):
    resource_positions = near_resource_position(self, townhall)
    townhall_position = np.array(townhall.position)
    # Every element in t2r_vectors is a vector starting from townhall.position, ending with a resource field position
    t2r_vectors = [field - townhall_position for field in resource_positions]
    random_t2r_vector = t2r_vectors[0]
    cos_list = [cos_between_two_vectors(t2r, random_t2r_vector) for t2r in t2r_vectors]
    out_most_1 = [field_info(Point2(x), y, z) for x, y, z in zip(resource_positions, t2r_vectors, cos_list)]
    # We will choose the resource field that are most far away from random_t2r_vector, it should be one of the two postition we are looking for
    out_most_1 = sorted(out_most_1, key=lambda f: f.cos)[0]
    cos_list = [cos_between_two_vectors(t2r, out_most_1.t2r) for t2r in t2r_vectors]
    # We will choose the resource field that are most far away from out_most_1, it should be the left one of the two postition we are looking for
    out_most_2 = [field_info(Point2(x), y, z) for x, y, z in zip(resource_positions, t2r_vectors, cos_list)]
    out_most_2 = sorted(out_most_2, key=lambda f: f.cos)[0]
    return [out_most_1.t2r, out_most_2.t2r]

"""This functin will return the middle positon of the resource cluster(gas and mineral combined) near the townhall"""
def resource_middle_position(self, townhall):
    resource_positions = near_resource_position(self, townhall)
    return sum(resource_positions) / len(resource_positions)

"""This function will return positions near resource(mineral and gas combined) clusters"""
def near_resource_position(self, townhall):
    resource_field = self.state.vespene_geyser.closer_than(RADIUS, townhall)
    mineral_cluster = self.state.mineral_field.closer_than(RADIUS, townhall)
    resource_field.extend(mineral_cluster) if mineral_cluster else None
    return [np.array(r.position) for r in resource_field]

"""Find the cosin of angle between two 2D vectors. v1, v2 must be np.array"""
def cos_between_two_vectors(v1, v2):
    return np.dot(v1, v2) / (linalg.norm(v1) * linalg.norm(v2))

"""Generate uniformlly distributed point inside a circle"""
def circular_point(center, radius):
    center = np.array(center)
    for i in range(10000):
        point = 2 * radius * np.random.rand(1,2) + (center - radius * np.array([1, 1]))
        if linalg.norm(point - center) > radius:
            continue
        else:
            # np.array has werid numpy.bool_ behavior, used tolist() to clear that
            return Point2(point[0].tolist())

"""This class is used to record resource fields information"""
class field_info:
    def __init__(self, position, t2r, cos):
        self.position = position
        self.t2r = t2r
        self.cos = cos
