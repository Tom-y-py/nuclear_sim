from dataclasses import dataclass, replace, field
import scipy.stats as stats
import math
import random
import pygame

pygame.init()
pygame.font.init()

# VARIABLES

Radius = 20
SCALE = 300.0 / Radius
simulation_running = True

init_ammount = 1000
current_gen = 0

max_gens = 50
gen_ammount = 50

N_target = 1000

neutrons = []
fission_bank = []
completed_tracks = []

multiplication_factors =[]

# Fonts & Colors

FONT = pygame.font.SysFont("Consolas", 16)
FONT_BOLD = pygame.font.SysFont("Consolas", 18, bold=True)

COLOR_BG = (15, 15, 22)
COLOR_CORE = (70, 130, 180)
COLOR_TEXT = (220, 220, 220)
COLOR_FISSION = (255, 215, 0)
COLOR_CAPTURED = (50, 150, 255)
COLOR_LEAKED = (90, 90, 100)
COLOR_TRACK = (40, 40, 50)

# PYGAME INIT

WIDTH, HEIGHT = 900, 800

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Monte Carlo Reactor Physics Simulator")
clock = pygame.time.Clock()

# PHYSICS VARIABLES

uran_density = 10.96
avogadro_const = 6.022*1e23

u235_mol_weight = 235.04
u238_mol_weight = 238.05

u235_enrichment = 0.05
u238_enrichment = 0.95

u235_micro_cross_section = 680*1e-24
u238_micro_cross_section = 11.8*1e-24 

u235_atomic_density = (uran_density*u235_enrichment*avogadro_const)/u235_mol_weight
u238_atomic_density = (uran_density*u238_enrichment*avogadro_const)/u238_mol_weight

#u235_macro_cross = u235_atomic_density * u235_micro_cross_section
#u238_macro_cross = u238_atomic_density * u238_micro_cross_section

#total_macro_cross_section = u235_macro_cross + u238_macro_cross

# SIGMA NOTATIONS

# Propability per centimeter of absorption by fissile nucleus of u235, splitting it apart and realasing 2-3 new neutrons
sigma_f = u235_atomic_density * (585 * 1e-24)
# Propability per centimeter of absorption by nucleus (e.g. u238 + n = u239), without causing fission, neutron is destroyed
sigma_a = u235_atomic_density * (99 * 1e-24) + u238_atomic_density * (2.7 * 1e-24)
# Propability per centimeter of bouncing off nucleus without being absorbed, kinetic energy and trajectory chenges, neutron survives.
sigma_s = u235_atomic_density * (15 * 1e-24) + u238_atomic_density * (9.0 * 1e-24)
# Sum of all possible interactions propabilities
sigma_t = sigma_f + sigma_a + sigma_s

# NEUTRON OBJECT

@dataclass
class Neutron:
    x: float
    y: float
    dir_angle: float
    status: str
    path: list = field(default_factory=list)

# NEUTRON SPAWN

def neutron_spawn(Radius: float) -> Neutron:
    dir_angle = random.uniform(0,2*math.pi)

    pos_angle = random.uniform(0,2*math.pi)
    r = Radius * math.sqrt(random.uniform(0,1))
    
    n = Neutron(
        x = r * math.cos(pos_angle),
        y = r * math.sin(pos_angle),
        dir_angle = dir_angle,
        status = "ALIVE"
    )

    n.path.append((n.x, n.y))
    return n

def neutron_spawn_fission(x: float, y: float) -> Neutron:
    n = Neutron(
        x = x,
        y = y,
        dir_angle = random.uniform(0,2*math.pi),
        status = "ALIVE"
    )

    n.path.append((x, y))
    return n

# NEUTRON PROPERTIES FUNCTIONS

def distance_calc(sigma_t) -> float:
    xi = random.uniform(1e-9, 1.0)
    d = -1*(math.log(xi)/sigma_t)
    return d

