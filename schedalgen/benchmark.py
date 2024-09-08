# pyright: reportOperatorIssue = false
# pyright: reportAttributeAccessIssue = false

from textwrap import wrap
from typing import Dict, List, Literal, Optional, Tuple

from ._typing import (
    ClassTuple,
    SimultaneousClasses,
    ValidClasses,
)
from .problem import Problem
from .utils import nested_list, wrap_dict


class ViolationsAdder:

    default_costs = {
        "zero_class_members": 1,
        "classroom_type": 1,
        "classroom_num_contr": 1,
        "multiple_teachers_contr": 1,
        "classroom_type_contr": 1,
        "teacher_contr": 1,
        "duplicate_groups": 1,
        "group_limit": 1,
        "classes_per_day": 1,
    }

    hard_constraints = [
        "zero_class_members",
        "classroom_type",
        "classroom_num_contr",
        "multiple_teachers_contr",
        "classroom_type_contr",
        "teacher_contr",
        "duplicate_groups",
    ]
    soft_constraints = ["group_limit", "classes_per_day"]

    _under = "_"
    _dunder = "__"
    _suffix = "cost"

    def __init__(self, costs: Dict[str, int] = default_costs) -> None:
        for attr in costs:
            value = costs[attr]
            setattr(self, attr + self._under + self._suffix, value)

    def reset_violation_attrs(self):
        to_reset = self.hard_constraints + self.soft_constraints
        for attr in to_reset:
            setattr(self, attr, 0)

    def sum_violations(self) -> int:
        overall_cost = 0
        for hard in self.hard_constraints:
            count = getattr(self, hard)
            cost = getattr(self, hard + self._under + self._suffix)
            overall_cost += count * cost
        for soft in self.soft_constraints:
            count = getattr(self, soft)
            cost = getattr(self, soft + self._under + self._suffix)
            overall_cost += count * cost

        return overall_cost


