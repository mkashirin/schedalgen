# pyright: reportOperatorIssue = false
# pyright: reportAttributeAccessIssue = false

from textwrap import wrap
from typing import Dict, List, Tuple

from ._typing import (
    ClassTuple,
    SimultaneousClasses,
    ValidClasses,
)
from .problem import ScheduleProblem
from .utils import get_nested_list, wrap_dict


class ScheduleProblemBenchmark:

    def __init__(
        self,
        hard_constraint_penalty: int,
        soft_constraint_penalty: int = 5,
        *,
        problem: ScheduleProblem = ScheduleProblem(),
    ):
        self.hard_constraint_penalty = hard_constraint_penalty
        self.soft_constraint_penalty = soft_constraint_penalty

        self.problem = problem

    def calculate_cost(self, total_shedules: str) -> int:
        self.__set_violation_attributes()

        simultaneous_classes = self._collect_simultaneous_classes(
            total_shedules
        )
        valid_classes = dict()
        for groups_list in simultaneous_classes:
            for group_number, class_tuple in enumerate(groups_list):
                classroom, class_type = class_tuple[0], class_tuple[2]
                if self._has_invalid_zeros(
                    class_tuple
                ) or self._is_invalid_classroom_type(
                    classroom,
                    class_type,
                ):
                    continue
                elif len(valid_classes.items()) < 1:
                    valid_classes[class_tuple] = [1, [group_number + 1]]
                    continue
                elif valid_classes.get(class_tuple, False):
                    self._add_if_got(
                        valid_classes,
                        group_number + 1,
                        class_tuple,
                    )
                    continue

                self._add_valid_class(valid_classes, group_number, class_tuple)

        self._count_classes_per_day_violations(total_shedules)

        hard_constraint_violations_cost = self.hard_constraint_penalty * (
            self.zero_class_members_violations
            + self.classroom_type_violations
            + self.classroom_number_contradiction_violations
            + self.multiple_teachers_contradiction_violations
            + self.classroom_type_contradiction_violations
            + self.teacher_contradiction_violations
            + self.course_or_direction_contradiction_violoations
        )
        soft_constraint_violations_cost = self.soft_constraint_penalty * (
            self.group_limit_violations + self.classes_per_day_violations
        )
        overall_cost = (
            hard_constraint_violations_cost + soft_constraint_violations_cost
        )

        return overall_cost

    def get_violations_report(self, spaces: int = 4) -> str:
        double_spacing = " " * spaces * 2
        report = (
            " " * spaces + "Hard constraint violations:\n"
            + double_spacing + "Zero class members: "
            + str(self.zero_class_members_violations) + "\n" 
            + double_spacing + "Classroom type: "
            + str(self.classroom_type_violations) + "\n"
            + double_spacing + "Classroom number contradiction: "
            + str(self.classroom_number_contradiction_violations) + "\n"
            + double_spacing + "Multiple teachers contradiction: "
            + str(self.multiple_teachers_contradiction_violations) + "\n"
            + double_spacing + "Classroom type contradiciton: "
            + str(self.classroom_number_contradiction_violations) + "\n"
            + double_spacing + "Teacher contradiction: "
            + str(self.teacher_contradiction_violations) + "\n"
            + double_spacing + "Course or direction contradiction: "
            + str(self.course_or_direction_contradiction_violoations) + "\n"
            + " " * spaces + "Soft constraint violations:\n"
            + double_spacing + "Group limit: "
            + str(self.group_limit_violations) + "\n"
            + double_spacing + "Classes per day: "
            + str(self.classes_per_day_violations) + "\n"
        )
        return report

    def _add_if_got(
        self,
        valid_classes: ValidClasses,
        group_number: int,
        class_tuple: ClassTuple,
    ) -> bool:
        if not (
            (
                not class_tuple[2] != 1
                and valid_classes[class_tuple][0]
                < self.problem.groups_per_practice
            )
            or (
                not class_tuple[2] != 0
                and valid_classes[class_tuple][0]
                < self.problem.groups_per_lecture
            )
        ):
            self.group_limit_violations += 1
            return False
        # fmt: off
        elif self._has_course_or_direction_contradiction(
            group_number, valid_classes[class_tuple][1][0]  # pyright: ignore[reportIndexIssue]
        ):
            self.course_or_direction_contradiction_violoations += 1
            return False
        # fmt: on
        elif group_number in valid_classes[class_tuple][1]:
            self.duplicate_groups_violations += 1
            return False
        valid_classes[class_tuple][0] += 1
        valid_classes[class_tuple][1] += [group_number]
        return True

    def _is_invalid_classroom_type(
        self, classroom: int, class_type: int
    ) -> bool:
        if classroom in self.problem.lecture_classrooms and class_type != 0:
            self.classroom_type_violations += 1
            return True
        elif classroom in self.problem.practice_classrooms and class_type != 1:
            self.classroom_type_violations += 1
            return True
        return False

    def _add_valid_class(
        self,
        valid_classes: ValidClasses,
        group_number: int,
        class_tuple: ClassTuple,
    ) -> None:
        for class_key in list(valid_classes):
            if (
                class_key[0] != class_tuple[0]
                and not class_key[1] != class_tuple[1]
                and not class_key[2] != class_tuple[2]
            ):
                self.classroom_number_contradiction_violations += 1
            elif (
                not class_key[0] != class_tuple[0]
                and class_key[1] != class_tuple[1]
                and not class_key[2] != class_tuple[2]
            ):
                self.multiple_teachers_contradiction_violations += 1
            elif (
                not class_key[0] != class_tuple[0]
                and not class_key[1] != class_tuple[1]
                and class_key[2] != class_tuple[2]
            ):
                self.classroom_type_contradiction_violations += 1
            elif (
                class_key[0] != class_tuple[0]
                and not class_key[1] != class_tuple[1]
                and class_key[2] != class_tuple[2]
            ):
                self.teacher_contradiction_violations += 1
            else:
                valid_classes[class_tuple] = [1, [group_number]]

    def _has_invalid_zeros(self, class_tuple: ClassTuple) -> bool:
        if 0 in class_tuple[:-1]:
            self.zero_class_members_violations += 1
            return True
        return False

    def _has_course_or_direction_contradiction(
        self,
        class_key_group: int,
        class_tuple_group: int,
    ) -> bool:
        for course, course_range in enumerate(self.problem.groups_by_course):
            if (
                class_key_group in course_range
                and class_tuple_group not in course_range
            ):
                return True
            for direction_range in self.problem.groups_by_direction[course]:
                if (
                    class_key_group in direction_range
                    and class_tuple_group not in direction_range
                ):
                    return True
        return False

    def _count_classes_per_day_violations(self, total_schedules) -> None:
        classes_per_day_by_group = self._collect_classes_per_day(
            total_schedules
        )
        # fmt: off
        mapped_to_violations = (
            map(
                lambda class_num: 1 if class_num < 2 or class_num > 5 else 0,
                classes_per_day_by_group[group_number],  # pyright: ignore[reportCallIssue, reportArgumentType]
            )
            for group_number, _ in enumerate(classes_per_day_by_group)
        )
        # fmt: on
        for classes_per_day_violations in mapped_to_violations:
            self.classes_per_day_violations += sum(classes_per_day_violations)

    def _collect_classes_per_day(
        self, total_schedules: str
    ) -> List[List[int]]:
        _, classes_per_day_by_group = get_nested_list(
            self.problem.total_groups
        )
        schedules_table = self.problem._wrap_schedules_table(total_schedules)
        for i, group_number in enumerate(schedules_table):
            for week_number in schedules_table[group_number]:
                for day_number in schedules_table[group_number][week_number]:

                    self._append_counter(
                        classes_per_day_by_group,
                        schedules_table[group_number][week_number],
                        day_number,
                        group_idx=i,
                    )
        return classes_per_day_by_group

    def _append_counter(
        self,
        classes_per_day_by_group: List[List[int]],
        schedules_table_week_depth: Dict[str, Dict[str, Dict[str, str]]],
        day_number: str,
        *,
        group_idx: int,
    ) -> None:
        class_per_day_counter = 0
        for class_number in schedules_table_week_depth[day_number]:
            class_dict = schedules_table_week_depth[day_number][class_number]
            class_per_day_counter += 1 if any(class_dict.values()) else 0
        classes_per_day_by_group[group_idx].append(class_per_day_counter)

    def _collect_simultaneous_classes(
        self, total_schedules: str
    ) -> SimultaneousClasses:
        """Collects every class for each group that is being conducted.

        :parameter total_schedules: A string representing schedules for each
            group.
            :type total_schedules: str

        :returns: List of lists of tuples. Each list contains classes being
            conducted at the same date and time. Single class is represented as
            tuple of three integers. First element of the tuple stands for
            classroom, second is for teacher and the third means class type
            (i.e. lecture or practice).
            :rtype: SimultaneousClasses (look up the "_typing.py" file)
        """
        groups_dict = self._wrap_groups_dict(total_schedules)

        classes_per_group_range, simultaneous_classes = get_nested_list(
            self.problem.classes_per_group
        )
        for group_key in groups_dict:
            for class_string, classes_list in zip(
                groups_dict[group_key], classes_per_group_range
            ):
                class_string_decoded, _ = self.problem.decode_string(
                    class_string
                )
                simultaneous_classes[classes_list].append(class_string_decoded)
        return simultaneous_classes

    def _wrap_groups_dict(
        self, total_schedules: str
    ) -> Dict[str, Tuple[str, ...]]:
        groups_dict_wrapped = wrap_dict(
            total_schedules,
            self.problem.wrap_groups_every_chars,
            "group",
            self.problem.total_groups,
        )
        for group_key in groups_dict_wrapped:
            groups_dict_wrapped[group_key] = tuple(
                wrap(
                    groups_dict_wrapped[group_key],
                    self.problem.total_string_len,
                )
            )
        return groups_dict_wrapped

    def __set_violation_attributes(self) -> None:
        # Hard constraints
        setattr(self, "zero_class_members_violations", 0)
        setattr(self, "duplicate_groups_violations", 0)
        setattr(self, "classroom_type_violations", 0)
        setattr(self, "classroom_number_contradiction_violations", 0)
        setattr(self, "multiple_teachers_contradiction_violations", 0)
        setattr(self, "classroom_type_contradiction_violations", 0)
        setattr(self, "teacher_contradiction_violations", 0)
        setattr(self, "course_or_direction_contradiction_violoations", 0)
        
        # Soft constraints
        setattr(self, "group_limit_violations", 0)
        setattr(self, "classes_per_day_violations", 0)
