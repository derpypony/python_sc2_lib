from sc2_lib.distribute_worker import distribute_workers
from sc2_lib.build import build
from sc2_lib.offence_and_defence import smart_defence, smart_offence
import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer, Human
import random

RADIUS = 10

class Sentbot(sc2.BotAI):
    def on_start(self):
        self.cybercore_boost = False
        self.assimilator = 0
        self.pylon = 0
        self.base = 1
        self.gateway = 0
        self.cybercore = 0
        self.forge = 0
        self.cybercore_unlock = False
        self.warpgate_reserch_unlock = False
        self.forge_unlock = False
        self.army = {ZEALOT: 0, STALKER: 0}
        self.attack_signal = False
        possible_enemy_base_location = list(self.expansion_locations)
        possible_enemy_base_location.sort(key=lambda u: u.distance_to(self.enemy_start_locations[0]))
        self.possible_enemy_base_location = possible_enemy_base_location[0:2]

    async def on_building_construction_started(self, unit):
        if unit.type_id == ASSIMILATOR:
            await self.do(self.workers.closest_to(unit).stop())

    async def on_building_construction_complete(self, unit):
        if unit.type_id == GATEWAY and self.gateway == 1:
            self.cybercore_unlock = True
        if unit.type_id == ASSIMILATOR:
            workers = self.workers.sorted_by_distance_to(unit)[0:3]
            await self.do_actions([w.stop() for w in workers])
        if unit.type_id == CYBERNETICSCORE:
            self.warpgate_reserch_unlock = True
        if unit.type_id == FORGE:
            self.forge_unlock = True

    async def on_unit_created(self, unit):
        if unit.type_id in {ZEALOT, STALKER}:
            townhall = self.townhalls.sorted(lambda u: u.distance_to(self.enemy_start_locations[0]))[0]
            await self.do(unit(RALLY_UNITS, townhall.position))
            self.army[unit.type_id] += 1


    async def on_step(self, iteration):
        await distribute_workers(self, iteration)
        await self.keep_state()
        await self.build_workers() if iteration % 7 == 2 else None
        await self.build_pylon() if iteration % 7 == 4 else None
        await self.build_assimilator() if iteration % 7 == 6 else None
        await self.build_gateway() if iteration % 11 == 3 else None
        await self.build_cybercore() if iteration % 11 == 7 else None
        await self.build_forge() if iteration % 11 == 10 else None
        await self.upgrade_warp_gate() if iteration % 19 == 0 else None
        await self.choron_boost_cybercore() if iteration % 19 == 4 else None
        await self.forge_level_1_upgrade() if iteration % 19 == 10 else None
        await self.choron_boost_forge() if iteration % 19 == 16 else None
        await self.expand() if iteration % 23 == 5 else None
        await self.build_army() if iteration % 7 == 0 else None
        await smart_defence(self, [[ZEALOT, 3], [STALKER, 1]], iteration)
        await smart_offence(self, [[ZEALOT, 20], [STALKER, 8]], iteration, self.attack_signal)
        if sum([len(u.current) for u in self.offence_army_info_list]) > 20:
            self.attack_signal = True

    async def keep_state(self):
        self.pylon = self.units.of_type({PYLON}).amount
        self.base = self.units.of_type({NEXUS}).amount
        self.assimilator = self.units.of_type({ASSIMILATOR}).amount
        self.gateway = self.units.of_type({GATEWAY, WARPGATE}).amount
        self.cybercore = self.units.of_type({CYBERNETICSCORE}).amount
        self.forge = self.units.of_type({FORGE}).amount
        self.army[ZEALOT] = self.units.of_type({ZEALOT}).amount
        self.army[STALKER] = self.units.of_type({STALKER}).amount

    async def build_workers(self):
        if self.base == 1 and self.workers.amount < 19:
            await self.do(self.townhalls.ready.idle.random.train(PROBE)) if self.townhalls.ready.idle and self.can_afford(PROBE) else None
        elif self.base == 2 and self.workers.amount < 35:
            await self.do(self.townhalls.ready.idle.random.train(PROBE)) if self.townhalls.ready.idle and self.can_afford(PROBE) else None
        elif self.base > 2 and self.workers.amount < 60:
            await self.do(self.townhalls.ready.idle.random.train(PROBE)) if self.townhalls.ready.idle and self.can_afford(PROBE) else None

    async def build_pylon(self):
        if not self.already_pending(PYLON):
            if self.units.amount < 20 and self.supply_left < 5:
                await build(self, PYLON, max_distance=6)
            elif self.units.amount >= 20 and self.units.amount < 40 and self.supply_left < 10:
                await build(self, PYLON, max_distance=7)
            elif self.units.amount >= 40 and self.supply_left < 15:
                await build(self, PYLON, max_distance=8)

    async def build_assimilator(self):
        if self.assimilator == 0 and self.pylon > 0:
            await build(self, ASSIMILATOR)
        elif self.base == 3 and self.assimilator == 1 and not self.already_pending(ASSIMILATOR):
            await build(self, ASSIMILATOR)
        elif self.base > 4 and not self.already_pending(ASSIMILATOR) and self.assimilator < 4:
            await build(self, ASSIMILATOR)

    async def build_gateway(self):
        if self.gateway == 0 and self.pylon > 0:
            await build(self, GATEWAY)
        elif self.base == 2 and self.gateway < 3 and self.cybercore == 1:
            await build(self, GATEWAY)
        elif self.base > 3 and self.gateway < 5 and self.cybercore == 1:
            await build(self, GATEWAY)

    async def expand(self):
        if self.base == 1 and self.gateway == 1:
            await build(self, NEXUS)
        elif self.base == 2 and self.workers.amount > 35 and not self.already_pending(NEXUS):
            await build(self, NEXUS)
        elif self.base >= 3 and self.workers.idle.amount > 9 and not self.already_pending(NEXUS):
            await build(self, NEXUS)


    async def build_cybercore(self):
        if self.cybercore_unlock and not self.already_pending(CYBERNETICSCORE) and self.cybercore == 0:
            await build(self, CYBERNETICSCORE)

    async def build_forge(self):
        if self.base > 1 and self.cybercore > 0 and self.forge < 2 and not self.already_pending(FORGE):
            await build(self, FORGE)

    # We will prioritize the RESEARCH_WARPGATE
    async def upgrade_warp_gate(self):
        if self.warpgate_reserch_unlock and not self.already_pending_upgrade(WARPGATERESEARCH) and self.can_afford(RESEARCH_WARPGATE):
            cybercore = self.units.of_type({CYBERNETICSCORE}).first
            await self.do(cybercore(RESEARCH_WARPGATE))

    async def choron_boost_cybercore(self):
        progress = self.already_pending_upgrade(WARPGATERESEARCH)
        if progress < 0.85 and progress > 0.01:
            cybercore = self.units.of_type({CYBERNETICSCORE}).first
            for townhall in self.townhalls.ready:
                can_cast = await self.can_cast(townhall, EFFECT_CHRONOBOOSTENERGYCOST, cybercore)
                if can_cast and not cybercore.has_buff(CHRONOBOOSTENERGYCOST):
                    await self.do(townhall(EFFECT_CHRONOBOOSTENERGYCOST, cybercore))
                    break

    async def forge_level_1_upgrade(self):
        upgrade = {FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1: PROTOSSGROUNDARMORSLEVEL1,
                    FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1: PROTOSSGROUNDWEAPONSLEVEL1,
                    FORGERESEARCH_PROTOSSSHIELDSLEVEL1: PROTOSSSHIELDSLEVEL1}
        if self.forge_unlock:
            forges = self.units.of_type({FORGE}).ready.idle
            if forges:
                forge = forges.random
                abilities = await self.get_available_abilities(forge)
                if abilities:
                    ability = random.choice(abilities)
                    if self.can_afford(upgrade[ability]) and not self.already_pending_upgrade(upgrade[ability]):
                        await self.do(forges.random(ability))

    # Ground weapons and ground armor have low priority
    async def choron_boost_forge(self):
        if self.already_pending_upgrade(WARPGATERESEARCH) > 0.9 and self.forge_unlock:
            forges = self.units.of_type({FORGE}).ready.filter(lambda u: not u.is_idle)
            forge = forges.random if forges else None
            progress = forge.orders[0].progress if forge and forge.orders else 0
            if progress < 0.85 and progress > 0.01:
                for townhall in self.townhalls.ready:
                    can_cast = await self.can_cast(townhall, EFFECT_CHRONOBOOSTENERGYCOST, forge)
                    if can_cast and not forge.has_buff(CHRONOBOOSTENERGYCOST):
                        await self.do(townhall(EFFECT_CHRONOBOOSTENERGYCOST, forge))
                        break

    async def build_army(self):
        if self.units(WARPGATE).ready.idle.exists and self.army[ZEALOT] + self.army[STALKER] < 50:
            warpgate = self.units(WARPGATE).ready.idle.random
            pylon = self.units.of_type({PYLON}).random
            abilities = await self.get_available_abilities(warpgate)
            if random.random() < 0.75:
                position = await self.find_placement(WARPGATETRAIN_ZEALOT , pylon.position)
                if warpgate and WARPGATETRAIN_ZEALOT in abilities and self.can_afford(ZEALOT):
                    await self.do(warpgate.warp_in(ZEALOT, position))
            else:
                position = await self.find_placement(WARPGATETRAIN_STALKER , pylon.position)
                if warpgate and WARPGATETRAIN_STALKER in abilities and self.can_afford(STALKER):
                    await self.do(warpgate.warp_in(STALKER, position))


sc2.run_game(sc2.maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, Sentbot(), name="Twilight Sparkle"),
    Computer(Race.Protoss, Difficulty.Medium)
        ], realtime=False)
    # Human(Race.Protoss)
    # Bot(Race.Protoss, Sentbot(), name="Twilight Sparkle")
    # Computer(Race.Protoss, Difficulty.Medium)
