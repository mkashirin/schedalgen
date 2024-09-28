# pyright: reportAttributeAccessIssue = false
# pyright: reportOperatorIssue = false

import random
from copy import deepcopy
from logging import basicConfig, info, INFO
from timeit import default_timer as timer
from typing import List, Tuple

from ._typing import Individual, Population
from .benchmark import Benchmark
from .problem import Problem
from .utils import (
    blank_individs_list,
    invalid_individ_values,
    invalid_individ_positions,
)


class FameHall:

    def __init__(self, size: int) -> None:
        self.size = size
        self.members: List[Individual] = list()
        self.best: Individual

    def __len__(self):
        return len(self.members)

    def __getitem__(self, i: int):
        return self.members[i]

    def __iter__(self):
        return iter(self.members)

    def append(self, individ: Individual) -> None:
        self.members.append(individ)

    def remove(self, i: int) -> None:
        del self.members[i]

    def insert(self, individ: Individual) -> None:
        to_insert = deepcopy(individ)
        _, ins_cost = to_insert
        for i in range(1, len(self)):
            i_off = i - 1
            _, left_cost = self[i_off]
            _, right_cost = self[i]
            if left_cost > ins_cost:
                self.members.insert(i_off, to_insert)
                self.best = to_insert
                break

            elif left_cost < ins_cost and right_cost > ins_cost:
                self.members.insert(i, to_insert)
                break
            elif left_cost == ins_cost or right_cost == ins_cost:
                break

    def update(self, population: Population) -> None:
        key_func = lambda ind: ind[1]
        # fmt: off
        population.sort(key=key_func)  # pyright: ignore[reportAssignmentType]
        # fmt: on
        if len(self) < 1:
            best_individs = population[: self.size]
            self.members += best_individs
            self.best = population[0]

        for ind in population:
            if len(self) <= self.size:
                self.insert(ind)

            if len(self) > self.size:
                self.remove(-1)