def boundry_check(neutron: Neutron, radius) -> bool:
    r_pos = math.sqrt(math.pow(neutron.x, 2) + math.pow(neutron.y, 2))

    if r_pos > radius:
        neutron.status = 'LEAKED'
        return False
    else:
        return True

def new_position(neutron: Neutron, d):
    neutron.x = neutron.x + d * math.cos(neutron.dir_angle)
    neutron.y = neutron.y + d * math.sin(neutron.dir_angle)
    neutron.path.append((neutron.x, neutron.y))

def sample_interaction(sigma_s, sigma_a, sigma_f) -> str:
    sigma_t = sigma_s + sigma_a + sigma_f
    xi = random.uniform(0, 1)

    # Cumulative probability intervals:
    # [0, P_scatter) -> SCATTER
    # [P_scatter, P_scatter + P_capture) -> CAPTURE
    # [P_scatter + P_capture, 1.0] -> FISSION

    p_scatter = sigma_s / sigma_t
    p_capture = (sigma_s + sigma_a) / sigma_t

    if xi < p_scatter:
        return 'SCATTER'
    elif xi < p_capture:
        return 'CAPTURED'
    else:
        return 'FISSION'

def track_neutron(neutron: Neutron, radius, sigma_s, sigma_a, sigma_f, fission_bank):
    while neutron.status == 'ALIVE':
        d = distance_calc(sigma_t)
        
        new_position(neutron, d)

        if not boundry_check(neutron, radius):
            break
        else:
            new_status= sample_interaction(sigma_s, sigma_a, sigma_f)
            if new_status == 'SCATTER':
                neutron.dir_angle = random.uniform(0,2*math.pi)
            elif new_status == 'CAPTURED':
                neutron.status = new_status
                break
            elif new_status == 'FISSION':
                neutron.status = new_status

                rand = random.randrange(2,4)
                for i in range(rand):
                    fission_bank.append(neutron_spawn_fission(neutron.x, neutron.y))
                break

button_rect = pygame.Rect(650, 720, 200, 45)
def step_generation():
    global current_gen, neutrons, last_stats, completed_tracks
    fission_bank = []

    for n in neutrons:
        track_neutron(n, Radius, sigma_s, sigma_a, sigma_f, fission_bank)

    completed_tracks = neutrons

    n_fission = sum(1 for n in neutrons if n.status=='FISSION')
    n_captured = sum(1 for n in neutrons if n.status=='CAPTURED')
    n_leaked = sum(1 for n in neutrons if n.status=='LEAKED')
    k_eff = len(fission_bank)/N_target

    last_stats = {
        "fission": n_fission,
        "captured": n_captured,
        "leaked": n_leaked,
        "keff": k_eff
    }
    multiplication_factors.append(k_eff)

    if len(fission_bank) > 0:
        neutrons = [replace(n, path=[(n.x, n.y)]) for n in random.choices(fission_bank, k=N_target)]
        current_gen += 1
    else:
        print("Neutron chain reaction terminated.")




# SIMULATION

neutrons = [neutron_spawn(Radius) for i in range(N_target)]
last_stats = {"fission": 0, "captured": 0, "leaked": 0, "keff": 0.0}

# ANALYTICS


#del multiplication_factors[:9]
#k_eff_mean = sum(multiplication_factors)/len(multiplication_factors)

#sem = stats.sem(multiplication_factors)

# VISUALISATION

step_generation()

