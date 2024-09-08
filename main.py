from random import seed

from schedalgen import Benchmark, Problem, PureSolution


def main():
    seed(228)

    problem = Problem(
        8,
        classroom_char=4,
        teacher_char=7,
        type_char=7,
        total_groups=15,
        classes_per_day=5,
    )
    benchmark = Benchmark(5, soft_penalty=3, problem=problem)

    probas = (1.0 / len(problem), 1.0 / problem.total_string_len)
    solution = PureSolution(
        problem,
        benchmark,
        population_size=20,
        crossover_proba=0.9,
        mutation_proba=0.3,
        max_gens=30,
        fame_hall_size=20,
        tournament_size=3,
        indep_probas=probas,
    )
    solution.perform_algorithm()
    solution.report_stats()


if __name__ == "__main__":
    main()
