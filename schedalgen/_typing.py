from typing import Dict, List, Tuple

ClassTuple = Tuple[int, int, int]
ClassDecodings = Tuple[Tuple[int, int, int], Dict[str, int]]
SchedulesTable = Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, str]]]]]
SimultaneousClasses = List[List[Tuple[int, int, int]]]
ValidClasses = Dict[ClassTuple, int]
