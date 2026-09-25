# main.py
import sys
import time
import threading

from src.controller import ReactorController
from src.reactor import Reactor
from src.simulation import PhysicsSimulation


def simulation_worker(
    sim: PhysicsSimulation, stop_event: threading.Event, tick_rate_sec: float = 1.0
):
    """Runs in background, updating physics every tick."""
    while not stop_event.is_set():
        sim.tick(dt=tick_rate_sec)
        time.sleep(tick_rate_sec)

def print_status(reactor: Reactor):
    """Print clean current telemetry without interrupting input prompts."""
    status = "ONLINE" if reactor.is_active else "OFFLINE"
    print(f"\n--- [{reactor.name} TELEMETRY | Status: {status}] ---")
    print(f"  Temperature : {reactor.temperature_c:6.2f} °C")
    print(f"  Pressure    : {reactor.pressure_bar:6.2f} bar")
    print(f"  Control Rods: {reactor.control_rod_insertion:6.1f} %")
    print(f"  Coolant Flow: {reactor.coolant_flow_rate:6.1f} %")
    print(f"  Fuel Level  : {reactor.fuel_level_percent:6.2f} %")
    if reactor.alarms:
        print(f"  Alarms      : {', '.join(reactor.alarms)}")
    print("------------------------------------------\n")

def print_help():
    print("""
Available Commands:
  start           - Power on the reactor
  scram           - Emergency full insertion / shutdown
  rods <0-100>    - Set control rod insertion (0=full power, 100=submerged)
  coolant <0-100> - Set coolant flow percentage
  status          - Show current reactor telemetry
  help            - Show this command list
  exit / quit     - Shutdown and exit
""")

def cli_loop(reactor: Reactor, controller: ReactorController):
    print_help()

    while True:
        try:
            raw_input = input("> ").strip()
            if not raw_input:
                continue

            parts = raw_input.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in ("exit", "quit"):
                print("[*] Exiting control interface...")
                controller.scram()
                break
            elif cmd == "start":
                controller.start()
                print("[+] Reactor started.")
            elif cmd == "scram":
                controller.scram()
                print("[ALERT] SCRAM executed!")
            elif cmd == "status":
                print_status(reactor)
            elif cmd == "help":
                print_help()
            elif cmd == "rods":
                if not args:
                    print("[!] Usage: rods <0-100>")
                    continue
                try:
                    val = float(args[0])
                    controller.set_rods(val)
                    print(f"[*] Rods adjusted to {val}%.")
                except ValueError:
                    print("[!] Invalid number for rods.")
            elif cmd == "coolant":
                if not args:
                    print("[!] Usage: coolant <0-100>")
                    continue
                try:
                    val = float(args[0])
                    controller.set_coolant(val)
                    print(f"[*] Coolant set to {val}%.")
                except ValueError:
                    print("[!] Invalid number for coolant.")
            else:
                print(f"[!] Unknown command: '{cmd}'. Type 'help' for options.")

        except (KeyboardInterrupt, EOFError):
            print("\n[*] Interrupted by user.")
            controller.scram()
            break

def main() -> int:
    reactor = Reactor(name="Unit-1")
    sim = PhysicsSimulation(reactor)
    controller = ReactorController(reactor)

    # Event flag to gracefully terminate the background thread
    stop_sim_event = threading.Event()

    # Start background physics thread as a daemon
    sim_thread = threading.Thread(
        target=simulation_worker,
        args=(sim, stop_sim_event, 0.5),  # 0.5s per tick
        daemon=True,
    )
    sim_thread.start()
    print("[*] Simulation background engine initialized.")

    try:
        # Run CLI in the foreground
        cli_loop(reactor, controller)
    finally:
        # Ensure cleanup and thread shutdown
        stop_sim_event.set()
        sim_thread.join(timeout=1.0)
        print("[+] Simulation cleanly stopped.")

    return 0

if __name__ == "__main__":
    sys.exit(main())