class PureSolution:

    def __init__(
        self,
        problem: Problem,
        benchmark: Benchmark,
        *,
        population_size: int,
        crossover_proba: float,
        mutation_proba: float,
        n_generations: int,
        fame_hall_size: int,
        tournament_size: int,
        indep_probas: Tuple[float, float],
    ) -> None:
        self.problem = problem
        self.benchmark = benchmark
        self.population_size = population_size
        self.crossover_proba = crossover_proba
        self.mutation_proba = mutation_proba
        self.n_generations = n_generations
        self.fame_hall_size = fame_hall_size
        self.tournament_size = tournament_size
        (self.cross_indep_proba, self.mut_indep_proba) = indep_probas

        basicConfig(format="%(message)s", level=INFO)
        self.__setup()

    def report_stats(self) -> None:
        best_value, best_cost = self.fame_hall.best
        self.benchmark.calculate_cost(best_value)
        self.problem.save_table(best_value, "schedule.json")
        report = f"""
Solution report
Best fitness value: {best_cost}\n
Best individual stats 
{self.benchmark.report_violations()}
Schedule output file name: schedule.json
"""
        info(report)

    def perform_algorithm(
        self,
    ) -> None:
        population: Population = self.init_population(self.population_size)
        invalid_ind_values = tuple(invalid_individ_values(population))
        costs = map(self.benchmark.calculate_cost, invalid_ind_values)
        for (i, ind_val), cost in zip(
            enumerate(invalid_ind_values), costs, strict=True
        ):
            evaluated_ind: Individual = (ind_val, cost)
            population[i] = evaluated_ind
        self.fame_hall.update(population)
        curr_fame_hall_size = len(self.fame_hall)

        for gen in range(1, self.n_generations + 1):
            start = timer()

            n_sels = (
                len(population) - curr_fame_hall_size
                if curr_fame_hall_size < len(population)
                else curr_fame_hall_size
            )
            offspring = self.select_tourn(population, n_sels)
            offspring, cross_mut_nums = self.evolve(offspring)
            invalid_ind_values = invalid_individ_values(offspring)
            evaluated_inds = blank_individs_list(invalid_ind_values)
            costs = map(self.benchmark.calculate_cost, invalid_ind_values)
            for (i, ind_val), cost in zip(
                enumerate(invalid_ind_values), costs, strict=True
            ):
                evaluated_ind: Individual = (ind_val, cost)
                evaluated_inds[i] = evaluated_ind

            invalid_ind_pos = invalid_individ_positions(offspring)
            for i, ind in zip(invalid_ind_pos, evaluated_inds, strict=True):
                offspring[i] = ind

            end = timer()
            time_taken = round(end - start, 3)
            self.__log(gen, cross_mut_nums, time_taken)

            offspring.extend(self.fame_hall.members)
            self.fame_hall.update(offspring)

    def init_population(self, population_size: int) -> Population:
        population: Population = [
            self.problem.create_random_individual()
            for _ in range(population_size)
        ]
        return population

    def select_tourn(self, individs: Population, n_sels: int) -> Population:
        chosen: Population = list()
        for _ in range(n_sels):
            parts = random.sample(individs, self.tournament_size)
            key_func = lambda part: part[1]
            chosen += [max(parts, key=key_func)]
        return chosen

    def evolve(
        self, population: Population
    ) -> Tuple[Population, Tuple[int, int]]:
        offspring = [deepcopy(ind) for ind in population]
        cross_count = 0
        for i in range(1, len(offspring), 2):
            info("trying to cross")
            if random.random() < self.crossover_proba:
                to_cross: Tuple[Individual, Individual] = (
                    offspring[i - 1],
                    offspring[i],
                )
                offspring[i - 1], offspring[i] = self.cross_uni(to_cross)
                cross_count += 1

        mut_count = 0
        for i, _ in enumerate(offspring):
            info("trying to mut")
            if random.random() < self.mutation_proba:
                offspring[i] = self.mut_zeros(offspring[i])
                mut_count += 1
        evolved: Tuple[Population, Tuple[int, int]] = (
            offspring,
            (cross_count, mut_count),
        )
        return evolved

    def cross_uni(
        self, individs: Tuple[Individual, Individual]
    ) -> Tuple[Individual, Individual]:
        first, second = individs
        first_val, _ = first
        second_val, _ = second
        for i, _ in enumerate(first_val):
            if random.random() < self.cross_indep_proba:
                first_val = list(first_val)
                second_val = list(second_val)
                first_val[i], second_val[i] = second_val[i], first_val[i]

        first_cross: Individual = ("".join(first_val), None)
        second_cross: Individual = ("".join(second_val), None)
        crossed: Tuple[Individual, Individual] = (first_cross, second_cross)
        return crossed

    def mut_zeros(self, individ: Individual) -> Individual:
        ind_value, _ = individ
        for i in range(0, len(individ), self._mut_range_step):
            rand_mult = random.randint(0, self.problem.classes_per_day) // 2
            plus_len = self.problem.total_string_len * rand_mult
            if random.random() < self.mut_indep_proba:
                ind_value = list(ind_value)
                ind_value[i : i + plus_len] = list("0" * plus_len)

        mutated: Individual = ("".join(ind_value), None)
        return mutated

    def __setup(self) -> None:
        self.fame_hall = FameHall(self.fame_hall_size)
        self._mut_range_step = (
            self.problem.total_string_len * self.problem.classes_per_day
        )

    def __log(
        self, gen: int, cross_mut_nums: Tuple[int, int], time_taken: float
    ) -> None:
        cross_num, mut_num = cross_mut_nums
        members_costs = (str(cost) for _, cost in self.fame_hall)
        log_info = f"""Generation {gen} info:
- Best individual cost: {self.fame_hall.best[1]}
- Fame Hall members costs: [
    {",\n    ".join(members_costs)},
]
Operations overview:
- Crossovers done: {cross_num}
- Mutations done: {mut_num}
Completed in {time_taken} seconds
"""
        info(log_info)