while simulation_running:
    # Process player inputs.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            simulation_running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                step_generation()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):
                step_generation()

    screen.fill(COLOR_BG)
    core_center = (400,400)
    pygame.draw.circle(screen, COLOR_CORE, core_center, int(Radius*SCALE), 2)

    for n in completed_tracks:
        screen_coords = [(int(x * SCALE + core_center[0]), int(y * SCALE + core_center[1])) for (x,y) in n.path]

        if len(screen_coords) > 1:
            pygame.draw.lines(screen, COLOR_TRACK, False, screen_coords, 1)

        end_x, end_y = screen_coords[-1]
        if n.status == 'FISSION':
            pygame.draw.circle(screen, COLOR_FISSION, (end_x, end_y), 3)
        elif n.status == 'CAPTURED':
            pygame.draw.circle(screen, COLOR_CAPTURED, (end_x, end_y), 2)
        elif n.status == 'LEAKED':
            pygame.draw.circle(screen, COLOR_LEAKED, (end_x, end_y), 1)

    info_lines = [
        f"Generation:     {current_gen}",
        f"k_eff:          {last_stats['keff']:.4f}",
        f"Fissions:       {last_stats['fission']}",
        f"Captures:       {last_stats['captured']}",
        f"Leakages:       {last_stats['leaked']}",
        f"Target Source:  {N_target}",
    ]

    for idx, line in enumerate(info_lines):
        txt_surf = FONT.render(line, True, COLOR_TEXT)
        screen.blit(txt_surf, (20, 20 + idx* 24))

    mouse_pos = pygame.mouse.get_pos()
    btn_color = (0, 160, 100) if button_rect.collidepoint(mouse_pos) else (0, 120, 75)
    pygame.draw.rect(screen, btn_color, button_rect, border_radius=6)

    btn_text = FONT_BOLD.render("Next Gen [SPACE]", True, (255, 255, 255))
    text_pos = btn_text.get_rect(center=button_rect.center)
    screen.blit(btn_text, text_pos)

    pygame.display.flip()
    clock.tick(30)

pygame.quit()



#DEBUG
#print(len(neutrons))
#print(len(fission_bank))

"""
total1 = sum(1 for n in neutrons if n.status in "CAPTURED")
total2 = sum(1 for n in neutrons if n.status in "FISSION")
total3 = sum(1 for n in neutrons if n.status in "ALIVE")
total4 = sum(1 for n in neutrons if n.status in "SCATTER")
total5 = sum(1 for n in neutrons if n.status in "LEAKED")

print(f"captured:{total1}, fission:{total2}, alive:{total3}, scatter:{total4}, leaked:{total5}")

total1a = sum(1 for n in fission_bank if n.status in "CAPTURED")
total2a = sum(1 for n in fission_bank if n.status in "FISSION")
total3a = sum(1 for n in fission_bank if n.status in "ALIVE")
total4a = sum(1 for n in fission_bank if n.status in "SCATTER")
total5a = sum(1 for n in fission_bank if n.status in "LEAKED")

print(f"captured:{total1a}, fission:{total2a}, alive:{total3a}, scatter:{total4a}, leaked:{total5a}")

print(multiplication_factors)
print(f"Multiplication coeficient mean: {k_eff_mean}")
print(f"Standard Error: {sem}")
"""


# ERROR MEMENTO

"""Mutable Object Reference Bug"""

# Problem
#
# random.choices(population, k) samples with replacement. 
# For custom objects (like a @dataclass), Python copies the memory reference (pointer),
# not the object itself. Multiple entries in the new list point to the exact same object.
# 
# Consequence
#
# 1. If a particle is selected multiple times, the first iteration processes it, triggers fission,
# and permanently changes its state attribute (status = 'FISSION').
# 
# 2. Subsequent iterations process the same object. The physics loop condition (while status == 'ALIVE')
# instantly evaluates to False.
#
# 3. The particle skips tracking and fails to spawn new neutrons, but your final analytics still count it as a fission event.
# This skews calculations and artificially depresses the neutrons-per-fission ratio below the physical minimum.
#
# Solution
# When sampling mutable agents or particles, explicitly clone each selection to ensure independent object states in memory.
#
# from dataclasses import replace

# WRONG: Copies references only
# neutrons = random.choices(fission_bank, k=N_target)

# CORRECT: Creates unique object instances
# neutrons = [replace(n) for n in random.choices(fission_bank, k=N_target)]
#
# Personal comment
# Nice showcase of why human intuition and observance is still a undeniable advantage compared to AI.
# First when data were presented to AI, it returned positive feedback, and didn't identify any problem, even when given code.
# Only way to discover this problem was to actually understand code and data shown. Thus creating a need for human to work manually.