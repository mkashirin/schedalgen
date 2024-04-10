from textwrap import wrap
from typing import Dict, List, Tuple

from ._typing import SimultaneousClasses
from .problem import ScheduleProblem


class ScheduleProblemBenchmark:

    def __init__(
        self,
        hard_constraint_penalty: int,
        soft_constraint_penalty: int = 5,
        *,
        problem: ScheduleProblem = ScheduleProblem()
    ):
        self.hard_constraint_penalty = hard_constraint_penalty
        self.soft_constraint_penalty = soft_constraint_penalty

        self.problem = problem

    def get_cost(self):
        pass

    def count_multiple_teachers_violations(self):
        #                        --- TODO: ---
        # На основе функции `_collect_simultaneous_classes()` посчитайте 
        # количество пар, которые "ведут" одни и те же преподаватели.
        #
        #                        +++ Hint: +++
        # Используйте уже имеющиеся решения (типа `collection.Counter`).
        # Старайтесь использовать как можно меньше вложенных циклов!
        pass

    def count_classroom_purpose_violations(self):
        #                        --- TODO: ---
        # На основе функции `_collect_simultaneous_classes()` посчитайте 
        # количество пар, которые "проходят" в аудиториях, которые не 
        # предназначены для данного типа пары (см README.md).
        #
        #                        +++ Hint: +++
        # Используйте уже имеющиеся решения (типа `collection.Counter`).
        # Старайтесь использовать как можно меньше вложенных циклов!
        pass

    def count_lecture_groups_number_violations(self):
        #                        --- TODO: ---
        # На основе функции `_collect_simultaneous_classes()` посчитайте 
        # количество лекций, на которых присутствовало групп больше, чем 
        # указано в `self.problem.groups_per_lecture`.
        #
        #                        +++ Hint: +++
        # Используйте уже имеющиеся решения (типа `collection.Counter`).
        # Старайтесь использовать как можно меньше вложенных циклов!
        pass

    def count_practice_groups_number_violations(self):
        #                        --- TODO: ---
        # На основе функции `_collect_simultaneous_classes()` посчитайте 
        # количество лекций, на которых присутствовало групп больше, чем 
        # указано в `self.problem.groups_per_practice`.
        #
        #                        +++ Hint: +++
        # Используйте уже имеющиеся решения (типа `collection.Counter`).
        # Старайтесь использовать как можно меньше вложенных циклов!
        pass

    def count_teachers_commons(self):
        #                        --- TODO: ---
        # На основе функции `_collect_simultaneous_classes()` посчитайте 
        # количество пар, которые "ведут" одни и те же преподаватели.
        #
        #                        +++ Hint: +++
        # Используйте уже имеющиеся решения (типа `collection.Counter`).
        # Старайтесь использовать как можно меньше вложенных циклов!
        pass

    def count_class_type_commons(self):
        #                        --- TODO: ---
        # На основе функции `_collect_simultaneous_classes()` посчитайте 
        # количество пар, в которых "проходят" и лекция, и практика.
        #
        #                        +++ Hint: +++
        # Используйте уже имеющиеся решения (типа `collection.Counter`).
        # Старайтесь использовать как можно меньше вложенных циклов!
        pass

    def _collect_simultaneous_classes(
        self, total_schedules: str 
    ) -> SimultaneousClasses:
        """Collects every class for each group that is being conducted.

        :parameter total_schedules: A string representing schedules for each 
            group.
            :type total_schedules: str

        :returns: List of lists of tuples. Each list contains classes that are 
            being conducted at the same date and time. Each nested list 
            represents a group. Single class is represented as tuple of three 
            integers. First element of the tuple stands for classroom, second 
            is for teacher and the third means class type (i.e. lecture or 
            practice).
            :rtype: SimultaneousClasses (look up the "_typing.py" file)
        """
        groups_dict = self._wrap_groups_dict(total_schedules)
        
        classes_per_group_range, simultaneous_classes = self._get_nested_list()
        for group_key in groups_dict:
            for class_string, classes_list in zip(
                groups_dict[group_key], classes_per_group_range
            ):
                class_string_decoded, _ = self.problem._decode_string(
                    class_string
                )
                simultaneous_classes[classes_list].append(class_string_decoded)
        return simultaneous_classes

    def _wrap_groups_dict(
        self, total_schedules: str
    ) -> Dict[str, Tuple[str, ...]]:
        schedules_sorted = self.problem._sort_by_groups(total_schedules)
        groups_dict_wrapped = self.problem._wrap_dict(
            schedules_sorted,
            self.problem.wrap_groups_every_chars,
            "group",
            self.problem.total_groups,
        )
        for group_key in groups_dict_wrapped:
            groups_dict_wrapped[group_key] = tuple(
                wrap(
                    groups_dict_wrapped[group_key],
                    self.problem.total_len_without_group,
                )
            )
        return groups_dict_wrapped
    
    def _get_nested_list(self) -> Tuple[range, List[List]]:
        classes_per_group_range = range(self.problem.classes_per_group)
        simultaneous_classes = [list() for _ in classes_per_group_range]
        classes_range_tuple = (classes_per_group_range, simultaneous_classes)
        return classes_range_tuple
