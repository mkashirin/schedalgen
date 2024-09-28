from textwrap import wrap
from typing import Any, Dict, List, Tuple

from ._typing import Individual, Population


def format_binary(num: int, n_bits: int) -> str:
    formatted: str = format(num, "0" + str(n_bits) + "b")
    return formatted


def nested_list(n_lists: int) -> Tuple[range, List[List]]:
    classes_per_group_range = range(n_lists)
    simult_classes = [list() for _ in classes_per_group_range]
    classes_range_tuple: Tuple[range, List[List]] = (
        classes_per_group_range,
        simult_classes,
    )
    return classes_range_tuple


def wrap_dict(
    to_wrap: str,
    wrap_every_chars: int,
    key_name: str,
    strings_num: int,
) -> Dict[str, Any]:
    strings_wrapped = tuple(wrap(to_wrap, wrap_every_chars))
    strings_wrapped_dict: Dict[str, Any] = {
        "{}-{}".format(key_name, key + 1): val
        for key, val in zip(range(strings_num), strings_wrapped)
    }
    return strings_wrapped_dict


def wrap_dict_cycle(
    dict_to_wrap: Dict[str, Any],
    wrap_every_chars: int,
    key_name: str,
    items_num: int,
) -> Dict[str, Any]:
    for dict_key in dict_to_wrap:
        dict_to_wrap[dict_key] = wrap_dict(
            dict_to_wrap[dict_key],
            wrap_every_chars,
            key_name,
            items_num,
        )
    return dict_to_wrap


def invalid_individ_values(
    population: Population,
) -> Tuple[str, ...]:
    invalid_ind_values = tuple(
        (val for val, cost in population if cost is None)
    )
    return invalid_ind_values


def invalid_individ_positions(
    population: Population,
) -> Tuple[int, ...]:
    invalid_ind_pos = tuple(
        (pos for pos, (_, cost) in enumerate(population) if cost is None)
    )
    return invalid_ind_pos


def blank_individs_list(base_on: Tuple[str, ...]) -> List[Individual]:
    blank_ind: Individual = ("", None)
    blank_list: List[Individual] = [blank_ind for _ in enumerate(base_on)]
    return blank_list
