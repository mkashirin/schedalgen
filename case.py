from schedalgen.problem import ScheduleProblem
from schedalgen.benchmark import ScheduleProblemBenchmark


def main():
    string = "010011110000111100001110010011110000111100001111"
    schedule_problem = ScheduleProblem()
    table = schedule_problem.wrap_schedules_table(string)
    schedule_problem.describe_table(table)

    schedule_problem_benchmark = ScheduleProblemBenchmark(
        10, problem=schedule_problem
    )
    simultaneous = schedule_problem_benchmark._collect_simultaneous_classes(
        string
    )
    print(simultaneous, len(simultaneous))


if __name__ == "__main__":
    main()
