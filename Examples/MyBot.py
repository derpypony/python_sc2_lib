from sc2_lib.distribute_worker import distribute_workers
from sc2_lib.build import build
import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
RADIUS = 10

"""This bot will only have three bases"""
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
        self.weapon_or_armor_unlock = False

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
            self.weapon_or_armor_unlock = True

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
        await self.upgrade_armor() if iteration % 19 == 8 else None
        await self.upgrade_weapon() if iteration % 19 == 12 else None
        await self.choron_boost_weapon_and_armor() if iteration % 19 == 16 else None
        await self.expand() if iteration % 23 == 5 else None

    async def keep_state(self):
        self.pylon = self.units.of_type({PYLON}).amount
        self.base = self.units.of_type({NEXUS}).amount
        self.assimilator = self.units.of_type({ASSIMILATOR}).amount
        self.gateway = self.units.of_type({GATEWAY, WARPGATE}).amount
        self.cybercore = self.units.of_type({CYBERNETICSCORE}).amount
        self.forge = self.units.of_type({FORGE}).amount

    async def build_workers(self):
        if self.base == 1 and self.workers.amount < 19:
            await self.do(self.townhalls.ready.idle.random.train(PROBE)) if self.townhalls.ready.idle and self.can_afford(PROBE) else None
        elif self.base == 2 and self.workers.amount < 35:
            await self.do(self.townhalls.ready.idle.random.train(PROBE)) if self.townhalls.ready.idle and self.can_afford(PROBE) else None
        elif self.base == 3 and self.workers.amount < 50:
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

    async def build_gateway(self):
        if self.gateway == 0 and self.pylon > 0:
            await build(self, GATEWAY)
        elif self.base == 2 and self.gateway < 4 and self.cybercore == 1:
            await build(self, GATEWAY)

    async def expand(self):
        if self.base == 1 and self.gateway == 1:
            await build(self, NEXUS)
        elif self.base == 2 and self.workers.amount > 35 and not self.already_pending(NEXUS):
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

    async def upgrade_armor(self):
        if self.weapon_or_armor_unlock:
            forges = self.units.of_type({FORGE}).ready.idle
            if forges and not self.already_pending_upgrade(PROTOSSGROUNDARMORSLEVEL1) and self.can_afford(PROTOSSGROUNDARMORSLEVEL1):
                await self.do(forges.random(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1))

    async def upgrade_weapon(self):
        if self.weapon_or_armor_unlock:
            forges = self.units.of_type({FORGE}).ready.idle
            if forges and not self.already_pending_upgrade(PROTOSSGROUNDWEAPONSLEVEL1) and self.can_afford(PROTOSSGROUNDWEAPONSLEVEL1):
                await self.do(forges.random(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1))

    # Ground weapons and ground armor have low priority
    async def choron_boost_weapon_and_armor(self):
        if self.already_pending_upgrade(WARPGATERESEARCH) > 0.9 and self.weapon_or_armor_unlock:
            forges = self.units.of_type({FORGE}).ready.filter(lambda u: not u.is_idle)
            forge = forges.random if forges else None
            progress = forge.orders[0].progress if forge and forge.orders else 0
            if progress < 0.85 and progress > 0.01:
                for townhall in self.townhalls.ready:
                    can_cast = await self.can_cast(townhall, EFFECT_CHRONOBOOSTENERGYCOST, forge)
                    if can_cast and not forge.has_buff(CHRONOBOOSTENERGYCOST):
                        await self.do(townhall(EFFECT_CHRONOBOOSTENERGYCOST, forge))
                        break

sc2.run_game(sc2.maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, Sentbot(), name="Twilight Sparkle"),
    Computer(Race.Protoss, Difficulty.Easy)
], realtime=True)
