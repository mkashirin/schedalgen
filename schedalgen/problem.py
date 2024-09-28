# pyright: reportIndexIssue = false
# pyright: reportAttributeAccessIssue = false

from random import getrandbits
from typing import Any, Dict, Optional, Tuple
from json import dump

from ._typing import SchedulesTable, ClassDecodings, Individual
from .utils import format_binary, wrap_dict, wrap_dict_cycle


class Problem:

    def __init__(
        self,
        total_string_len: int = 8,
        *,
        classroom_char: int = 4,
        teacher_char: int = 7,
        type_char: int = 7,
        total_groups: int = 63,
        courses: int = 2,
        directions: int = 4,
        groups_per_lecture: int = 4,
        groups_per_practice: int = 2,
        classes_per_day: int = 8,
        days_per_week: int = 6,
        weeks_per_group: int = 2,
        lecture_classrooms: Optional[Tuple[int] | range] = None,
        practice_classrooms: Optional[Tuple[int] | range] = None,
    ) -> None:
        self.total_string_len = total_string_len

        self.classroom_char = classroom_char
        self.teacher_char = teacher_char
        self.type_char = type_char
        self.total_classrooms = 2**self.classroom_char - 1
        self.total_groups = total_groups

        self.courses = courses
        self.directions = directions
        self.groups_per_lecture = groups_per_lecture
        self.groups_per_practice = groups_per_practice
        self.classes_per_day = classes_per_day
        self.days_per_week = days_per_week
        self.weeks_per_group = weeks_per_group

        self.scheduels_table: SchedulesTable = None

        self._setter: _AttrSetter = _AttrSetter(self)
        self._setter.set_classrooms_attrs(
            lecture_classrooms, practice_classrooms
        )
        self._setter.set_wrapper_attrs()
        self._setter.set_additional_attrs()

    def __len__(self):
        return self.total_schedules_len

    def create_random_individual(self) -> Individual:
        random_schedule = str()
        for _ in range(1, self.total_groups + 1):
            for _ in range(self.classes_per_group):
                class_string = format_binary(
                    getrandbits(self.total_string_len),
                    self.total_string_len,
                )
                random_schedule += class_string
        individual: Individual = (random_schedule, None)
        return individual

    def save_table(self, total_schedules: str, file_name: str) -> None:
        schedules_table: SchedulesTable = self._wrap_table(
            total_schedules
        )
        with open(file_name, "w") as file:
            dump(schedules_table, file, indent=4)

    def decode_string(self, class_string: str) -> ClassDecodings:
        classroom = int(class_string[: self.classroom_char], 2)
        teacher = int(
            class_string[self.classroom_char : self.teacher_char - 1], 2
        )
        class_type = int(class_string[self.type_char :], 2)
        class_tuple = classroom, teacher, class_type

        class_dict = dict()
        class_dict["classroom"] = classroom
        class_dict["teacher"] = teacher
        class_dict["type"] = class_type

        class_decodings: ClassDecodings = class_tuple, class_dict
        return class_decodings

    def _wrap_table(self, total_schedules: str) -> SchedulesTable:
        self.schedules_table = wrap_dict(
            total_schedules,
            self.wrap_groups_every_chars,
            "group",
            self.total_groups,
        )
        self.schedules_table = wrap_dict_cycle(
            self.schedules_table,
            self.wrap_weeks_every_chars,
            "week",
            self.weeks_per_group,
        )
        for group_number in self.schedules_table:
            self.schedules_table[group_number] = wrap_dict_cycle(
                self.schedules_table[group_number],
                self.wrap_days_every_chars,
                "day",
                self.days_per_week,
            )
        for group_number in self.schedules_table:
            for week_number in self.schedules_table[group_number]:
                self.schedules_table[group_number][week_number] = (
                    wrap_dict_cycle(
                        self.schedules_table[group_number][week_number],
                        self.wrap_classes_every_chars,
                        "class",
                        self.classes_per_day,
                    )
                )
        for group_number in self.schedules_table:
            for week_number in self.schedules_table[group_number]:
                for day_number in self.schedules_table[group_number][
                    week_number
                ]:
                    self._wrap_dict_classes(
                        self.schedules_table[group_number][week_number][
                            day_number
                        ]
                    )

        return self.schedules_table

    def _describe_table(
        self,
        schedules_table: Dict,
        spaces: int = 4,
    ) -> None:
        for key, val in schedules_table.items():
            if isinstance(val, dict):
                print("{}{}:\n".format(" " * spaces, str(key)))
                self._describe_table(val, spaces + 4)
            else:
                print("{}- {}: {}\n".format(" " * spaces, str(key), str(val)))

    def _wrap_dict_classes(self, day_schedule: Dict[str, Any]) -> None:
        for class_number in day_schedule:
            _, day_schedule[class_number] = self.decode_string(
                day_schedule[class_number]
            )


class _AttrSetter:

    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    def set_wrapper_attrs(self) -> None:
        problem = self.problem

        problem.wrap_groups_every_chars = (
            problem.total_string_len
            * problem.classes_per_day
            * problem.days_per_week
            * problem.weeks_per_group
        )
        problem.wrap_weeks_every_chars = (
            problem.wrap_groups_every_chars // problem.weeks_per_group
        )
        problem.wrap_days_every_chars = (
            problem.wrap_weeks_every_chars // problem.days_per_week
        )
        problem.wrap_classes_every_chars = (
            problem.wrap_days_every_chars // problem.classes_per_day
        )

    def set_additional_attrs(self) -> None:
        problem = self.problem

        problem.total_schedules_len = (
            problem.total_string_len
            * problem.classes_per_day
            * problem.days_per_week
            * problem.weeks_per_group
            * problem.total_groups
        )
        problem.classes_per_group = (
            problem.classes_per_day
            * problem.days_per_week
            * problem.weeks_per_group
        )

        problem.classroom_decoding_index = 0
        problem.teacher_decoding_index = 1
        problem.class_type_decoding_index = 2

        problem.lecture_int_code = 0
        problem.practice_int_code = 1

    def set_classrooms_attrs(
        self,
        lecture_classrooms: Optional[Tuple[int] | range],
        practice_classrooms: Optional[Tuple[int] | range],
    ) -> None:
        problem = self.problem

        problem.lecture_classrooms = (
            lecture_classrooms
            if lecture_classrooms is not None
            else range(1, (problem.total_classrooms + 1) // 2)
        )
        problem.practice_classrooms = (
            practice_classrooms
            if practice_classrooms is not None
            else range(
                (problem.total_classrooms + 1) // 2,
                problem.total_classrooms + 1,
            )
        )
