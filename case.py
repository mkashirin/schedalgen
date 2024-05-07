from random import seed

from schedalgen.solution import ScheduleProblemSolution
from schedalgen.problem import ScheduleProblem
from schedalgen.benchmark import ScheduleProblemBenchmark


def main():
    seed(52)

    schedule_problem = ScheduleProblem(
        8,
        classroom_char=4,
        teacher_char=7,
        type_char=7,
        total_groups=127,
        classes_per_day=5,
    )
    schedule_problem_benchmark = ScheduleProblemBenchmark(
        5,
        soft_constraint_penalty=3,
        check_for_courses_and_directions=False,
        problem=schedule_problem,
    )
    schedule_problem_solution = ScheduleProblemSolution(
        population_size=100,
        crossover_proba=0.9,
        mutation_proba=0.3,
        max_generations=15,
        hall_of_fame_size=15,
        tournament_size=3,
        schedule_problem=schedule_problem,
        schedule_problem_benchmark=schedule_problem_benchmark,
    )

    hall_of_fame, logbook = schedule_problem_solution.perform_algorithm()
    schedule_problem_solution.report_stats(hall_of_fame, logbook)


if not __name__ != "__main__":
    main()