class Benchmark:
    """This class provides an interface for benchmarking the individuals.
    The working horse of Benchmark is the
    :method:`Benchmark.calculate_cost()` method.
    """

    def __init__(
        self,
        hard_penalty: int,
        soft_penalty: int = 5,
        classes_per_day_pref: range = range(2, 6),
        adder: ViolationsAdder = ViolationsAdder(),
        *,
        problem: Problem = Problem(),
    ) -> None:
        """This initializer sets the values for benchmarking parameters.

        :parameter hard_penalty: Hard constraint penalty
        multiplies the hard constraint violation sum by the factor specified.
        :type hard_penalty: :class:`int`
        :parameter soft_penalty: Soft constraint penalty does
        the same thing but for soft constraints.
        :type soft_penalty: :class:`int`

        :keyword classes_per_day_preference: The preferred range of classes
        per day.
        :type classes_per_day_preference: :class:`range`
        :keyword check_for_courses_and_directions: Defines whether or not to
        check for course and direction group ranges.
        :type check_for_courses_and_directions: :class:`bool`

        :returns: :data:`None`
        :rtype: :class:`NoneType`

        .. note:: See
        :method:`Benchmark.__set_violation_attributes()`
        for the list of all violations.
        """
        self.hard_penalty = hard_penalty
        self.soft_penalty = soft_penalty
        self.classes_preference = classes_per_day_pref
        self._part_num_index = 0
        self._part_list_index = 1

        self.adder = adder
        self.problem = problem
        self._cond_checker = _CondChecker(self.problem)
        self._collector = _Collector(self.problem)

    def calculate_cost(self, total_shedules: str) -> int:
        """This function calculates the cost of a single individual.

        :parameter total_schedules: String that constains all the schedules
        for each group (this is actually called individual).
        :type total_schedules: :class:`str`

        :returns: Cost of a single individual.
        :rtype: :class:`int`
        """
        self.adder.reset_violation_attrs()

        simult_classes = self._collector.collect_simult_classes(total_shedules)
        for groups_list in simult_classes:
            group_valid_classes = dict()
            for group_num, class_tuple in enumerate(groups_list):
                classroom_num, _, class_type = class_tuple
                group_num += 1
                if len(group_valid_classes.items()) < 1:
                    default: List[int | List[int]] = [1, [group_num]]
                    group_valid_classes[class_tuple] = default
                    continue

                continue_cond = (
                    True
                    if self.invalid_class_tuple_chars(class_tuple)
                    or not self.valid_classroom_type(classroom_num, class_type)
                    else False
                )
                if continue_cond:
                    continue
                elif group_valid_classes.get(class_tuple, False):
                    self.update_valid_class_value(
                        group_valid_classes,
                        group_num,
                        class_tuple,
                    )
                    continue
                self.update_valid_classes(
                    group_valid_classes, group_num, class_tuple
                )
        self.count_classes_per_day(total_shedules)

        overall_cost = self.adder.sum_violations()
        return overall_cost

    def report_violations(self) -> str:
        """This method returns a violations report in a form of string."""
        adder = self.adder
        report = f""" 
    Hard constraint violations:
        Zero class members: {str(adder.zero_class_members)} 
        Classroom type: {str(adder.classroom_type)}
        Classroom number contradiction: {str(adder.classroom_num_contr)}
        Multiple teachers contradiction: {str(adder.multiple_teachers_contr)}
        Classroom type contradiciton: {str(adder.classroom_type_contr)}
        Teacher contradiction: {str(adder.teacher_contr)}
    Soft constraint violations:
        Group limit: {str(adder.group_limit)}
        Classes per day: {str(adder.classes_per_day)} 
"""
        return report

    def update_valid_class_value(
        self,
        valid_classes: ValidClasses,
        group_num: int,
        class_tuple: ClassTuple,
    ) -> bool:
        """This method adds up to the valid class setting if the conditions
        below are satisfied.

        :parameter valid_classes: The dictionary of classes that passed all
        the validation checks
        (see :method:`Benchmark._add_valid_class()` method).
        :type valid_classes: :class:`ValidClasses`
        (see :module:`_typing.py` module)
        :parameter group_number: Number of the group to be put in the
        dictionary. :type group_number: :class:`int`
        :parameter class_tuple: Class setting to be additionally validated.
        :type class_tuple: :class:`ClassTuple`
        (see :module:`_typing.py` module)

        :returns: Whether the group has been added to the class setting
        or not.
        :rtype: :class:`bool`
        """
        parts_num, valid_class_parts = valid_classes[class_tuple]
        self._cond_checker.set_checker_attrs(
            "part", class_tuple, valid_classes=valid_classes
        )
        # fmt: off
        over_lecture_parts_num = self._cond_checker.check_parts_num(
            self.problem.lecture_int_code, parts_num  # pyright: ignore[reportArgumentType]
        )
        over_practice_parts_num = self._cond_checker.check_parts_num(
            self.problem.practice_int_code, parts_num  # pyright: ignore[reportArgumentType]
        )
        # fmt: on

        if over_lecture_parts_num or over_practice_parts_num:
            self.adder.group_limit += 1
            return False
        elif group_num in valid_class_parts:
            self.adder.duplicate_groups += 1
            return False

        valid_classes[class_tuple][self._part_num_index] += 1
        valid_classes[class_tuple][self._part_list_index] += [group_num]
        return True

    def valid_classroom_type(self, classroom: int, class_type: int) -> bool:
        """This method detects whether or not the classroom number matches
        its type (i.e. lecture or classroom).

        :parameter classroom: Classroom number in the class setting.
        :type classroom: :class:`int`
        :parameter class_type: Class type in the class setting.
        :type class_type: :class:`int`

        :returns: Whether or not the classroom number matches its type.
        :rtype: :class:` bool`
        """
        lecture_classroom_mismatch = (
            classroom in self.problem.lecture_classrooms
            and class_type != self.problem.lecture_int_code
        )
        practice_classroom_mismatch = (
            classroom in self.problem.practice_classrooms
            and class_type != self.problem.practice_int_code
        )
        if not lecture_classroom_mismatch:
            return True
        elif not practice_classroom_mismatch:
            return True

        self.classroom_type += 1
        return False

    def update_valid_classes(
        self,
        valid_classes: ValidClasses,
        group_num: int,
        class_tuple: ClassTuple,
    ) -> None:
        """This method adds class to the valid classes dictionary if it's
        setting satisfies the conditions provdied below.

        :parameter valid_classes: The dictionary of classes that passed all
        the validation checks
        (see :method:`Benchmark._add_valid_class()` method).
        :type valid_classes: :class:`ValidClasses`
        :parameter group_number: Group number of the to be appended to the
        attendance list.
        :type group_number: :class:`int`
        :parameter class_tuple: Class setting to be added to valid classes.
        :type: :class:`ClassTuple` (see :module:`_typing.py` module)

        :returns: None.
        :rtype: :class:`NoneType`
        """
        classroom_num_pos = (True, False, False)
        multiple_teachers_pos = (False, True, False)
        classroom_type_pos = (False, False, True)
        teacher_pos = (True, False, True)
        
        for class_key in list(valid_classes):
            self._cond_checker.set_checker_attrs(
                "contrs", class_tuple, class_key=class_key
            )

            if self._cond_checker.check_contr_cond(classroom_num_pos):
                self.adder.classroom_num_contr += 1
            if self._cond_checker.check_contr_cond(multiple_teachers_pos):
                self.adder.multiple_teachers_contr += 1
            if self._cond_checker.check_contr_cond(classroom_type_pos):
                self.adder.classroom_type_contr += 1
            if self._cond_checker.check_contr_cond(teacher_pos):
                self.adder.teacher_contr += 1
        else:
            default: List[int | List[int]] = [1, [group_num]]
            valid_classes[class_tuple] = default

    def invalid_class_tuple_chars(self, class_tuple: ClassTuple) -> bool:
        """This method detects if the class setting provided has invalid zeros
        in it (i.e. setting like :code:`(52, 0, 1)` is considered invalid)

        :parameter class_tuple: Class setting to be added to valid classes.
        :type: :class:`ClassTuple` (see :module:`_typing.py` module)

        :returns: Whether or not the setting provided has invalid zeros in it.
        :rtype: :class:`bool`
        """
        *classroom_and_teacher, class_type = class_tuple
        if classroom_and_teacher.count(0) == 1 or (
            not any(classroom_and_teacher) and class_type != 0
        ):
            self.adder.zero_class_members += 1
            return True
        return False

    def count_classes_per_day(self, total_schedules: str) -> None:
        """This method counts how many classes been given each day and
        calculates the cost based on the
        :attribute:`Benchmark.classes_per_day_preference`
        attribute.

        :parameter total_schedules: A string representing schedules for each
        group.
        :type total_schedules: :class:`str`

        :returns: None.
        :rtype: :class:`NoneType`
        """
        classes_per_day = self._collector.collect_classes_per_day(
            total_schedules
        )
        # fmt: off
        mapped_to_violations = (
            map(
                lambda class_num: (
                    1 if class_num in self.classes_preference else 0
                ),
                classes_per_day[group_number],  # pyright: ignore[reportCallIssue, reportArgumentType]
            )
            for group_number, _ in enumerate(classes_per_day)
        )
        # fmt: on
        for viols in mapped_to_violations:
            self.adder.classes_per_day += sum(viols)


