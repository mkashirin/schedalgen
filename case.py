from schedalgen.solution import ScheduleProblemSolution
from schedalgen.problem import ScheduleProblem
from schedalgen.benchmark import ScheduleProblemBenchmark


def main():
    schedule_problem = ScheduleProblem(
        8,
        classroom_char=4,
        teacher_char=7,
        type_char=7,
        total_groups=63,
        courses=2,
        directions=4,
    )
    schedule_problem_benchmark = ScheduleProblemBenchmark(
        5, soft_constraint_penalty=3, problem=schedule_problem,
    )
    schedule_problem_solution = ScheduleProblemSolution(
        10,
        population_size=300,
        crossover_proba=0.9,
        mutation_proba=0.3,
        max_generations=200,
        hall_of_fame_size=30,
        tournament_size=3,
        schedule_problem=schedule_problem,
        schedule_problem_benchmark=schedule_problem_benchmark,
    )

    hall_of_fame, logbook = schedule_problem_solution.perform_algorithm() 
    schedule_problem_solution.report_stats(hall_of_fame, logbook)


if not __name__ != "__main__":
    main()
