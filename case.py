# pyright: reportAttributeAccessIssue = false

from random import seed
from time import perf_counter

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
    print(schedule_problem.total_schedules_len)

    total_schedules = schedule_problem.create_random_schedule()
    schedule_problem_benchmark = ScheduleProblemBenchmark(
        10, problem=schedule_problem
    )
    seed(123)

    start_time = perf_counter()
    print(schedule_problem_benchmark.get_cost(total_schedules))
    end_time = perf_counter()
    print(f"Execution took {end_time - start_time} seconds.")


if __name__ == "__main__":
    main()
