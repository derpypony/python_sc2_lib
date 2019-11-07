from sc2.constants import *
"""In this script, we will assume self.workers.amount > 0 and self.townhalls.ready.amount > 0.
   Now the main function distribute_workers will only work for Protoss"""

"""self.state.mineral_field.closer_than(RADIUS, townhall) should return the near mineral cluster.
   This constant can be changed if it causes bugs in certain maps"""
RADIUS = 10

"""The main function distribute_workers has two parts, outer_distribute and inner_distribute.
   outer_distribute is used to transfer workers optimally between different townhalls, which
   is activited in around every 10 seconds(220 iterations) while inner_distribute is used to
   transfer workers optimally inside any townhall, which is activited in every 5 iterations"""
async def distribute_workers(self, iteration):
    # Will be activited every 10 second(about 220 iterations)
    await outer_distribute(self, iteration) if iteration % 220 == 0 else None
    # This step will make sure all the idle workers in the wild to return to a townhall. Activited in every second(22 game iterations)
    actions = [go_home(self, w) for w in self.workers.idle.filter(lambda u: self.townhalls.ready.closest_distance_to(u) > RADIUS)] if self.workers.idle else None
    await self.do_actions(actions) if actions and iteration % 22 == 0 else None
    for townhall in self.townhalls.ready:
        # Activited in every 5 game iteration
        await inner_distribute(self, townhall) if iteration % 5 == 0 else None

"""Function inner_distribute will try to optimize the inner workers distribution, and if the
   townhall has too many extra workers, inner_distribute will give those extra workers
   orders to stop working, over time, those idle workers near the townhall will gather up,
   you can think of those idle workers as 'garbage' and function outer_distribute will be the 'garbage truck' to
   gather 'garbage' produced by townhalls in every 10 seconds. After determining the most
   over staffed townhall and the most under staffed townhall, outer_distribute will just transfer
   extra workers from the most over staffed townhall to the most under staffed townhall"""
async def outer_distribute(self, iteration):
    most_understaffed_townhall = self.townhalls.ready.sorted(lambda u: need_worker_amount(self, u))[-1]
    most_overstaffed_townhall = self.townhalls.ready.sorted(lambda u: idle_worker_amount(self, u))[-1]
    if need_worker_amount(self, most_understaffed_townhall) > 0 and idle_worker_amount(self, most_overstaffed_townhall) > 0:
        transfer_amount = min(need_worker_amount(self, most_understaffed_townhall), idle_worker_amount(self, most_overstaffed_townhall))
        transfer_workers = idle_workers(self, most_overstaffed_townhall).take(transfer_amount)
        await self.do_actions([w.move(most_understaffed_townhall.position) for w in transfer_workers])

"""The principle behind the design of inner_distribute is to only transfer one worker
   in every iteration. For example, if there are 8 extra workers(8 surplus workers) near the townhall are mining mineral,
   in the next 5th game iteration, only one of the 8 extra workers will receive an order to stop mining,
   that means it will take 5*8=40 game iterations to fully optimize the workers distribution
   near the townhall. I also prioritize workers to gather gas(if they are idle)"""
async def inner_distribute(self, townhall):
    if expel_mineral_worker(self, townhall):
        await self.do(expel_mineral_worker(self, townhall))
        return
    if expel_gas_worker(self, townhall):
        await self.do(expel_gas_worker(self, townhall))
        return
    if idle_workers(self, townhall):
        worker = idle_workers(self, townhall).random
        task = give_task(self, worker, townhall)
        await self.do(task) if task else None

"""This function will give an order for workers to go to the townhall which are most under staffed"""
def go_home(self, worker):
    townhall = self.townhalls.ready.sorted(lambda u: need_worker_amount(self, u))[-1]
    return worker.move(townhall.position)

"""This function will give an order for the worker to gather under-stadffed resource.
   Gas is prioritized"""
def give_task(self, worker, townhall):
    if need_gas_worker(self, townhall):
        random_gas_structure = need_gas_worker(self, townhall).random
        return worker.gather(random_gas_structure)
    elif townhall.surplus_harvesters < 0:
        return worker.gather(self.state.mineral_field.closer_than(RADIUS, townhall).random)

"""If the mineral cluster is over staffed, this function will randomly choose a
   worker who is mining mineral and give it an order to stop"""
def expel_mineral_worker(self, townhall):
    if townhall.surplus_harvesters > 0:
        workers_1 = self.workers.filter(lambda u: len(u.orders) > 0)
        workers_2 = workers_1.filter(lambda u: u.orders[0].target == townhall.tag) if workers_1 else None
        worker = workers_2.random if workers_2 else None
        return worker.stop() if worker else None

"""If the Assimilatrs are over staffed, this function will randomly choose a
   worker who is mining gas and give it an order to stop"""
def expel_gas_worker(self, townhall):
    if need_expel_gas_worker(self, townhall):
        structure = need_expel_gas_worker(self, townhall).random
        workers_1 = self.workers.filter(lambda u: len(u.orders) > 0)
        workers_2 = workers_1.filter(lambda u: u.orders[0].target == structure.tag) if workers_1 else None
        worker = workers_2.random if workers_2 else None
        return worker.stop() if worker else None

"""This function will return all the Assimilatrs near the townhall that are over staffed"""
def need_expel_gas_worker(self, townhall):
    if not working_gas_structure(self, townhall):
        return None
    else:
        g = working_gas_structure(self, townhall).filter(lambda u: u.surplus_harvesters > 0)
        return g if g else None

"""This function will return all the Assimilatrs near the townhall that are under staffed"""
def need_gas_worker(self, townhall):
    if not working_gas_structure(self, townhall):
        return None
    else:
        g = working_gas_structure(self, townhall).filter(lambda u: u.surplus_harvesters < 0)
        return g if g else None

"""This function will return all the ready, none empty Assimilatrs near the townhall"""
def working_gas_structure(self, townhall):
    gas_structure = self.units.closer_than(RADIUS, townhall.position).of_type({ASSIMILATOR}) # change that for other races
    return gas_structure.ready.filter(lambda u: u.ideal_harvesters == 3) if gas_structure and gas_structure.ready else None

"""If the townhall is under staffed, Assimilatrs and mineral fields combined, this function
   will return the total neeeded workers number to fully gather these resource."""
def need_worker_amount(self, townhall):
    need_gas_worker_amount = sum([-u.surplus_harvesters for u in need_gas_worker(self, townhall)]) if need_gas_worker(self, townhall) else 0
    need_mineral_worker_amount = -townhall.surplus_harvesters if townhall.surplus_harvesters < 0 else 0
    return need_gas_worker_amount + need_mineral_worker_amount

"""This function will return the amount of idle workers near the townhall"""
def idle_worker_amount(self, townhall):
    return idle_workers(self, townhall).amount if idle_workers(self, townhall) else 0

"""This function will return all the idle workers near the radius of the townhall"""
def idle_workers(self, townhall):
    return self.workers.closer_than(RADIUS, townhall).idle if self.workers.closer_than(RADIUS, townhall) else None
