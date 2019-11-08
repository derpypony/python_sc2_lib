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
        # Used to prevent forge upgrade get chrono boost before cybercore does at least two
        self.cybercore_boost = 0

    async def on_step(self, iteration):
        await distribute_workers(self, iteration)
        await self.build_workers() if iteration % 2 == 0 else None
        await self.build_pylon() if iteration % 3 == 0 else None
        await self.build_assimilator() if iteration % 5 == 0 else None
        await self.build_forge() if iteration % 7 == 0 else None
        await self.build_cybercore() if iteration % 11 == 0 else None
        await self.build_gateway() if iteration % 13 == 0 else None
        await self.upgrade_warp_gate() if iteration % 17 == 0 else None
        await self.upgrade_weapon() if iteration % 17 == 9 else None
        await self.expand() if iteration % 19 == 0 else None


    async def build_pylon(self):
        if self.workers.amount < 25 and self.supply_left < 5 and not self.already_pending(PYLON):
            await build(self, PYLON)
        elif self.workers.amount >= 25 and self.supply_left < 10 and not self.already_pending(PYLON):
            await build(self, PYLON)

    async def build_assimilator(self):
        if self.units.of_type({ASSIMILATOR}).amount < 2:
            await build(self, ASSIMILATOR)

    async def expand(self):
        if self.townhalls.amount == 1 and self.units.of_type({GATEWAY}):
            await build(self, NEXUS)
        elif self.townhalls.amount == 2 and self.workers.amount > 40:
            await build(self, NEXUS)

    async def build_workers(self):
        if self.workers.amount < 45:
            for nexus in self.townhalls.ready.idle:
                await self.do(nexus.train(PROBE)) if self.can_afford(PROBE) else None

    async def build_cybercore(self):
        if self.units.of_type({GATEWAY}).ready and not self.units.of_type({CYBERNETICSCORE}) and not self.already_pending(CYBERNETICSCORE):
            oldest_building = self.townhalls.sorted(lambda u: self.townhall_age(u))[-1]
            await build(self, CYBERNETICSCORE, oldest_building)

    async def build_gateway(self):
        if self.units.of_type({GATEWAY, WARPGATE}).amount < 1:
            await build(self, GATEWAY)
        elif self.already_pending_upgrade(WARPGATERESEARCH) == 1 and self.units.of_type({GATEWAY, WARPGATE}).amount < 5:
            await build(self, GATEWAY)

    # We will prioritize the RESEARCH_WARPGATE
    async def upgrade_warp_gate(self):
        if self.units.of_type({CYBERNETICSCORE}).ready:
            cybercore = self.units.of_type({CYBERNETICSCORE}).ready.first
            if self.can_afford(RESEARCH_WARPGATE) and not self.already_pending_upgrade(WARPGATERESEARCH):
                await self.do(cybercore(RESEARCH_WARPGATE))
            for townhall in self.townhalls.ready:
                can_cast = await self.can_cast(townhall, EFFECT_CHRONOBOOSTENERGYCOST, cybercore)
                progress_less_than_80 = self.already_pending_upgrade(WARPGATERESEARCH) < 0.8 and self.already_pending_upgrade(WARPGATERESEARCH) > 0.01
                if can_cast and progress_less_than_80 and not cybercore.has_buff(CHRONOBOOSTENERGYCOST):
                    await self.do(townhall(EFFECT_CHRONOBOOSTENERGYCOST, cybercore))
                    self.cybercore_boost += 1

    async def upgrade_weapon(self):
        if self.units.of_type({FORGE}).ready.amount == 1:
            if self.can_afford(PROTOSSGROUNDWEAPONSLEVEL1) and not self.already_pending_upgrade(PROTOSSGROUNDWEAPONSLEVEL1):
                forge = self.units.of_type({FORGE}).ready.first
                await self.do(forge(FORGERESEARCH_PROTOSSGROUNDWEAPONSLEVEL1))
        elif self.units.of_type({FORGE}).ready.amount == 2:
            if self.can_afford(PROTOSSGROUNDARMORSLEVEL1) and not self.already_pending_upgrade(PROTOSSGROUNDARMORSLEVEL1):
                forge = self.units.of_type({FORGE}).idle.first
                await self.do(forge(FORGERESEARCH_PROTOSSGROUNDARMORLEVEL1)) if self.cybercore_boost > 1 else None
        try:
            forge = self.units.of_type({FORGE}).ready.filter(lambda u: not u.is_idle).random
            for townhall in self.townhalls.ready:
                can_cast = await self.can_cast(townhall, EFFECT_CHRONOBOOSTENERGYCOST, forge)
                progress_less_than_80 = forge.orders[0].progress < 0.8 and forge.orders[0].progress > 0.01
                if can_cast and progress_less_than_80 and not forge.has_buff(CHRONOBOOSTENERGYCOST):
                    await self.do(townhall(EFFECT_CHRONOBOOSTENERGYCOST, forge)) if self.cybercore_boost > 1 else None
        except:
            pass

    async def build_forge(self):
        if self.townhalls.amount == 2 and self.units.of_type({FORGE}).amount < 2 and not self.already_pending(FORGE):
            await build(self, FORGE)

    def townhall_age(self, townhall ):
        if not townhall:
            return None
        else:
            mineral_packs = self.state.mineral_field.closer_than(RADIUS, townhall)
            return -sum([pack.mineral_contents for pack in mineral_packs]) if mineral_packs else 0

class Dummy(sc2.BotAI):
    async def on_step(self, iteration):
        pass

sc2.run_game(sc2.maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, Sentbot(), name="Twilight Sparkle"),
    Bot(Race.Protoss, Dummy(), name="Sunset Shimmer")
], realtime=False)
