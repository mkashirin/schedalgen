# pyright: reportAttributeAccessIssue = false
# pyright: reportOptionalMemberAccess = false
# pyright: reportOperatorIssue = false

import random
from typing import Any, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import random
from deap import algorithms, tools, base, creator

from .benchmark import Benchmark
from .problem import Problem


class LibSolution:

    def __init__(
        self,
        population_size: int,
        hall_of_fame_size: int,
        tournament_size: int,
        random_seed: int = 52,
        problem: Optional[Problem] = None,
        benchmark: Optional[Benchmark] = None,
        hard_penalty: Optional[int] = None,
    ) -> None:
        self.hard_contraint_penalty = hard_penalty
        self.population_size = population_size
        self.hall_of_fame_size = hall_of_fame_size
        self.tournament_size = tournament_size
        self.random_seed = random_seed
        self.schedule_problem = problem if problem is not None else Problem()
        self.schedule_problem_benchmark = (
            benchmark
            if benchmark is not None
            else (
                Benchmark(self.hard_constraint_penalty)
                if self.hard_contraint_penalty is not None
                else None
            )
        )
        if self.schedule_problem_benchmark is None:
            message = "hard constaint penalty can not be None"
            raise ValueError(message)

        self.toolbox = base.Toolbox()

    def perform_algorithm(
        self,
        *,
        crossover_proba: float,
        mutation_proba: float,
        n_generations: int,
        stats=None,
        hall_of_fame=None,
        verbose=__debug__,
    ) -> Tuple[Any, Any]:
        """This algorithm is similar to DEAP's ``eaSimple()`` algorithm, with the
        modification that halloffame is used to implement an elitism mechanism.
        The individuals contained in the ``halloffame`` are directly injected into
        the next generation and are not subject to the genetic operators of
        selection, crossover and mutation.
        """
        self._setup()
        population = self.toolbox.populationCreator(n=self.population_size)

        stats = tools.Statistics(lambda individual: individual.fitness.values)
        stats.register("min", np.min)
        stats.register("mean", np.mean)
        hall_of_fame = tools.HallOfFame(self.hall_of_fame_size)
        logbook = tools.Logbook()
        logbook.header = ("gen", "nevals")

        # Evaluate the individuals with an invalid fitness
        invalid_individual = [
            individual
            for individual in population
            if not individual.fitness.valid
        ]
        fitnesses = self.toolbox.map(self.toolbox.evaluate, invalid_individual)
        for individual, fitness in zip(invalid_individual, fitnesses):
            individual.fitness.values = fitness

        hall_of_fame.update(population)
        hall_of_fame_size = (
            len(hall_of_fame.items) if hall_of_fame.items else 0
        )

        record = stats.compile(population) if stats else {}
        logbook.record(gen=0, nevals=len(invalid_individual), **record)
        if verbose:
            print(logbook.stream)

        # Begin the generational process
        for generation in range(1, n_generations + 1):
            print("gen", generation)
            # Select the next generation individuals
            offspring = self.toolbox.select(
                population, len(population) - hall_of_fame_size
            )
            # Vary the pool of individuals
            offspring = algorithms.varAnd(
                offspring, self.toolbox, crossover_proba, mutation_proba
            )
            # Evaluate the individuals with an invalid fitness
            invalid_individual = [
                individual
                for individual in offspring
                if not individual.fitness.valid
            ]
            fitnesses = self.toolbox.map(
                self.toolbox.evaluate, invalid_individual
            )
            for individual, fitness in zip(invalid_individual, fitnesses):
                individual.fitness.values = fitness

            # Add the best back to population
            offspring.extend(hall_of_fame.items)
            # Update the hall of fame with the generated individuals
            hall_of_fame.update(offspring)
            # Replace the current population by the offspring
            population[:] = offspring
            # Append the current generation statistics to the logbook
            record = stats.compile(population) if stats else {}
            logbook.record(
                gen=generation, nevals=len(invalid_individual), **record
            )
            if verbose:
                print(logbook.stream)

        return population, logbook

    def report_stats(self, hall_of_fame: Any, logbook: Any) -> None:
        best_individual = hall_of_fame.items[0]
        best_individual_string = "".join(map(str, best_individual))
        self.schedule_problem_benchmark.calculate_cost(best_individual_string)
        min_fitness_values, mean_fitness_values = logbook.select("min", "mean")
        self.schedule_problem.save_table(
            best_individual_string, "schedule.json"
        )
        report = f"""
Solution report\n
Best fitness value: {best_individual.fitness.values[0]}
Best individual stats
{self.schedule_problem_benchmark.report_violations()}
Schedule output file name: schedule.json
"""
        print(report)

        _, axis = plt.subplots()
        max_value = np.max(
            np.concatenate([min_fitness_values, mean_fitness_values])
        )
        y_limit = int((max_value + 10) - (max_value % 10))
        axis.set_xlim(0, self.max_generations)
        axis.set_ylim(0, y_limit)
        axis.set_xlabel("Generation")
        axis.set_ylabel("Min/mean fitness value")
        axis.plot(
            min_fitness_values,
            label="Min fitness",
            color="red",
            linestyle="--",
        )
        axis.plot(mean_fitness_values, label="Mean fitness", color="blue")
        axis.set_title("Min and mean fitness over generations", fontsize=14)

        plt.legend()
        plt.tight_layout()
        plt.savefig("stats.png")

    def calculateCost(self, individual) -> Tuple:
        individual_string = "".join(map(str, individual))
        cost = (
            self.schedule_problem_benchmark.calculate_cost(individual_string),
        )
        return cost

    def _setup(self) -> None:
        self._mutation_range_step = (
            self.schedule_problem.total_string_len
            * self.schedule_problem.classes_per_day
        )

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMin)
        self.toolbox.register("zeroOrOne", random.randint, 0, 1)
        self.toolbox.register(
            "individualCreator",
            tools.initRepeat,
            creator.Individual,
            self.toolbox.zeroOrOne,
            len(self.schedule_problem),
        )
        self.toolbox.register(
            "populationCreator",
            tools.initRepeat,
            list,
            self.toolbox.individualCreator,
        )
        self.toolbox.register("evaluate", self.calculateCost)
        self.toolbox.register(
            "select", tools.selTournament, tournsize=self.tournament_size
        )
        self.toolbox.register(
            "mate",
            tools.cxUniform,
            indpb=1.0 / len(self.schedule_problem),
        )
        self.toolbox.register(
            "mutate",
            self._mutateZeroBits,
            indpb=1.0 / self.schedule_problem.total_string_len,
        )

    def _mutateZeroBits(self, individual, indpb):
        print("mutated")
        for i in range(0, len(individual), self._mutation_range_step):
            random_multiplier = (
                random.randint(0, self.schedule_problem.classes_per_day) // 2
            )
            plus_length = (
                self.schedule_problem.total_string_len * random_multiplier
            )
            if random.random() < indpb:
                individual[i : i + plus_length] = list("0" * plus_length)
        return (individual,)
