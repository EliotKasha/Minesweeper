try:
    import pygame

except:
    import pip
    pip.main(["install", "pygame"])

    import pygame

import webbrowser
import random
import math

pygame.init()
pygame.font.init()
clock = pygame.time.Clock()

h = 800
w = h + 200
window = pygame.display.set_mode((w, h))

# Set icon
icon = pygame.image.load("MINE.png")
pygame.display.set_icon(icon)

# Settings
grid_size = 20  # Board size for both vertical and horizontal (WARNING: text may not show for very large board sizes)
bomb_rate = 1.25  # How dense the bombs are (WARNING: anything above about 2 can get borderline impossible)
fast = False  # Lowers render frequency for faster result
animate_flood = False  # Adds a little bit of animation when a "0" tile is explored [VISUAL ONLY]
darker_zeroes = True  # Makes tiles with 0 bombs around them appear a slightly darker blue [VISUAL ONLY]
fancy_bombs = True  # Adds special bomb image rather than a simple circle [VISUAL ONLY]

# Colors
black = (0, 0, 0)
white = (255, 255, 255)
grey = (223, 223, 223)
blue = (0, 0, 255)
blue_dark = (0, 0, 207)
red = (255, 0, 0)
green = (0, 255, 0)
gold = (218, 165, 32)

# Misc
num_colors = [blue_dark, (0, 255, 255), (63, 255, 63), (255, 0, 0), (238, 63, 238), (127, 0, 0), (255, 255, 0), (0, 0, 0), (127, 127, 127)]

sqsize = round(h / grid_size)
surrounding = [[1, 0], [-1, 0], [0, 1], [0, -1], [1, 1], [-1, -1], [-1, 1], [1, -1]]

bombs = round(grid_size * grid_size / 10 * bomb_rate)
b = pygame.transform.scale(icon, (sqsize - 1, sqsize - 1))

controls = ["Left Mouse: Uncover Tile", "Right Mouse: Mark Tile", "Space: Solve Game", "R: Reset Game"]

tile_font = pygame.font.SysFont("comicsans", round(h / 1.5 / grid_size))
font = pygame.font.SysFont("comicsans", 30)
font_small = pygame.font.SysFont("comicsans", 10)

class Node:
    def __init__(self):
        self.bomb = False
        self.around = 0
        self.marked = False
        self.explored = False

