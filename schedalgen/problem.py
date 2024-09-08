# pyright: reportIndexIssue = false
# pyright: reportAttributeAccessIssue = false

from random import getrandbits
from typing import Any, Dict, Optional, Tuple
from json import dump

from ._typing import SchedulesTable, ClassDecodings, Individual
from .utils import format_binary, wrap_dict, wrap_dict_cycle


class Problem:
    """This class serves as an interface for the general project's problem
    statement. In essense, the functions of this class are:
        - Creating random schedules;
        - Wrapping the schedules in a table object (nested dictionary, in fact);
        - Describing the wrapped table object (in a YAML like format);
        - Decoding individual class strings.
    Use it to produce random schedules or save schedules as tables and then
    save them as files.
    """

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
        """This initializer provides a way to comprehensively set up the
        problem.

        :parameter total_string_len: Sets the total length of a single
        individual.
        :type total_string_len: :class:`int`

        :keyword classroom_char: Index of the single class string
        representation where the characters reserved for the classroom end.
        :type classroom_char: :class:`int`
        :keyword teacher_char: The same as the :parameter:`classroom_char`
        but for the teacher.
        :type teacher_char: :class:`int`
        :keyword type_char: The same as the :parameter:`classroom_char`
        but for the class type (e.g. 0 for lecture and 1 for practice).
        :type type_char: :class:`int`
        :keyword total_groups: Defines the number of groups schedule would
        be made for.
        :type total_groups: :class:`int`
        :keyword courses: The number of courses the groups would be separated on.
        :type courses: :class:`int`
        :keyword directions: The number of directions the courses would be
        separated on.
        :type directions: :class:`int`
        :keyword groups_per_lecture: Maximum number of groups allowed to attend
        a lecture.
        :type groups_per_lecture: :class:`int`
        :keyword groups_per_practice: Maximum number of groups allowed to attend
        a practice.
        :type groups_per_practice: :class:`int`
        :keyword classes_per_day: Maximum number of classes to be put in a day.
        :type classes_per_day: :class:`int`
        :keyword days_per_week: Days in a week to be put in the schedule.
        :type days_per_week: :class:`int`
        :keyword weeks_per_group: How many weeks schedule would be made for.
        :type weeks_per_group: :class:`int`
        :keyword lecture_classrooms: Either tuple or range of classroom numbers
        to be reserved for lectures.
        :type lecture_classrooms: :class:`Optional[Tuple[int] | range]`
        :keyword practice_classrooms: Either tuple or range of classroom numbers
        to be reserved for practices.
        :type practice_classrooms: :class:`Optional[Tuple[int] | range]`

        :returns: None.
        :rtype: :class:`NoneType`
        """
        # Settings
        self.total_string_len = total_string_len

        self.classroom_char = classroom_char
        self.teacher_char = teacher_char
        self.type_char = type_char
        self.total_classrooms = 2**self.classroom_char - 1
        self.total_groups = total_groups

        # Constraints
        self.courses = courses
        self.directions = directions
        self.groups_per_lecture = groups_per_lecture
        self.groups_per_practice = groups_per_practice
        self.classes_per_day = classes_per_day
        self.days_per_week = days_per_week
        self.weeks_per_group = weeks_per_group

        # State
        self.scheduels_table: SchedulesTable = None

        # Additional attributes
        self._setter: _AttrSetter = _AttrSetter(self)
        self._setter.set_classrooms_attrs(
            lecture_classrooms, practice_classrooms
        )
        self._setter.set_wrapper_attrs()
        self._setter.set_additional_attrs()

    def __len__(self):
        return self.total_schedules_len

    def create_random_individual(self) -> Individual:
        """Create a random schedule string based on the parameters specified
        with the initializer.

        :returns: Schedule string.
        :rtype: :class:`str`
        """
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
        """Decode any class string of length :attribute:`Problem.total_string_len`
        turning it into a dictionary.

        :parameter class_string: Binary string representing the class.
        :type class_string: :class:`str`

        :returns: Dictionary describing a class with integers.
        :rtype: :class:`ClassDescodings` (look up the :module:`_typing.py` module)
        """
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
        """Wrap the schedule string in a nested dictionary.

        :parameter total_schedules: Schedule string
        (e.g. the one returned by :method:`Problem.create_random_schedule()`).
        :type total_schedules: :class:`str`

        :returns: Schedules table, which represents the nested dictionary with
        all the data about every individual group schedule.
        :rtype: :class:`SchedulesTable` (look up the :module:`_typing.py` file)
        """
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
        """Describe the table obtained by calling the
        :method:`Problem.wrap_schedules_table()` function
        (by printing out in the shell).

        :parameter schedules_table: Schedules table produced by
        :method:`Problem.wrap_schedules_table()`.
        :type schedules_table: :class:`dict`
        :parameter spaces: Number of spaces to use for tabulation.
        :type spaces: :class:`int`

        :returns: None.
        :rtype: :class:`NoneType`
        """
        for key, val in schedules_table.items():
            if isinstance(val, dict):
                print("{}{}:\n".format(" " * spaces, str(key)))
                self._describe_table(val, spaces + 4)
            else:
                print("{}- {}: {}\n".format(" " * spaces, str(key), str(val)))

    def _wrap_dict_classes(self, day_schedule: Dict[str, Any]) -> None:
        """Wraps the classes in a day schedule. Reduces nesting :keyword:`for`s."""
        for class_number in day_schedule:
            _, day_schedule[class_number] = self.decode_string(
                day_schedule[class_number]
            )


class _AttrSetter:

    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    def set_wrapper_attrs(self) -> None:
        """Sets the attributes required for the wrapping functions. Reduces
        boilerplate in the :method:`Problem.__init__()` method.
        """
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
        """Sets some additional attributes required for benchmarking functions.
        Reduces boilerplate in the :method:`Problem.__init__()` method.
        """
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
        """Sets classroom classificating attributes required for benchmarking
        functions. Reduces boilerplate in the
        :method:`Problem.__init__()` method.
        """
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
