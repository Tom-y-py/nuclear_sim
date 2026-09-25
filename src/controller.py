# src/controller.py
from src.reactor import Reactor


class ReactorController:

    def __init__(self, reactor: Reactor):
        self.reactor = reactor

    def start(self):
        self.reactor.is_active = True
        self.reactor.control_rod_insertion = 40.0  # Withdraw rods to start

    def set_rods(self, percent: float):
        self.reactor.control_rod_insertion = max(0.0, min(100.0, percent))

    def set_coolant(self, flow: float):
        self.reactor.coolant_flow_rate = max(0.0, min(100.0, flow))

    def scram(self):
        self.reactor.control_rod_insertion = 100.0
        self.reactor.is_active = False