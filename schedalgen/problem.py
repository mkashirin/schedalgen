# pyright: reportIndexIssue = false
# pyright: reportAttributeAccessIssue = false

from textwrap import wrap
from typing import Any, Dict, Optional, Tuple

from ._typing import SchedulesTable, ClassDecodings


class ScheduleProblem:

    def __init__(
        self,
        total_string_len: int = 24,
        *,
        group_char: int = 8,
        classroom_char: int = 16,
        teacher_char: int = 23,
        type_char: int = 23,
        groups_per_lecture: int = 4,
        groups_per_practice: int = 2,
        classes_per_day: int = 8,
        days_per_week: int = 6,
        weeks_per_group: int = 2,
        lecture_classrooms: Optional[Tuple[int]] = None,
        practice_classrooms: Optional[Tuple[int]] = None,
    ):
        # Settings
        self.total_string_len = total_string_len

        self.group_char = group_char
        self.classroom_char = classroom_char
        self.teacher_char = teacher_char
        self.type_char = type_char
        self.total_len_without_group = self.total_string_len - self.group_char
        self.total_classrooms = (
            2 ** (self.classroom_char - self.group_char) - 1
        )
        self.total_groups = 2**self.group_char - 1
        self.lecture_classrooms = (
            lecture_classrooms
            if lecture_classrooms is not None
            else tuple(range(1, (self.total_classrooms + 1) // 2))
        )
        self.practice_classrooms = (
            practice_classrooms
            if practice_classrooms is not None
            else tuple(
                range((self.total_classrooms + 1) // 2, self.total_classrooms)
            )
        )

        # Constraints
        self.groups_per_lecture = groups_per_lecture
        self.groups_per_practice = groups_per_practice
        self.classes_per_day = classes_per_day
        self.days_per_week = days_per_week
        self.weeks_per_group = weeks_per_group

        self.classes_per_group = (
            self.classes_per_day * self.days_per_week * self.weeks_per_group
        )

        # Wrap every characters
        self.wrap_groups_every_chars = (
            self.total_string_len
            * self.classes_per_day
            * self.days_per_week
            * self.weeks_per_group
        )
        self.wrap_weeks_every_chars = (
            self.wrap_groups_every_chars
            // self.total_string_len
            // self.weeks_per_group
            * self.total_len_without_group
        )
        self.wrap_days_every_chars = (
            self.wrap_weeks_every_chars // self.days_per_week
        )
        self.wrap_classes_every_chars = (
            self.wrap_days_every_chars // self.classes_per_day
        )

        # State
        self.scheduels_table: SchedulesTable = None

        self.__validate_initializer()

    def __validate_initializer(self):
        exceptions = {
            "chars specified are not compatable with the string length": (
                self.group_char
                + (self.classroom_char - self.group_char)
                + (self.teacher_char - self.classroom_char)
                + (self.type_char - self.teacher_char)
                + 1
            )
            != self.total_string_len,
            "char indicies specified incorrectly": not (
                self.group_char < self.classroom_char
                and self.classroom_char < self.teacher_char
                and self.teacher_char < self.type_char
            ),
            "classrooms specified incorrectly": (
                len(self.lecture_classrooms) + len(self.practice_classrooms)
            )
            or (set(self.lecture_classrooms) & set(self.practice_classrooms)),
            "incorrect range of days per week": self.days_per_week < 0
            or self.days_per_week > 7,
            "incorrect range of classes per day": self.classes_per_day < 0
            or self.classes_per_day > 8,
        }
        for message, value in exceptions.items():
            if value:
                raise ValueError(message)

    def wrap_schedules_table(self, total_schedules: str) -> SchedulesTable:
        schedules_sorted = self.sort_by_groups(total_schedules)

        self.schedules_table = self.wrap_dict(
            schedules_sorted,
            self.wrap_groups_every_chars,
            "group",
            self.total_groups,
        )
        weeks_dict = self._wrap_dict_cycle(
            self.schedules_table,
            self.wrap_weeks_every_chars,
            "week",
            self.weeks_per_group,
        )
        days_dict = self._wrap_dict_cycle(
            self._get_values(weeks_dict),
            self.wrap_days_every_chars,
            "day",
            self.days_per_week,
        )
        classes_dict = self._wrap_dict_cycle(
            self._get_values(days_dict),
            self.wrap_classes_every_chars,
            "class",
            self.classes_per_day,
        )
        classes_decoded: Dict = self._get_values(classes_dict)
        for class_key in classes_decoded.keys():
            _, classes_decoded[class_key] = self.decode_string(
                classes_decoded[class_key]
            )

        return self.schedules_table

    def describe_table(self, schedules_table: Dict, spaces: int = 0) -> None:
        for key, val in schedules_table.items():
            if isinstance(val, dict):
                print("{}{}:".format(" " * spaces, str(key)))
                self.describe_table(val, spaces + 4)
            else:
                print("{}- {}: {}".format(" " * spaces, str(key), str(val)))

    def decode_string(self, class_string: str) -> ClassDecodings:
        classroom = int(class_string[: self.group_char], 2)
        teacher = int(
            class_string[self.group_char : self.classroom_char - 1], 2
        )
        class_type = int(class_string[self.type_char :], 2)
        class_tuple = (classroom, teacher, class_type)

        class_dict = dict()
        class_dict["classroom"] = classroom
        class_dict["teacher"] = teacher
        class_dict["type"] = class_type

        class_decodings: ClassDecodings = (class_tuple, class_dict)
        return class_decodings

    def sort_by_groups(self, string_to_cut: str) -> str:
        strings_wrapped = list(wrap(string_to_cut, self.total_string_len))
        sorting_key = lambda string: string[: self.group_char]
        strings_sorted = sorted(strings_wrapped, key=sorting_key)
        for i, _ in enumerate(strings_sorted):
            strings_sorted[i] = strings_sorted[i][self.group_char :]
        strings_concat = "".join(strings_sorted)
        return strings_concat

    @staticmethod
    def wrap_dict(
        to_wrap: str,
        wrap_every_chars: int,
        key_name: str,
        strings_number: int,
    ) -> Dict[str, Any]:
        strings_wrapped = tuple(wrap(to_wrap, wrap_every_chars))
        strings_wrapped_dict = {
            "{}-{}".format(key_name, key + 1): val
            for key, val in zip(range(strings_number), strings_wrapped)
        }
        return strings_wrapped_dict

    def _wrap_dict_cycle(
        self,
        dict_to_wrap: Dict[str, Any],
        wrap_every_chars: int,
        key_name: str,
        items_number: int,
    ) -> Dict[str, Any]:
        for dict_key in dict_to_wrap.keys():
            dict_to_wrap[dict_key] = self.wrap_dict(
                dict_to_wrap[dict_key],
                wrap_every_chars,
                key_name,
                items_number,
            )
        return dict_to_wrap

    @staticmethod
    def _get_values(get_from: Dict) -> Dict:
        values = tuple(get_from.values())[0]
        return values
