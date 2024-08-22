import pygame
import numpy as np
import configparser

# Read configuration from file
config = configparser.ConfigParser()
config.read('game_of_life_config.ini')

# Extract parameters
random_placement = config.getboolean('DEFAULT', 'random')
center_size = config.getint('DEFAULT', 'center_size')
config_grid_size = config.getint('DEFAULT', 'grid_size')
max_size = config.getint('DEFAULT', 'max_size')
initial_cell_size = config.getint('DEFAULT', 'initial_cell_size')
placements = config.get('DEFAULT', 'placements')
window_width = config.getint('DEFAULT', 'window_width')
window_height = config.getint('DEFAULT', 'window_height')

if '], [' in placements:
    # Cleaning the placements for multiple coordinate pairs
    placements = [p.strip().replace(' ', '') for p in placements.split('], [')]
    placements[0], placements[-1] = placements[0][1:], placements[-1][:-1]
else:
    placements = [placements.strip().replace('[', '').replace(']', '')]

# Initialize grid size
grid_size = 0

# Parse placements and determine grid size
def set_dynamic_size(placements):
    max_x, max_y = 0, 0  # Initialize max values

    for placement in placements:
        x, y = placement.split(',')
        x_max = max([int(p) for p in x.split(':')]) if ':' in x else int(x)
        y_max = max([int(p) for p in y.split(':')]) if ':' in y else int(y)

        max_x = max(max_x, x_max)
        max_y = max(max_y, y_max)

    # Create a square grid based on the max value, add 10 for padding
    return max(max_x, max_y) + 10

# Parse placements
def place(placements, grid):
    for placement in placements:
        x, y = placement.split(',')
        x_min, x_max = [int(p) for p in x.split(':')] if ':' in x else [int(x), int(x)]
        y_min, y_max = [int(p) for p in y.split(':')] if ':' in y else [int(y), int(y)]
        grid[y_min:y_max+1, x_min:x_max+1] = 1

# Initialize the grid with config-based placements and dynamic size or random initialization with config-based size
def initialize_grid(center_size, placements, random_placement):
    global grid_size
    if random_placement:
        grid_size = config_grid_size
        grid = np.zeros((grid_size, grid_size))
        center_start = (grid_size - center_size) // 2
        center_end = center_start + center_size
        grid[center_start:center_end, center_start:center_end] = np.random.choice(
            [0, 1], (center_size, center_size), p=[0.8, 0.2]
        )
    else:
        grid_size = set_dynamic_size(placements)
        grid = np.zeros((grid_size, grid_size))  # Use dynamic size
        place(placements, grid)

    return grid

# Function to update the grid based on the rules
def update_grid(grid):
    # Pad the grid with zeros for easier neighbor calculations
    padded_grid = np.pad(grid, ((1, 1), (1, 1)), mode='wrap')

    # Calculate the sum of live neighbors for each cell
    neighbors = (
        padded_grid[:-2, :-2] + padded_grid[:-2, 1:-1] + padded_grid[:-2, 2:] +
        padded_grid[1:-1, :-2] + padded_grid[1:-1, 2:] +
        padded_grid[2:, :-2] + padded_grid[2:, 1:-1] + padded_grid[2:, 2:]
    )

    # Apply the Game of Life rules
    birth = (neighbors == 3) & (grid == 0)
    survive = ((neighbors == 2) | (neighbors == 3)) & (grid == 1)

    # Update the grid
    grid[:] = birth | survive
    return grid

# Initialize Pygame
pygame.init()
grid = initialize_grid(center_size, placements, random_placement)
cell_size = initial_cell_size
screen = pygame.display.set_mode((window_width, window_height))  # Use config values

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Dragging variables
dragging = False
drag_start_x = 0
drag_start_y = 0
drag_offset_x = 0
drag_offset_y = 0

# Function to draw the grid
def draw_grid(grid, offset_x=0, offset_y=0):
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            color = WHITE if grid[i, j] == 1 else BLACK
            pygame.draw.rect(screen, color, ((j * cell_size) + offset_x, (i * cell_size) + offset_y, cell_size, cell_size))

def expand_grid(grid, amount):
    # Create a new grid with expanded dimensions
    new_size = min(grid.shape[0] + amount, max_size)
    new_grid = np.zeros((new_size, new_size))
    
    # Calculate the offset to center the old grid within the new grid
    offset = (new_size - grid.shape[0]) // 2
    new_grid[offset:offset + grid.shape[0], offset:offset + grid.shape[1]] = grid
    print(cell_size)
    return new_grid

def mouse_position_to_grid(mouse_x, mouse_y):
    grid_x = (mouse_x - drag_offset_x) // cell_size
    grid_y = (mouse_y - drag_offset_y) // cell_size
    return grid_x, grid_y

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                drag_start_x = event.pos[0] - drag_offset_x
                drag_start_y = event.pos[1] - drag_offset_y
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                drag_offset_x = event.pos[0] - drag_start_x
                drag_offset_y = event.pos[1] - drag_start_y
        elif event.type == pygame.MOUSEWHEEL:
            if event.y > 0:  # Scroll up (zoom in)
                # Calculate the mouse position
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x, grid_y = mouse_position_to_grid(mouse_x, mouse_y)

                cell_size = min(cell_size + 2, 50)  # Cap max cell size

                # Keep the zoom position fixed relative to the grid
                drag_offset_x -= (grid_x * 2)
                drag_offset_y -= (grid_y * 2)
            elif event.y < 0:  # Scroll down (zoom out)
                # Calculate the mouse position
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x, grid_y = mouse_position_to_grid(mouse_x, mouse_y)

                cell_size = max(cell_size - 2, 1)   # Cap min cell size

                # Keep the zoom position fixed relative to the grid
                drag_offset_x += (grid_x * 2)
                drag_offset_y += (grid_y * 2)

    # Check if expansion is needed (same as before)
    if np.any(grid[[0, -1], :]) or np.any(grid[:, [0, -1]]):
        if grid.shape[0] < max_size:
            grid = expand_grid(grid, 100)

    # Update the grid
    grid = update_grid(grid)

    # Draw the grid with offset
    screen.fill(BLACK)
    draw_grid(grid, drag_offset_x, drag_offset_y)

    pygame.display.flip()

pygame.quit()