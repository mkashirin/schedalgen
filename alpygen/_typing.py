from typing import Dict, List, Tuple

SchedulesTable = Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, str]]]]]
ClassDecodings = Tuple[Tuple[int, int, int], Dict[str, int]]
SimultaneousClasses = List[List[Tuple[int, int, int]]]
