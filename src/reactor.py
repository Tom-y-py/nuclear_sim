# src/reactor.py
from dataclasses import dataclass, field


@dataclass
class Reactor:
    name: str
    #max_output_mw: float
    coolant_type: str = "Water"

    # Operational state
    is_active: bool = False
    control_rod_insertion: float = 100.0 # 0% = max reaction, 100% = shutdown
    coolant_flow_rate: float = 50.0 # Liters/sec or %
    fuel_level_percent: float = 100.0


    # Dynamic physical state
    temperature_c: float = 25.0
    pressure_bar: float = 1.0
    
    # Constants & history
    ambient_temp_c: float = 25.0
    alarms: list[str] = field(default_factory=list)