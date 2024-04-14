from textwrap import wrap
from typing import Any, Dict, List, Tuple


def format_binary(number: int, n_bits: int) -> str:
    formatted: str = format(number, "0" + str(n_bits) + "b")
    return formatted


def get_nested_list(n_lists: int) -> Tuple[range, List[List]]:
    classes_per_group_range = range(n_lists)
    simultaneous_classes = (list() for _ in classes_per_group_range)
    classes_range_tuple: Tuple[range, List[List]] = (
        classes_per_group_range,
        list(simultaneous_classes),
    )
    return classes_range_tuple


def wrap_dict(
    to_wrap: str,
    wrap_every_chars: int,
    key_name: str,
    strings_number: int,
) -> Dict[str, Any]:
    strings_wrapped = tuple(wrap(to_wrap, wrap_every_chars))
    strings_wrapped_dict: Dict[str, Any] = {
        "{}-{}".format(key_name, key + 1): val
        for key, val in zip(range(strings_number), strings_wrapped)
    }
    return strings_wrapped_dict


def wrap_dict_cycle(
    dict_to_wrap: Dict[str, Any],
    wrap_every_chars: int,
    key_name: str,
    items_number: int,
) -> Dict[str, Any]:
    for dict_key in dict_to_wrap:
        dict_to_wrap[dict_key] = wrap_dict(
            dict_to_wrap[dict_key],
            wrap_every_chars,
            key_name,
            items_number,
        )
    return dict_to_wrap
