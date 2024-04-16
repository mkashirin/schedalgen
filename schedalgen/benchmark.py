# pyright: reportOperatorIssue = false
# pyright: reportAttributeAccessIssue = false

from textwrap import wrap
from typing import Dict, Tuple

from ._typing import ClassTuple, SimultaneousClasses, ValidClasses
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

        # Hard constraints
        self.zero_class_members_violations = 0
        self.classroom_type_violations = 0
        self.classroom_number_contradiction_violations = 0
        self.multiple_teachers_contradiction_violations = 0
        self.classroom_type_contradiction_violations = 0
        self.teacher_contradiction_violations = 0

        # Soft constraints
        self.group_limit_violations = 0

    def get_cost(self, total_shedules: str) -> int:
        simultaneous_classes = self._collect_simultaneous_classes(
            total_shedules
        )
        valid_classes = dict()
        for groups_list in simultaneous_classes:
            for group_number, class_tuple in enumerate(groups_list):
                group_number += 1
                classroom, class_type = class_tuple[0], class_tuple[2]
                if self._has_invalid_zeros(
                    class_tuple
                ) or self._is_invalid_classroom_type(
                    classroom,
                    class_type,
                ):
                    continue
                elif len(valid_classes.items()) < 1:
                    valid_classes[class_tuple] = [1, [group_number]]
                    continue
                elif valid_classes.get(class_tuple, False):
                    self._add_if_got(
                        valid_classes,
                        group_number,
                        class_tuple,
                    )
                    continue

                self._add_valid_class(valid_classes, group_number, class_tuple)

        hard_constraint_violations_cost = self.hard_constraint_penalty * (
            self.zero_class_members_violations
            + self.classroom_type_violations
            + self.classroom_number_contradiction_violations
            + self.multiple_teachers_contradiction_violations
            + self.classroom_type_contradiction_violations
            + self.teacher_contradiction_violations
        )
        soft_constraint_violations_cost = (
            self.group_limit_violations * self.soft_constraint_penalty
        )
        overall_cost = (
            hard_constraint_violations_cost + soft_constraint_violations_cost
        )
        return overall_cost

    def _add_if_got(
        self,
        valid_classes: ValidClasses,
        group_number: int,
        class_tuple: ClassTuple,
    ) -> bool:
        if (
            not class_tuple[2] != 1
            and valid_classes[class_tuple][0]
            <= self.problem.groups_per_practice
        ) or (
            not class_tuple[2] != 0
            and valid_classes[class_tuple][0]
            <= self.problem.groups_per_lecture
        ):
            valid_classes[class_tuple][0] += 1
            valid_classes[class_tuple][1] += [group_number]
            return True
        self.group_limit_violations += 1
        return False

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
        else:
            return False

    def count_classes_per_day(self):
        #                        --- TODO: ---
        # На основе функции `_collect_simultaneous_classes()` проверьте, чтобы
        # количество пар в день не было меньше двух и не превышало пяти.
        #
        #                        +++ Hint: +++
        # Используйте уже имеющиеся решения (типа `collections.Counter`).
        # Старайтесь использовать как можно меньше вложенных циклов!

        pass

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
        # schedules_sorted = self.problem.sort_by_groups(total_schedules)
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
