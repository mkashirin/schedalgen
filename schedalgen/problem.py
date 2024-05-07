# pyright: reportIndexIssue = false
# pyright: reportAttributeAccessIssue = false

from random import getrandbits
from typing import Any, Dict, Optional, Tuple
from json import dump

from ._typing import SchedulesTable, ClassDecodings
from .utils import format_binary, get_nested_list, wrap_dict, wrap_dict_cycle


class ScheduleProblem:
    """This class serves as an interface for the general project's problem
    statement. All the inputs passed to the inilializer get validated
    (incorrect value causes :class:`ValueError`) by :class:`_ScheduleProblemValidator`.
    In essense, the functions of this class are:
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
        self.__set_classrooms_attrs(lecture_classrooms, practice_classrooms)

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

        self.__set_groups_splitting_attrs()
        self.__set_additional_attrs()

        # Wrap every characters
        self.__set_wrapper_attrs()

        # Validate provided input
        self.__validator = _ScheduleProblemValidator(self)
        self.__validator.validate_problem_initializer()

    def __len__(self):
        return self.total_schedules_len

    def create_random_schedule(self) -> str:
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
        return random_schedule

    def save_table(self, total_schedules: str, file_name: str) -> None:
        schedules_table: SchedulesTable = self._wrap_schedules_table(
            total_schedules
        )
        with open(file_name, "w") as file:
            dump(schedules_table, file, indent=4)

    def decode_string(self, class_string: str) -> ClassDecodings:
        """Decode any class string of length :attribute:`ScheduleProblem.total_string_len` 
        turning it into a dictionary.

        :parameter class_string: Binary string representing the class.
        :type class_string: :class:`str`

        :returns: Dictionary describing a class with integers.
        :rtype: :class:`ClassDescodings` (look up the :module:`_typing.py` file)
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

    def _wrap_schedules_table(self, total_schedules: str) -> SchedulesTable:
        """Wrap the schedule string in a nested dictionary.

        :parameter total_schedules: Schedule string 
        (e.g. the one returned by :method:`ScheduleProblem.create_random_schedule()`).
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
        :method:`ScheduleProblem.wrap_schedules_table()` function 
        (by printing out in the shell).

        :parameter schedules_table: Schedules table produced by
        :method:`ScheduleProblem.wrap_schedules_table()`.
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

    def __set_wrapper_attrs(self):
        """Sets the attributes required for the wrapping functions. Reduces
        boilerplate in the :method:`ScheduleProblem.__init__()` method.
        """
        wrap_groups_every_chars = (
            self.total_string_len
            * self.classes_per_day
            * self.days_per_week
            * self.weeks_per_group
        )
        wrap_weeks_every_chars = (
            wrap_groups_every_chars // self.weeks_per_group
        )
        wrap_days_every_chars = wrap_weeks_every_chars // self.days_per_week
        wrap_classes_every_chars = (
            wrap_days_every_chars // self.classes_per_day
        )

        setattr(
            self,
            "wrap_groups_every_chars",
            wrap_groups_every_chars,
        )
        setattr(self, "wrap_weeks_every_chars", wrap_weeks_every_chars)
        setattr(
            self,
            "wrap_days_every_chars",
            wrap_days_every_chars,
        )
        setattr(
            self,
            "wrap_classes_every_chars",
            wrap_classes_every_chars,
        )

    def __set_additional_attrs(self):
        """Sets some additional attributes required for benchmarking functions.
        Reduces boilerplate in the :method:`ScheduleProblem.__init__()` method.
        """
        total_schedules_len = (
            self.total_string_len
            * self.classes_per_day
            * self.days_per_week
            * self.weeks_per_group
            * self.total_groups
        )
        classes_per_group = (
            self.classes_per_day * self.days_per_week * self.weeks_per_group
        )
        setattr(self, "total_schedules_len", total_schedules_len)
        setattr(self, "classes_per_group", classes_per_group)

    def __set_groups_splitting_attrs(self):
        """Sets course/direction segregation based attributes required for
        benchmarking functions. Reduces boilerplate in the 
        :method:`ScheduleProblem.__init__()` method.
        """
        groups_per_course = (self.total_groups + 1) // self.courses
        groups_per_direction = (
            (self.total_groups + 1) // self.courses // self.directions
        )
        groups_by_course = tuple(
            range(start, start + groups_per_course)
            for start in range(0, self.total_groups, groups_per_course)
        )
        groups_by_direction_ranges = tuple(
            range(start, start + groups_per_direction)
            for start in range(0, self.total_groups, groups_per_direction)
        )
        _, groups_by_direction = get_nested_list(self.courses)
        course = 0
        for i, group_range in enumerate(groups_by_direction_ranges):
            course += 1 if i != 0 and not i % 8 != 0 else 0
            groups_by_direction[course].append(group_range)
        groups_by_direction = tuple(map(tuple, groups_by_direction))

        setattr(
            self,
            "groups_per_course",
            groups_per_course,
        )
        setattr(
            self,
            "groups_per_direction",
            groups_per_direction,
        )
        setattr(self, "groups_by_course", groups_by_course)
        setattr(self, "groups_by_direction", groups_by_direction)

    def __set_classrooms_attrs(
        self,
        lecture_classrooms: Optional[Tuple[int] | range],
        practice_classrooms: Optional[Tuple[int] | range],
    ):
        """Sets classroom classificating attributes required for benchmarking
        functions. Reduces boilerplate in the 
        :method:`ScheduleProblem.__init__()` method.
        """
        lecture_classrooms = (
            lecture_classrooms
            if lecture_classrooms is not None
            else range(1, (self.total_classrooms + 1) // 2)
        )
        practice_classrooms = (
            practice_classrooms
            if practice_classrooms is not None
            else range(
                (self.total_classrooms + 1) // 2, self.total_classrooms + 1
            )
        )

        setattr(self, "lecture_classrooms", lecture_classrooms)
        setattr(self, "practice_classrooms", practice_classrooms)


class _ScheduleProblemValidator:
    """Serves an interface for the initializer input to :class:`ScheduleProblem`
    validation functionality.
    """

    def __init__(self, problem: ScheduleProblem):
        self.problem = problem

    def validate_problem_initializer(self):
        """Just read the messages for each of the conditions if you are trying
        to understand this shit.
        """
        chars_length_cond = (
            self.problem.classroom_char
            + (
                self.problem.teacher_char - self.problem.classroom_char
                if self.problem.teacher_char - self.problem.classroom_char != 0
                else self.problem.teacher_char
            )
            + (self.problem.type_char - self.problem.teacher_char)
            + 1
            != self.problem.total_string_len
        )
        chars_length_message = (
            "chars specified are not compatable with the string length"
        )

        chars_indicies_cond = not (
            self.problem.classroom_char <= self.problem.teacher_char
            and self.problem.teacher_char <= self.problem.type_char
        )
        chars_indicies_message = "char indicies specified incorrectly"

        classrooms_cond = (
            len(self.problem.lecture_classrooms)
            + len(self.problem.practice_classrooms)
        ) != self.problem.total_classrooms or (
            set(self.problem.lecture_classrooms)
            & set(self.problem.practice_classrooms)
        )
        classrooms_message = "classrooms specified incorrectly"

        days_per_week_cond = (
            self.problem.days_per_week < 1 or self.problem.days_per_week > 7
        )
        days_per_week_message = "incorrect range of days per week"

        clases_per_day_cond = (
            self.problem.classes_per_day < 0
            or self.problem.classes_per_day > 8
        )
        classes_per_day_message = "incorrect range of classes per day"

        courses_directions_cond = (
            self.problem.total_groups + 1
        ) % self.problem.courses != 0 or (
            self.problem.total_groups + 1
        ) % self.problem.courses % self.problem.directions != 0
        courses_directions_message = (
            "courses or directions specified are not compatable with total "
            "groups number"
        )

        conditions = {
            chars_length_message: chars_length_cond,
            chars_indicies_message: chars_indicies_cond,
            classrooms_message: classrooms_cond,
            days_per_week_message: days_per_week_cond,
            classes_per_day_message: clases_per_day_cond,
            courses_directions_message: courses_directions_cond,
        }
        for message, value in conditions.items():
            if value:
                raise ValueError(message)