class _Collector:

    def __init__(self, problem: Problem) -> None:
        self.problem = problem

    def collect_classes_per_day(self, total_schedules: str) -> List[List[int]]:
        """This method analyses information about classes to be given each
        day to pass the resulting collection to the
        :method:`Benchmark._count_classes_per_day_violations()`
        which then calculates the cost for violations.

        :parameter total_schedules: String representing schedules for each
        group.
        :type total_schedules: :class:`str`

        :returns: List of lists of integers. Each list contains integers.
        :rtype: :class:`List[List[int]]`
        """
        _, classes_per_day_by_group = nested_list(self.problem.total_groups)
        schedules_table = self.problem._wrap_table(total_schedules)
        for i, group_number in enumerate(schedules_table):
            for week_number in schedules_table[group_number]:
                for day_number in schedules_table[group_number][week_number]:
                    self._append_counter(
                        classes_per_day_by_group,
                        schedules_table[group_number][week_number],
                        day_number,
                        group_index=i,
                    )
        return classes_per_day_by_group

    def collect_simult_classes(
        self, total_schedules: str
    ) -> SimultaneousClasses:
        """Collects every class for each group that is being conducted.

        :parameter total_schedules: String representing schedules for each
        group.
        :type total_schedules: :class:`str`

        :returns: List of lists of tuples. Each list contains classes to be
        given at the same date and time. Single class is represented as
        tuple of three integers. First element of the tuple stands for
        classroom, second is for teacher and the third means class type
        (i.e. lecture or practice).
        :rtype: :class:`SimultaneousClasses`
        (look up the :module:`_typing.py` file)
        """
        groups_dict = self._wrap_groups_dict(total_schedules)

        classes_per_group_range, simultaneous_classes = nested_list(
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

    def _append_counter(
        self,
        classes_per_day_by_group: List[List[int]],
        schedules_table_week_depth: Dict[str, Dict[str, Dict[str, str]]],
        day_number: str,
        *,
        group_index: int,
    ) -> None:
        class_per_day_counter = 0
        for class_number in schedules_table_week_depth[day_number]:
            class_dict = schedules_table_week_depth[day_number][class_number]
            class_values = tuple(class_dict.values())
            class_per_day_counter += 1 if 0 not in class_values[:-1] else -1
        classes_per_day_by_group[group_index].append(class_per_day_counter)

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


class _CondChecker:

    def __init__(
        self,
        problem: Problem,
    ) -> None:
        self.problem = problem

    def set_checker_attrs(
        self,
        check_type: Literal["contrs", "part"],
        class_tuple: ClassTuple,
        *,
        class_key: Optional[ClassTuple] = None,
        valid_classes: Optional[ValidClasses] = None,
    ) -> None:
        match check_type:
            case "contrs":
                if class_key is None:
                    raise ValueError("class key can not be unbound if contrs")

                self.class_tuple = class_tuple
                self.class_key = class_key
            case "part":
                if valid_classes is None:
                    raise ValueError(
                        "valid classes can not be unbound if part"
                    )

                *_, self.class_type = class_tuple
                # fmt: off
                self.parts_num, _ = valid_classes[class_tuple]  # pyright: ignore[reportOptionalSubscript]
                # fmt: on
        self.mode = check_type

    def check_parts_num(self, int_code: int, parts_limit: int) -> bool:
        result = self.class_type == int_code and self.parts_num > parts_limit
        return result

    def check_contr_cond(
        self,
        not_pos: Tuple[bool, bool, bool],
    ) -> bool:
        if self.mode != "contrs":
            raise ValueError("can not check for contrs with part attrs")
        conds = (
            key != tup if not_pos else key == tup
            for key, tup, not_pos in zip(
                self.class_key, self.class_tuple, not_pos
            )
        )
        result = all(tuple(conds))
        return result