class Game:
    def __init__(self):
        self.board = []

        # Generate empty board
        for i in range(grid_size):
            self.board.append([])

            for j in range(grid_size):
                self.board[i].append(Node())

        self.dead = False
        self.dead_on = None

        self.started = False
        self.solving = False
        self.solved_tiles = []

        self.flags = 0
        self.guesses = 0

    # Counts number of explored tiles
    def exp(self):
        count = 0

        for i in range(grid_size):
            for j in range(grid_size):
                if self.board[i][j].explored:
                    count += 1

        return count

    # Returns if board has been solved or not
    def won(self):
        for i in range(grid_size):
            for j in range(grid_size):
                if not self.board[i][j].bomb and not self.board[i][j].explored:
                    return False

        return True

    # Populate board with bombs
    def populate(self):
        bombs_placed = 0

        while bombs_placed < bombs:
            i = random.randint(0, grid_size - 1)
            j = random.randint(0, grid_size - 1)

            if not self.board[i][j].bomb and not self.board[i][j].explored:
                self.board[i][j].bomb = True
                bombs_placed += 1

                # Update surrounding bomb counters
                for surround in surrounding:
                    if 0 <= i + surround[0] < grid_size and 0 <= j + surround[1] < grid_size:
                        self.board[i + surround[0]][j + surround[1]].around += 1

    # Called every frame to handle key input
    def take_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

            # Register clicks
            if event.type == pygame.MOUSEBUTTONUP and not self.dead:
                pos = pygame.mouse.get_pos()

                # Make sure inbounds click
                if pos[0] < 800:
                    board_pos = [math.floor(pos[1] / sqsize), math.floor(pos[0] / sqsize)]

                    # LMB
                    if event.button == 1:
                        if not self.board[board_pos[0]][board_pos[1]].marked:
                            if self.board[board_pos[0]][board_pos[1]].bomb:
                                self.dead = True
                                self.dead_on = board_pos

                            else:
                                self.board[board_pos[0]][board_pos[1]].explored = True

                                # First click is always a "0" tile
                                if not self.started:
                                    for surround in surrounding:
                                        if 0 <= board_pos[0] + surround[0] < grid_size and 0 <= board_pos[1] + surround[1] < grid_size:
                                            self.board[board_pos[0] + surround[0]][board_pos[1] + surround[1]].explored = True

                                    self.populate()
                                    self.started = True

                    # RMB
                    elif event.button == 3:
                        if not self.board[board_pos[0]][board_pos[1]].explored:

                            # Remove mark
                            if self.board[board_pos[0]][board_pos[1]].marked:
                                self.board[board_pos[0]][board_pos[1]].marked = False
                                self.flags -= 1

                            # Add mark
                            elif self.started:
                                self.board[board_pos[0]][board_pos[1]].marked = True
                                self.flags += 1

        if pygame.key.get_pressed()[pygame.K_c]:
            return

        if pygame.key.get_pressed()[pygame.K_r]:
            self.__init__()

        if pygame.key.get_pressed()[pygame.K_SPACE]:
            # To ensure board population before AI is triggered
            if self.started and not self.solving and not self.dead and not self.won():
                self.solving = True

                for i in range(grid_size):
                    for j in range(grid_size):
                        if self.board[i][j].marked:
                            self.board[i][j].marked = False

                self.flags = 0

        if pygame.key.get_pressed()[pygame.K_RETURN]:
            webbrowser.open("https://github.com/T-fXD/Minesweeper/blob/main/main.py")

            # To avoid multiple tabs opening
            pygame.time.delay(100)

    # Recusive function to auto-expand tiles with no bombs around them
    def flood(self):
        f = False

        for i in range(grid_size):
            for j in range(grid_size):
                if self.board[i][j].around == 0 and self.board[i][j].explored:
                    for surround in surrounding:
                        if 0 <= i + surround[0] < grid_size and 0 <= j + surround[1] < grid_size:
                            if not self.board[i + surround[0]][j + surround[1]].explored:
                                self.board[i + surround[0]][j + surround[1]].explored = True

                                f = True

        if f:
            if animate_flood:
                self.render_game()

            self.flood()

    # Called every frame to render in the minesweeper game
    def render_game(self):
        window.fill(black)

        over = self.won()

        for i in range(grid_size):
            for j in range(grid_size):
                pos = (j * sqsize, i * sqsize, sqsize - 1, sqsize - 1)

                # Marked
                if self.board[i][j].marked:
                    pygame.draw.rect(window, red, pos)

                # Unexplored
                elif not self.board[i][j].explored:
                    pygame.draw.rect(window, white, pos)

                # Explored
                elif self.board[i][j].around != 0 or not darker_zeroes:
                    c = num_colors[self.board[i][j].around]
                    pygame.draw.rect(window, blue, pos)

                    # Bombs around text
                    if self.board[i][j].around != 0:
                        label = tile_font.render(str(self.board[i][j].around), 1, num_colors[self.board[i][j].around])
                        window.blit(label, (j * sqsize + sqsize / 2 - label.get_width() / 2, i * sqsize + sqsize / 2 - label.get_height() / 2))

                # Darker 0 tiles (if enabled)
                else:
                    pygame.draw.rect(window, blue_dark, pos)

                if over and self.board[i][j].bomb:
                    pygame.draw.rect(window, gold, pos)

        # Hovered tile
        int_pos = [math.floor(pygame.mouse.get_pos()[1] / sqsize), math.floor(pygame.mouse.get_pos()[0] / sqsize)]

        if not self.dead and not self.solving and int_pos[0] < grid_size and int_pos[1] < grid_size \
            and not self.board[int_pos[0]][int_pos[1]].explored and not self.board[int_pos[0]][int_pos[1]].marked:

            pygame.draw.rect(window, grey,
                                 (int_pos[1] * sqsize, int_pos[0] * sqsize, sqsize - 1, sqsize - 1))

        # If game over...
        if self.dead:
            # Show where last clicked
            pygame.draw.rect(window, green, (self.dead_on[1] * sqsize, self.dead_on[0] * sqsize, sqsize - 1, sqsize - 1))

            # Show bombs
            for i in range(grid_size):
                for j in range(grid_size):
                    if self.board[i][j].bomb:

                        # Fancy bomb
                        if fancy_bombs:
                            window.blit(b, (j * sqsize, i * sqsize))

                        # Circle bomb
                        else:
                            pygame.draw.circle(window, black, (j * sqsize + sqsize / 2, i * sqsize + sqsize / 2),
                                           sqsize / 2.5)

        # Sidebar text

        # Bombs text
        label = font.render(str(math.floor(self.exp() / (grid_size * grid_size - bombs) * 100)) + "% solved", 1, white)
        window.blit(label, (h + (w - h) / 2 - label.get_width() / 2, 10))

        # Percent solved text
        label_ = font.render(str(self.flags) + "/" + str(bombs) + " bombs", 1, white)
        window.blit(label_, (h + (w - h) / 2 - label_.get_width() / 2, 20 + label.get_height()))

        # Satisfied text
        sur = 0
        for surround in surrounding:
            i = int_pos[0] + surround[0]
            j = int_pos[1] + surround[1]

            if 0 <= i < grid_size and 0 <= j < grid_size:
                if self.board[i][j].marked:
                    sur += 1

        text = "-/-"

        if 0 <= int_pos[0] < grid_size and 0 <= int_pos[1] < grid_size:
            if not self.board[int_pos[0]][int_pos[1]].marked and self.board[int_pos[0]][int_pos[1]].explored:
                text = str(sur) + "/" + str(self.board[int_pos[0]][int_pos[1]].around)

        _label = font.render(text + " marked", 1, white)
        window.blit(_label, (h + (w - h) / 2 - _label.get_width() / 2, 30 + label.get_height() + label_.get_height()))

        # Guesses text
        label = font.render("Guesses: " + str(self.guesses), 1, white)
        window.blit(label, (h + (w - h) / 2 - label.get_width() / 2, h - label.get_height() - 10))

        # Show fps
        clock.tick(60)
        pygame.display.set_caption("Minesweeper / " + str(round(clock.get_fps(), 2)) + " fps")

        pygame.display.update()

    # Called every frame if key "c" is held in order to render the controls for the game
    def render_controls(self):

        window.fill(black)

        for i in range(len(controls)):
            label = font.render(controls[i], 1, white)
            window.blit(label, (w/2 - label.get_width()/2, h/2 - label.get_height()/2 + i*52 - len(controls)*26))

        label = font_small.render("By TfXD - Press Enter To See Repository", 1, white)
        window.blit(label, (w - label.get_width() - 10, h - label.get_height() - 10))

        # Show fps
        clock.tick(60)
        pygame.display.set_caption("Minesweeper / " + str(round(clock.get_fps(), 2)) + " fps")

        pygame.display.update()

    def solve(self):
        # Failsafe if no new tiles are explored
        fs = True

        for i in range(grid_size):
            for j in range(grid_size):
                if self.board[i][j].explored and self.board[i][j].around > 0 and [i, j] not in self.solved_tiles:
                    opens = 0
                    marks = 0

                    for surround in surrounding:
                        _i = i + surround[0]
                        _j = j + surround[1]

                        if 0 <= _i < grid_size and 0 <= _j < grid_size:
                            if not self.board[_i][_j].explored:
                                opens += 1

                            if self.board[_i][_j].marked:
                                marks += 1

                    # Mark tiles
                    if opens == self.board[i][j].around:
                        for surround in surrounding:
                            _i = i + surround[0]
                            _j = j + surround[1]

                            if 0 <= _i < grid_size and 0 <= _j < grid_size:

                                if not self.board[_i][_j].explored and not self.board[_i][_j].marked:
                                    self.board[_i][_j].marked = True

                                    self.flags += 1

                                    if not fast:
                                        self.flood()
                                        self.render_game()

                                    fs = False

                        self.solved_tiles.append([i, j])

                    # Explore tiles
                    if marks == self.board[i][j].around:
                        for surround in surrounding:
                            _i = i + surround[0]
                            _j = j + surround[1]

                            if 0 <= _i < grid_size and 0 <= _j < grid_size:

                                if not self.board[_i][_j].explored and not self.board[_i][_j].marked:
                                    self.board[_i][_j].explored = True

                                    if not fast:
                                        self.flood()
                                        self.render_game()

                                    fs = False

                        self.solved_tiles.append([i, j])

        if fs:
            for i in range(grid_size):
                for j in range(grid_size):
                    if not self.board[i][j].explored and not self.board[i][j].marked:
                        self.guesses += 1

                        if self.board[i][j].bomb:
                            self.solving = False
                            self.dead = True
                            self.dead_on = [i, j]
                            return

                        self.board[i][j].explored = True
                        return

            # If all tiles have been explored
            self.solving = False

        if fast:
            self.flood()
            self.render_game()


def main():
    game = Game()

    while True:
        game.take_input()
        game.flood()

        if game.solving:
            game.solve()
            game.render_game()

        elif not pygame.key.get_pressed()[pygame.K_c]:
            game.render_game()

        else:
            game.render_controls()

if __name__ == "__main__":
    main()
