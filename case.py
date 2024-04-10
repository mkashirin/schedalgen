from alpygen.problem import ScheduleProblem
from alpygen.benchmark import ScheduleProblemBenchmark


def main():
    string = "010011110000111100001111010011110000111100001111"
    schedule_problem = ScheduleProblem(24)
    table = schedule_problem.wrap_schedules_table(string)
    schedule_problem.describe_table(table)

    schedule_problem_benchmark = ScheduleProblemBenchmark(
        10, problem=schedule_problem
    )
    print(schedule_problem_benchmark.count_exact_commons(string))


if __name__ == "__main__":
    main()
