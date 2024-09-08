from typing import Dict, List, Optional, Tuple

ClassTuple = Tuple[int, int, int]
ClassDecodings = Tuple[Tuple[int, int, int], Dict[str, int]]
SchedulesTable = Dict[str, Dict[str, Dict[str, Dict[str, Dict[str, str]]]]]
SimultaneousClasses = List[List[ClassTuple]]
ValidClasses = Dict[ClassTuple, List[int | List[int]]]

Individual = Tuple[str, Optional[int]]
Population = List[Individual]
