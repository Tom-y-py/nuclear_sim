# src/simulation.py
from src.reactor import Reactor

class PhysicsSimulation:
    def __init__(self, reactor: Reactor):
        self.reactor = reactor

    def tick(self, dt: float = 1.0):
        if not self.reactor.is_active:
            self._apply_passive_cooling(dt)
            return

        self._update_reaction(dt)
        self._update_pressure(dt)
        self._check_safety_limits()

    def _update_reaction(self, dt: float):
        r = self.reactor

        reactivity = max(0.0, (100.0-r.control_rod_insertion )/ 100.0)

        heat_generated = reactivity * 25.0 * dt
        heat_dissipated = (
            (r.coolant_flow_rate / 100) * ((r.temperature_c - r.ambient_temp_c) * 0.05)
        )
        r.temperature_c = max(
            r.ambient_temp_c, r.temperature_c + heat_generated - heat_dissipated
        )

        # Fuel burn rate
        burn_rate = (reactivity * 0.01) * dt
        r.fuel_level_percent = max(0.0, r.fuel_level_percent - burn_rate)

    def _update_pressure(self, dt: float):
        r = self.reactor

        # Simplified ideal-gas-like pressure response to temperature
        target_pressure = 1.0 + (max(0.0, r.temperature_c - 100.0) * 0.4)

        # Smooth pressure adjustment toward target
        r.pressure_bar += (target_pressure - r.pressure_bar) * 0.2 * dt

    def _apply_passive_cooling(self, dt: float):
        r = self.reactor
        if r.temperature_c > r.ambient_temp_c:
            r.temperature_c -= (r.temperature_c - r.ambient_temp_c) * 0.02 * dt
        if r.pressure_bar > 1.0:
            r.pressure_bar -= (r.pressure_bar -1.0) *0.05 * dt

    def _check_safety_limits(self):
        r = self.reactor
        if (
            r.temperature_c > 350.0
            and "HIGH_TEMPERATURE_WARNING" not in r.alarms
        ):
            r.alarms.append("HIGH_TEMPERATURE_WARNING")