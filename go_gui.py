#! /usr/bin/env python
import numpy as np
import math
import pygame
import pygame.gfxdraw
import time
from random import shuffle, random, choice
import colorsys
import cairo
import Image


MUTE = False

LEFT = 1

bgcolor = 0, 0, 0
blueval = 0
bluedir = 1
x = y = 0
running = True
# TODO: draw board size button as a 3x3 grid?

fps = 30
DISPLAY_REFRESH = pygame.USEREVENT
pygame.time.set_timer(DISPLAY_REFRESH, int(1000.0 / fps))

sound_files = ["%i.wav" % i for i in xrange(1, 26)]

pygame.init()

sounds = [pygame.mixer.Sound("board_game_sounds_amp/" + x) for x in sound_files]

# Hide the mouse cursor
blank_cursor_strings = [''.join([' '] * 24)] * 24
# TODO: set this based on whether a touch device is available?
if False:
    blank_cursor_strings[0] = 'XX                      '
    blank_cursor_strings[1] = blank_cursor_strings[0]
cursor_dims = (24, 24)
cursor_center = (0, 0)
cursor_data, cursor_mask = pygame.cursors.compile(blank_cursor_strings, black='X', white='.', xor='o')
pygame.mouse.set_cursor(cursor_dims,
                        cursor_center,
                        cursor_data,
                        cursor_mask)
# pygame.mouse.set_visible(False) # seems like this may generate unwanted mouse movement events in fullscreen mode
info_object = pygame.display.Info()

print "display info:"
print str(info_object)

# exit()

full_res = (info_object.current_w, info_object.current_h)
# window_res = (full_res[0]/2, full_res[1]/2)
# window_res = (600,600)
window_res = (800, 400)
#window_res = (1000, 600) # better usually
fullscreen = False
current_res = window_res
lw_factor = 0.005
# define line-width in relation to minimum display dimension
# (should ultimately relate this to inches or cm)
# Will need to rework to deal with multitouch zoom
lw = 0


def update_lw():
    global lw
    lw = max(1, int(lw_factor * min(current_res)))


update_lw()
screen = pygame.display.set_mode(window_res)

mouse_down = False

from time import clock
class LatencyTimer:
    thresh = 0.1 # required delay between plays
                 # - seems like timer.clock() might not be in seconds
    last_time = -1

    def __init__(self, thresh=None):
        if thresh is not None:
            self.thresh = thresh
        self.last_time = clock()

    def reset(self):
        #print "Resetting timer"
        self.last_time = clock()

    def check(self):
        current_time = clock()
        diff = current_time - self.last_time
        #print "Time since last timer reset: %f"%diff
        if diff > self.thresh:
            return True
        else:
            return False

latency_timer = LatencyTimer()


class Notifier:
    thresh = 0.2

    def __init__(self):
        self.timer = LatencyTimer(4)
        self.text = ""

    def update(self, **kwargs):
        print "updating notifier"
        # set a negative thresh to indicate no threshold to disappearance
        if "text" in kwargs:
            self.text = kwargs["text"]
            print "with text \"%s\""%self.text
        if "thresh" in kwargs:
            self.thresh = kwargs["thresh"]
        else:
            self.thresh = 0.5
        self.timer = LatencyTimer(self.thresh)

    def render(self):
        # TODO: render same message rotated for each player
        # and out of the way of the board

        #print "Checking notifier timer with thresh %f"%self.timer.thresh
        if self.thresh<0 or not self.timer.check():
            #print "Attempting to render notification"
            # calc rect coords in window coords
            w = current_res[0]
            h = current_res[1]
            if w > h:
                # landscape mode
                c = (w/6.0, 10)
            else:
                # portrait mode
                c = (w / 2.0, (h - w) / 2.0)

            # myfont = pygame.font.SysFont("monospace", 24)
            myfont = pygame.font.SysFont("Ubuntu", 48)
            # render text
            label = myfont.render(self.text, True, (100,180,255))
            #label = pygame.transform.rotate(label, 90)
            screen.blit(label, c)

notifier = Notifier()


colors = [
    # cyan and magenta
    [(0, 170, 170), (85, 255, 255), (170, 0, 170), (255, 85, 255)]
    # magenta and green
    # blue and orange
    # yellow and purple

]


# TODO:
# - render a dithered gradient for each game piece instead of flat circle
# - multitouch pinch zoom   
# - stone placement jitter?

# cairo-to-pygame func -------------------------------------

def bgra_surf_to_rgba_string(cairo_surface):
    # uses Python Image Library
    img = Image.frombuffer(
        'RGBA', (cairo_surface.get_width(),
                 cairo_surface.get_height()),
        cairo_surface.get_data(), 'raw', 'BGRA', 0, 1)

    return img.tostring('raw', 'RGBA', 0, 1)


# -------------------------------------------------------------


def hsv2rgb(h, s, v):
    # hue is 0-1
    # saturation and value are 0-1
    return tuple(i * 255 for i in colorsys.hsv_to_rgb(h, s, v))


def angle_diff(a, b):
    # given two angles 0-1, return the absolute 
    # angular distance between them (taking into account boundary)
    diff = abs(a - b)
    if diff > 0.5:
        diff = diff - 0.5
    return diff


def color_gen():

    while True:
        hue1 = choice(list(np.arange(0, 1, 1.0 / 360.0)))
        # print "hue1: %f"%hue1
        hue2 = hue1 + 0.5
        if hue2 > 1.0:
            hue2 = hue2 - 1.0
        dark1 = hsv2rgb(hue1, 0.95, 0.9)
        bright1 = hsv2rgb(hue1, 0.4, 1.0)
        # print "bright1: %s"%(str(bright1))
        dark2 = hsv2rgb(hue2, 0.95, 0.9)
        bright2 = hsv2rgb(hue2, 0.4, 1.0)
        # print "bright2: %s"%(str(bright2))
        yield (dark1, bright1, dark2, bright2)


color_index = 0

dims = [(5, 5), (9, 9), (13, 13), (19, 19)]
dims_index = 1

if False:
    states = [
        '''2.11.
        12111
        1.1..
        11.11
        .1111''',
        '''2.11.
        12111
        111..
        11.11
        .1111''']
    initial_states = []
    for n in xrange(len(states)):
        s = [line.strip() for line in states[n].splitlines()]
        initial_states.append(np.full((5, 5), 0, dtype=np.int))
        for i in xrange(5):
            for j in xrange(5):
                if s[i][j] == '.':
                    continue
                initial_states[-1][i][j] = int(s[i][j])

    moves = [((1, 2), 1)]


def rounded_rect(w, h, r=10, color=(255, 255, 255)):
    data = np.full(w * h * 4, 0, dtype=np.int8)
    cairo_surface = cairo.ImageSurface.create_for_data(
        data, cairo.FORMAT_ARGB32, w, h, w * 4)

    context = cairo.Context(cairo_surface)

    color = [v / 255.0 for v in color]
    x = y = 0
    "Draw a rounded rectangle"
    #   A****BQ
    #  H      C
    #  *      *
    #  G      D
    #   F****E

    context.move_to(x + r, y)  # Move to A
    context.line_to(x + w - r, y)  # Straight line to B
    context.curve_to(x + w - r / 2, y,
                     x + w, y + r / 2,
                     x + w, y + r)  # Curve to C, Control points are both at Q
    context.line_to(x + w, y + h - r)  # Move to D
    context.curve_to(x + w, y + h - r / 2,
                     x + w - r / 2, y + h,
                     x + w - r, y + h)  # Curve to E
    context.line_to(x + r, y + h)  # Line to F
    context.curve_to(x + r / 2, y + h,
                     x, y + h - r / 2,
                     x, y + h - r)  # Curve to G
    context.line_to(x, y + r)  # Line to H
    context.curve_to(x, y + r / 2,
                     x + r / 2, y,
                     x + r, y)  # Curve to A
    context.set_source_rgb(color[0], color[1], color[2])  # Solid color
    context.fill()
    return cairo_surface


# not sure whether I should use global screen state or
# pass as params on render
# TODO: break some of this out into other classes
# this seems to be approaching the god-object
class Board:
    def __init__(self, stone_colors, dims):
        self.dims = dims
        self.komi = 7.5
        if self.dims == (19, 19):
            self.komi = 7.5
        elif self.dims == (5, 5):
            self.komi = 0.5
        else:
            self.komi = 5.5  # use smaller komi for smaller boards
        self.star_points = []
        if self.dims == (19, 19):
            self.star_points = [
                (3, 3), (9, 3), (15, 3),
                (3, 9), (9, 9), (15, 9),
                (3, 15), (9, 15), (15, 15)
            ]
        elif self.dims == (13, 13):
            self.star_points = [
                (3, 3), (9, 3),
                (6, 6),
                (3, 9), (9, 9)
            ]
        elif self.dims == (9, 9):
            self.star_points = [
                (2, 2), (6, 2),
                (4, 4),
                (2, 6), (6, 6)
            ]
        # make padding half a cell width plus some fixed factor
        self.pad = 1.0 / self.dims[0] / 2.0 + 0.05
        # self.pad = 0.08 # fraction of minimum window dimension
        # that will be a border around rendered board
        # TODO: should add a fixed padding to account for an extra cell of width and height
        # (this would make varying board sizes more consistent)
        self.stretch_factor = 1.5  # wide axis stretch factor (slight perspective correction)
        # TODO: account for this in transformations and in circle rendering
        self.base_grid_color = (127, 127, 254)
        self.grid_brightness_factors = [x/10.0 for x in range(10)]
        self.grid_brightness_index = 4
        self.set_grid_color()
        # TODO: make pairs of colors and rotate through for new games
        self.player1_fillcolor = stone_colors[0]
        self.player1_tempfillcolor = stone_colors[1]
        self.player2_fillcolor = stone_colors[2]
        self.player2_tempfillcolor = stone_colors[3]

        self.player1_edgecolor = (0, 0, 0)
        self.player2_edgecolor = (0, 0, 0)
        self.player1_rect = ((0, 0), (0, 0))
        self.player2_rect = ((0, 0), (0, 0))
        self.newboard_rect = ((0, 0), (0, 0))
        self.circle_lw_factor = 0.02  # fraction of cell width circle lw fills
        self.circle_width_factor = 0.52  # fraction of cell width circle fills
        self.territory_width_factor = 0.16
        self.grid_lw_factor = 0.002
        self.capture_counts = {1: [], 2: []}
        # self.passed = False # store True if the last turn was passed
        self.states = []
        self.moves = []  # store player and coords of move or "pass" indicator
        self.state_index = 0
        initial_state = np.full(self.dims, 0, dtype=np.int)
        # initial_state[0][0] = '1' # test rendering
        # initial_state[1][0] = '2'
        self.states.append(initial_state)
        self.playable = np.full(self.dims, 1, dtype=np.int)
        self.current_player = 1
        self.temp_coords = None  # location (in board coordinates) of moused-over position
        self.last_stone_coords = [None]  # location of last-played stone
        self.game_modes = ["play", "dead removal", "territory assignment"]
        self.current_game_mode = 0  # index of game mode
        self.dead_removed_state = None
        self.territory = np.full(self.dims, 0, dtype=np.int)
        self.scores = {1: 0.0, 2: self.komi}  # add komi to second player's score
        self.final_scores = {1: 0.0, 2: 0.0}
        self.button_down = 0  # 1 or 2 indicating mouse down on player pass button, 3 indicating board size button
        self.undo_button_down = 0

        # self.states = initial_states.copy()
        # self.moves = list(moves)

        # self.img_data = [None]*10 # should get rid of this, probably don't need

        self.prerender_cairo()
        # self.init_cairo_surface()

    def set_grid_color(self):
        self.grid_color = ( int(self.base_grid_color[0]*self.grid_brightness_factors[self.grid_brightness_index]),
                            int(self.base_grid_color[1]*self.grid_brightness_factors[self.grid_brightness_index]),
                            int(self.base_grid_color[2]*self.grid_brightness_factors[self.grid_brightness_index]) )
        print "Set grid color to (%i, %i, %i)"%(self.grid_color[0],
                                                self.grid_color[1],
                                                self.grid_color[2])

    def init_cairo_surface(self):
        w, h = screen.get_size()
        # Get a reference to the memory block storing the pixel data.
        pixels = pygame.surfarray.pixels2d(screen)

        # Set up a Cairo surface using the same memory block and the same pixel
        # format (Cairo's RGB24 format means that the pixels are stored as
        # 0x00rrggbb; i.e. only 24 bits are used and the upper 16 are 0).
        self.cairo_surface = cairo.ImageSurface.create_for_data(
            pixels.data, cairo.FORMAT_RGB24, w, h)

        self.prerender_cairo()  # eventually delete the above, shouldn't be needed

    def prerender_stone(self, color, radius, outline_width=0, use_gradient=True):

        w = int(round(radius * 2))
        data = np.full(w * w * 4, 0, dtype=np.int8)
        # need to get this into a pygame.Surface for blitting
        cairo_surface = cairo.ImageSurface.create_for_data(
            data, cairo.FORMAT_ARGB32, w, w, w * 4)

        def draw_circle(r, color):
            ctx = cairo.Context(cairo_surface)
            x = radius  # outer radius, i.e. half the width of the full tile
            y = x
            grad = cairo.RadialGradient(x, y, 0, x, y, r)
            red, green, blue = [v / 255.0 for v in color]
            # stop location, r, g, b, a
            locs_alphas = [
                (0, 1),
                (0.3, 1),
                (0.75, 0.8),
                (0.85, 0.75),
                (0.95, 0.5),
                (1.0, 0.0)
            ]
            if use_gradient == True:
                for loc, a in locs_alphas:
                    grad.add_color_stop_rgba(loc, red, green, blue, a)
                ctx.set_source(grad)
            else:
                ctx.set_source_rgb(red, green, blue)
            ctx.arc(x, y, r, 0, 2 * math.pi);
            ctx.close_path()
            ctx.fill()

        if outline_width != 0:
            draw_circle(radius, (0, 0, 0))
        draw_circle(radius - outline_width, color)

        w = cairo_surface.get_width()
        h = cairo_surface.get_height()
        # print "surf dims: %i, %i"%(w,h)

        # write to file for debug
        # cairo_surface.write_to_png ("prerendered/stone%i.png"%i)

        # Create PyGame surface from Cairo Surface
        data_string = bgra_surf_to_rgba_string(cairo_surface)
        pygame_surface = pygame.image.frombuffer(data_string, (w, h), "RGBA", )  # data.tostring()

        # write to file for debug
        # cairo_surface.write_to_png ("prerendered/stone%i_after_pygame_conversion.png"%i)

        # also return pointer to raw data, so it remains persistent (NVM)
        return pygame_surface

    def prerender_button(self, player=1, bright=False):
        if player == 1:
            color = self.player1_fillcolor
            w = abs(self.player1_rect[0][0] - self.player1_rect[1][0])
            h = abs(self.player1_rect[0][1] - self.player1_rect[1][1])
            if bright == True:
                color = self.player1_tempfillcolor
        elif player == 2:
            color = self.player2_fillcolor
            w = abs(self.player2_rect[0][0] - self.player2_rect[1][0])
            h = abs(self.player2_rect[0][1] - self.player2_rect[1][1])
            if bright == True:
                color = self.player2_tempfillcolor

        print "about to prerender button with dims: %i,%i" % (w, h)
        cairo_surface = rounded_rect(w, h, r=w / 15.0, color=color)

        w = cairo_surface.get_width()
        h = cairo_surface.get_height()

        # cairo_surface.write_to_png ("prerendered/button_%i_bright_%s.png"%(player,str(bright)))

        # Create PyGame surface from Cairo Surface
        data_string = bgra_surf_to_rgba_string(cairo_surface)
        pygame_surface = pygame.image.frombuffer(data_string, (w, h), "RGBA", )  # data.tostring()
        return pygame_surface

    def prerender_cairo(self):
        w, h = screen.get_size()
        cell_width = min(w, h) * (1 - self.pad * 2) / (self.dims[0] - 1)
        circle_lw = max(1, self.circle_lw_factor * cell_width)
        circle_width = max(2, self.circle_width_factor * cell_width)
        territory_width = max(2, self.territory_width_factor * cell_width)
        last_stone_width = max(2, self.circle_width_factor * cell_width * 0.2)
        marker_scale = (self.dims[0] - 5) / 14 * 0.075 + 0.08
        if self.dims[0] == 13:
            marker_scale = 0.12
        grid_marker_width = int(round(max(2, cell_width * marker_scale)))
        # want the scale to be 1.5 for 19x19, 1.1 for 5x5
        scale = (self.dims[0] - 5) / 14 * 0.4 + 1.1
        if self.dims[0] == 13:
            scale = 1.4  # 13x13 needs to be a bit larger, too tiny on current screen
        self.stone1 = self.prerender_stone(self.player1_fillcolor,
                                           circle_width,
                                           outline_width=circle_lw)
        self.stone1_bright = self.prerender_stone(self.player1_tempfillcolor,
                                                  circle_width,
                                                  outline_width=circle_lw)
        self.stone1_bright_large = self.prerender_stone(self.player1_tempfillcolor,
                                                        circle_width * scale,
                                                        outline_width=circle_lw)
        self.territory1 = self.prerender_stone(self.player1_fillcolor,
                                               territory_width,
                                               outline_width=circle_lw)
        self.last_stone1 = self.prerender_stone(self.player1_tempfillcolor,
                                                last_stone_width,
                                                outline_width=0,
                                                use_gradient=False)
        self.grid_marker = self.prerender_stone(self.grid_color,
                                                grid_marker_width,
                                                outline_width=0,
                                                use_gradient=False)

        self.stone2 = self.prerender_stone(self.player2_fillcolor,
                                           circle_width,
                                           outline_width=circle_lw)
        self.stone2_bright = self.prerender_stone(self.player2_tempfillcolor,
                                                  circle_width,
                                                  outline_width=circle_lw)
        self.stone2_bright_large = self.prerender_stone(self.player2_tempfillcolor,
                                                        circle_width * scale,
                                                        outline_width=circle_lw)
        self.territory2 = self.prerender_stone(self.player2_fillcolor,
                                               territory_width,
                                               outline_width=circle_lw)
        self.last_stone2 = self.prerender_stone(self.player2_tempfillcolor,
                                                last_stone_width,
                                                outline_width=0,
                                                use_gradient=False)
        self.stone1_captured = self.prerender_stone(self.player1_fillcolor,
                                                    circle_width / 5.0,
                                                    outline_width=circle_lw)
        self.stone2_captured = self.prerender_stone(self.player2_fillcolor,
                                                    circle_width / 5.0,
                                                    outline_width=circle_lw)

        o = 4
        t = 0.5
        if w > h:
            # landscape mode
            UL1 = (int(round((w - h) / 2.0 * 0.5)), int(round(self.pad * h * 2)))
            LR1 = (int(round((w - h) / 2.0 * 0.5 + self.pad * h)), int(round((1 - self.pad * 2) * h)))
            UL2 = (int(round(h + (w - h) / 2.0 + (w - h) / 2.0 * 0.5 - self.pad * h)), int(round(self.pad * h * 2)))
            LR2 = (int(round(h + (w - h) / 2.0 + (w - h) / 2.0 * 0.5)), int(round((1 - self.pad * 2) * h)))
        else:
            # portrait mode
            UL1 = (int(round(self.pad * w * 2)), int(round((h - w) / 2.0 * 0.5)))
            LR1 = (int(round((1 - self.pad * 2) * w)), int(round((h - w) / 2.0 * 0.5 + self.pad * w)))
            UL2 = (int(round(self.pad * w * 2)), int(round(w + (h - w) / 2.0 * 0.75)))
            LR2 = (int(round((1 - self.pad * 2) * w)), int(round(w + (h - w) / 2.0 * 0.75 - self.pad * w)))
        self.player1_rect = (UL1, LR1)
        self.player2_rect = (UL2, LR2)

        self.button1 = self.prerender_button(player=1, bright=False)
        self.button1_bright = self.prerender_button(player=1, bright=True)
        self.button2 = self.prerender_button(player=2, bright=False)
        self.button2_bright = self.prerender_button(player=2, bright=True)

    def score(self):
        # score is controlled empty territory
        # minus stones lost to capture
        # plus komi (komi is added at init)
        for p in [1, 2]:
            self.final_scores[p] = self.scores[p] + np.sum(self.territory == p) - sum(self.capture_counts[p])
            print "player %i score is %0.1f, %0.f territory - %0.f captured or passed + %0.1f komi" % (p,
                                                                                                       self.final_scores[p],
                                                                                                       np.sum(self.territory == p),
                                                                                                       sum(self.capture_counts[p]),
                                                                                                       self.scores[p])


    # TODO: remove redundant code in forward and reverse transforms
    # TODO: implement zoom/move in following two transforms
    def trans_window_to_figure(self, coord):
        w = current_res[0]
        h = current_res[1]
        if w > h:
            # landscape mode
            UL = ((w - h) / 2.0, 0.0)
            LR = (float(UL[0] + h), float(h))
        else:
            # portrait mode
            UL = (0.0, (h - w) / 2.0)
            LR = (float(w), float(w + UL[1]))
        x0 = UL[0]
        y0 = UL[1]
        x1 = LR[0]
        y1 = LR[1]
        # print "x0, y0 = "+str(UL)
        # print "x1, y1 = "+str(LR)
        # figure coords go from 0 to 1 on both axes
        x = (coord[0] - x0) / (x1 - x0)
        y = (coord[1] - y0) / (y1 - y0)
        return (x, y)

    def trans_figure_to_window(self, coord):
        # use upper left corner of figure as starting point, and scale by some factor
        # this will hopefully make zoom implementation simpler
        w = current_res[0]
        h = current_res[1]
        if w > h:
            # landscape mode
            UL = ((w - h) / 2.0, 0.0)
            LR = (float(UL[0] + h), float(h))
        else:
            # portrait mode
            UL = (0.0, (h - w) / 2.0)
            LR = (float(w), float(w + UL[1]))
        x0 = UL[0]
        y0 = UL[1]
        x1 = LR[0]
        y1 = LR[1]
        # figure coords go from 0 to 1 on both axes
        x = x0 + coord[0] * (x1 - x0)
        y = y0 + coord[1] * (y1 - y0)
        return (x, y)

    def trans_figure_to_board(self, coord):
        # first rescale from 0 to 1
        # xtemp = coord[0]/float(self.dims[0]-1)
        # ytemp = coord[1]/float(self.dims[1]-1)
        # then account for padding around board
        x0 = self.pad
        x1 = 1 - self.pad
        y0 = self.pad
        y1 = 1 - self.pad
        x = (coord[0] - x0) / (x1 - x0) * float(self.dims[0] - 1)
        y = (coord[1] - y0) / (y1 - y0) * float(self.dims[1] - 1)
        return (x, y)

    def trans_board_to_figure(self, coord):
        # first rescale from 0 to 1
        xtemp = coord[0] / float(self.dims[0] - 1)
        ytemp = coord[1] / float(self.dims[1] - 1)
        # then account for padding around board
        x0 = self.pad
        x1 = 1 - self.pad
        y0 = self.pad
        y1 = 1 - self.pad
        x = x0 + xtemp * (x1 - x0)
        y = y0 + ytemp * (y1 - y0)
        return (x, y)

    def trans_board_to_window(self, coord):
        return self.trans_figure_to_window(self.trans_board_to_figure(coord))

    def trans_window_to_board(self, coord):
        # window_coords = coord
        # fig_coords = self.trans_window_to_figure(coord)
        # board_coords = self.trans_figure_to_board(fig_coords)
        # print "window coords: "+str(window_coords)
        # print "fig coords: "+str(fig_coords)
        # print "board coords: "+str(board_coords)
        return self.trans_figure_to_board(self.trans_window_to_figure(coord))

    def tbw(self, coord):
        return self.trans_board_to_window(coord)

    def twb(self, coord):
        return self.trans_window_to_board(coord)

    def test_pass(self, coord, both=False):
        # given a location in window coords, check for within rectangle
        # print "testing for pass button press, current player %i"%self.current_player
        # print "player1 rect: "+str(self.player1_rect)
        # print "player2 rect: "+str(self.player2_rect)
        # print "event location: "+str(coord)
        # print "both = %s"%(both)
        x = coord[0]
        y = coord[1]
        if ((self.current_player == 1) or (both is True)):
            if x > self.player1_rect[0][0] and \
                y > self.player1_rect[0][1] and \
                x < self.player1_rect[1][0] and \
                y < self.player1_rect[1][1]:
                # print "button 1 pressed"
                return 1
        if ((self.current_player == 2) or (both is True)):
            if x > self.player2_rect[0][0] and \
                y > self.player2_rect[0][1] and \
                x < self.player2_rect[1][0] and \
                y < self.player2_rect[1][1]:
                # print "button 2 pressed"
                return 2

        if x > self.newboard_rect[0][0] and \
            y > self.newboard_rect[0][1] and \
            x < self.newboard_rect[1][0] and \
            y < self.newboard_rect[1][1]:
            # print "button 3 pressed"
            return 3
        return False

    def render_grid(self):
        # print "\n\n\n"
        grid_lw = max(1, int(self.grid_lw_factor * min(current_res)))
        # draw horizontal gridlines
        for i in xrange(self.dims[1]):
            start = self.tbw((0, i))
            end = self.tbw((self.dims[0] - 1, i))
            # print "hline: %s - %s"%(start, end)
            pygame.draw.line(screen, self.grid_color,
                             start, end, grid_lw)
        # draw vertical gridlines
        for i in xrange(self.dims[0]):
            start = self.tbw((i, 0))
            end = self.tbw((i, self.dims[1] - 1))
            # print "vline: %s - %s"%(start, end)
            pygame.draw.line(screen, self.grid_color,
                             start, end, grid_lw)

        # draw star points
        for i, j in self.star_points:
            center = self.tbw((i, j))
            self.center_blit(int(round(center[0])),
                             int(round(center[1])),
                             self.grid_marker)


    def center_blit(self, x, y, surf):
        # blit a surface to the screen surface,
        # centering the surface horizontally and vertically
        sw = surf.get_width()
        sh = surf.get_height()
        c1 = x - int(round(sw / 2.0))
        c2 = y - int(round(sh / 2.0))
        screen.blit(surf, (c1, c2))


    def blit_button(self, player=1, bright=False):
        if player == 1:
            if bright == True:
                screen.blit(self.button1_bright, self.player1_rect[0])
            else:
                screen.blit(self.button1, self.player1_rect[0])
        elif player == 2:
            if bright == True:
                screen.blit(self.button2_bright, self.player2_rect[0])
            else:
                screen.blit(self.button2, self.player2_rect[0])

    def render_state(self, state):
        # draw game pieces
        for i in xrange(self.dims[0]):
            for j in xrange(self.dims[1]):
                p = state[i][j]
                if p == 0:
                    continue
                elif p == 1 or p == 2:
                    center = self.tbw((i, j))

                    # blit pre-rendered image instead of regen
                    if p == 1:
                        img = self.stone1
                    elif p == 2:
                        img = self.stone2
                    self.center_blit(int(round(center[0])),
                                     int(round(center[1])),
                                     img)


    def render_bright_stone(self, coords, player, scale=1.0):
        center = self.tbw(coords)

        if player == 1:
            if scale == 1.0:
                img = self.stone1_bright
            else:
                img = self.stone1_bright_large
        elif player == 2:
            if scale == 1.0:
                img = self.stone2_bright
            else:
                img = self.stone2_bright_large
        self.center_blit(int(round(center[0])),
                         int(round(center[1])),
                         img)


    def render_territory_marker(self, coords, player):
        center = self.tbw(coords)

        if player == 1:
            img = self.territory1
        elif player == 2:
            img = self.territory2
        self.center_blit(int(round(center[0])),
                         int(round(center[1])),
                         img)


    def render_last_stone_marker(self):
        if self.last_stone_coords[-1] is None:
            return
        # print "rendering last stone marker"
        # print "last_stone_coords: "+str(self.last_stone_coords)
        center = self.tbw(self.last_stone_coords[-1])
        player = self.states[-1][self.last_stone_coords[-1][0]][self.last_stone_coords[-1][1]]

        if player == 1:
            img = self.last_stone1
        elif player == 2:
            img = self.last_stone2
        self.center_blit(int(round(center[0])),
                         int(round(center[1])),
                         img)


    def render_temp_stone(self):
        # draw temp game piece before final play
        if self.temp_coords == None:
            return
        # want the scale to be 1.5 for 19x19, 1.1 for 5x5
        scale = (self.dims[0] - 5) / 14 * 0.4 + 1.1
        self.render_bright_stone(self.temp_coords, self.current_player, scale=scale)

    def render_undo_stone(self):
        if self.undo_button_down == 0:
            return
        if self.last_stone_coords[-1] is not None:
            scale = (self.dims[0] - 5) / 14 * 0.4 + 1.1
            x, y = self.last_stone_coords[-1]
            self.render_bright_stone((x, y), self.states[-1][x][y], scale=scale)

    def render_pass_buttons(self, both=False):
        ## draw current player indicator rects/pass buttons
        # calc rect coords in window coords
        w = current_res[0]
        h = current_res[1]
        o = 4
        t = 0.5
        if w > h:
            # landscape mode
            UL1 = ((w - h) / 2.0 * 0.5, self.pad * h * 2)
            LR1 = ((w - h) / 2.0 * 0.5 + self.pad * h, (1 - self.pad * 2) * h)
            UL2 = (h + (w - h) / 2.0 + (w - h) / 2.0 * 0.5 - self.pad * h, self.pad * h * 2)
            LR2 = (h + (w - h) / 2.0 + (w - h) / 2.0 * 0.5, (1 - self.pad * 2) * h)
            UL3 = (self.pad * h, self.pad * h)
            LR3 = (self.pad * h * 1.5, self.pad * h * 1.5)
        else:
            # portrait mode
            UL1 = (self.pad * w * 2, (h - w) / 2.0 * 0.5)
            LR1 = ((1 - self.pad * 2) * w, (h - w) / 2.0 * 0.5 + self.pad * w)
            UL2 = (self.pad * w * 2, w + (h - w) / 2.0 * 0.75)
            LR2 = ((1 - self.pad * 2) * w, w + (h - w) / 2.0 * 0.75 - self.pad * w)
            UL3 = (self.pad * h, self.pad * h)
            LR3 = (self.pad * h * 1.5, self.pad * h * 1.5)
        self.player1_rect = (UL1, LR1)
        self.player2_rect = (UL2, LR2)
        self.newboard_rect = (UL3, LR3)
        bright = False
        if self.button_down == 1:
            #player1_color = self.player1_tempfillcolor
            bright = True
        else:
            pass
            #player1_color = self.player1_fillcolor
        if self.button_down == 2:
            #player2_color = self.player2_tempfillcolor
            bright = True
        else:
            pass
            #player2_color = self.player2_fillcolor
        if self.button_down == 3:
            button3_color = (100, 100, 100)
        else:
            button3_color = (50, 50, 50)

        # print "about to blit button(s)"
        if (self.current_player == 1) or (both == True):
            self.blit_button(player=1, bright=bright)

        if (self.current_player == 2) or (both == True):
            self.blit_button(player=2, bright=bright)

        pygame.draw.rect(screen, button3_color,
                         (self.newboard_rect[0][0], self.newboard_rect[0][1],
                          self.newboard_rect[1][0] - self.newboard_rect[0][0],
                          self.newboard_rect[1][1] - self.newboard_rect[0][1]))

    def render_temp_group(self):
        if self.temp_coords == None:
            return
        # find all connected positions at current temp loc        
        connected_locs = self.find_connected_locs(self.dead_removed_state,
                                                  self.temp_coords)
        # iterate over connected positions and render
        i = self.temp_coords[0]
        j = self.temp_coords[1]
        player = self.states[-1][i][j]
        for coords in connected_locs:
            self.render_bright_stone(coords, player)

    def render_territory(self):
        for i in xrange(self.dims[0]):
            for j in xrange(self.dims[1]):
                t = self.territory[i][j]
                if t != 0:
                    self.render_territory_marker((i, j), t)

    def render_score(self):
        # TODO: properly rotate and center text
        self.score()  # not sure if this call is more natural somewhere else
        # calc rect coords in window coords
        w = current_res[0]
        h = current_res[1]
        o = 6
        if w > h:
            # landscape mode
            c1 = ((w - h) / 2.0, h / 2.0)
            c2 = (h + (w - h) / 2.0 + ((w - h) / 2.0) * 0.0, h / 2.0)
        else:
            # portrait mode
            c1 = (w / 2.0, (h - w) / 2.0)
            c2 = (w / 2.0, w + (h - w) / 2.0 + ((h - w) / 2.0) * 0.0)

        # myfont = pygame.font.SysFont("monospace", 24)
        myfont = pygame.font.Font(None, 64)
        # render text
        label = myfont.render(" %0.1f " % self.final_scores[1], 1, (128, 128, 128), (0, 0, 0))
        screen.blit(label, c1)
        label = myfont.render(" %0.1f " % self.final_scores[2], 1, (128, 128, 128), (0, 0, 0))
        screen.blit(label, c2)


    def render_captured(self):
        # TODO: group into tens for easier midgame counting, maybe also show number
        #print "rendering captured stones"
        for p in [1, 2]:
            if len(self.capture_counts[p]) > 0:
                captured_count = sum(self.capture_counts[p])
            else:
                captured_count = 0
            #print "player %i capture count: %i"%(p, captured_count)

            if p == 2:
                x = -1
                d = -1/5.0
            else:
                x = board.dims[0]
                d = 1/5.0
            y = 0
            for i in xrange(captured_count):
                center = self.tbw((x, y))
                if p == 2:
                    img = self.stone1_captured
                elif p == 1:
                    img = self.stone2_captured
                self.center_blit(int(round(center[0])),
                                 int(round(center[1])),
                                 img)
                y += 1/5.0
                if y >= self.dims[1]:
                    x += d
                    y = 0


    def render(self):
        game_mode = board.game_modes[board.current_game_mode]
        if game_mode == "play":
            board.render_grid()
            board.render_state(board.states[-1])
            board.render_captured()
            board.render_temp_stone()
            board.render_undo_stone()
            board.render_last_stone_marker()
            board.render_pass_buttons()
        elif game_mode == "dead removal":
            board.render_grid()
            board.render_state(board.dead_removed_state)
            board.render_captured()
            board.render_temp_group()
            board.render_pass_buttons(both=True)
        elif game_mode == "territory assignment":
            board.render_grid()
            board.render_state(board.dead_removed_state)
            board.render_captured()
            board.render_territory()
            board.render_pass_buttons(both=True)
            board.render_score()
        notifier.render()

    def calc_capture_counts(self, state1, state2):
        capture_counts = {}
        for player in [1, 2]:
            captured = 0
            for i in xrange(self.dims[0]):
                for j in xrange(self.dims[1]):
                    if state1[i][j] == player and state2[i][j] == 0:
                        captured += 1
            capture_counts[player] = captured
        return capture_counts

    def update_capture_counts(self):
        game_mode = self.game_modes[self.current_game_mode]
        #print "Updating capture counts in game mode %s"%game_mode
        if game_mode == "play":
            state1 = self.states[-2]
            state2 = self.states[-1]
        else:
            state1 = self.states[-1]
            state2 = self.dead_removed_state
        #print "state1:"
        #self.print_state(state1)
        #print "state2:"
        #self.print_state(state2)
        capture_counts = self.calc_capture_counts(state1, state2)
        for p in [1, 2]:
            self.capture_counts[p].append(capture_counts[p])
            if capture_counts[p] > 0:
                op = 1
                if p == 1:
                    op = 2
                notifier.update(text="Player %i captured %i stones"%(op, capture_counts[p]))

        #print "updated capture counts: "+str(self.capture_counts)

    def update_temp_coords(self, coord, do_action=False):
        # given a location in window coordinates (pixels)
        # convert to board coordinates, maybe do some collision-esque test
        # and set the temp piece location if within bounds and no current piece there, otherwise set None

        # do simple integer rounding to find closest grid loc,
        board_coord = self.twb(coord)
        int_x = round(board_coord[0])
        int_y = round(board_coord[1])
        # exclude diamond shaped regions to minimize jitter that would otherwise occur at four-way junctions
        t = 0.25
        if abs(int_x - board_coord[0]) > t and \
                        abs(int_y - board_coord[1]) > t:
            self.temp_coords = None
            return
        # exclude out-of-bounds locations
        if not (int_x >= 0 and int_x < self.dims[0] and \
                            int_y >= 0 and int_y < self.dims[1]):
            self.temp_coords = None
            return

        game_mode = self.game_modes[self.current_game_mode]
        if game_mode == "play":
            # exclude previous plays, suicides, and take-backs        
            if self.playable[int_x][int_y] == 1:
                self.temp_coords = (int_x, int_y)
            else:
                self.temp_coords = None
            if do_action is True:
                if self.temp_coords is not None:
                    self.last_stone_coords.append(self.temp_coords)
                self.place_piece()

        elif game_mode == "dead removal":
            # only allow locations with stones
            if self.dead_removed_state[int_x][int_y] != 0:
                self.temp_coords = (int_x, int_y)
            else:
                self.temp_coords = None
            # remove stones
            if do_action is True:
                self.remove_dead()
        elif game_mode == "territory assignment":
            # only allow locations without stones
            if self.dead_removed_state[int_x][int_y] == 0:
                self.temp_coords = (int_x, int_y)
            else:
                self.temp_coords = None
            # toggle player assignment
            if do_action is True:
                self.toggle_territory()

    def find_connected_locs(self, state, coords):
        x = coords[0]
        y = coords[1]
        player = state[x][y]
        connected_locs = [(x, y)]
        locs_to_check = [(x, y)]
        while len(locs_to_check) > 0:
            new_locs_to_check = []
            for i, j in locs_to_check:
                sc = [(i, j - 1), (i - 1, j), (i + 1, j), (i, j + 1)]
                for c in sc:
                    if c[0] >= 0 and c[0] < self.dims[0] and c[1] >= 0 and c[1] < self.dims[1]:
                        v = state[c[0]][c[1]]
                        if v == player:
                            if (c[0], c[1]) not in new_locs_to_check and (c[0], c[1]) not in connected_locs:
                                new_locs_to_check.append((c[0], c[1]))
            locs_to_check = list(new_locs_to_check)
            connected_locs.extend(locs_to_check)
        connected_locs = list(set(connected_locs))
        return connected_locs

    def undo_move(self):
        del self.states[-1]
        del self.last_stone_coords[-1]
        del self.moves[-1]
        del self.capture_counts[1][-1]
        del self.capture_counts[2][-1]
        self.temp_coords = None
        self.state_index -= 1
        if self.current_player == 1:
            self.current_player = 2
        elif self.current_player == 2:
            self.current_player = 1
        self.update_playable()

    def check_undo(self, coord, action="down"):
        # do simple integer rounding to find closest grid loc,
        board_coord = self.twb(coord)
        int_x = round(board_coord[0])
        int_y = round(board_coord[1])
        # exclude diamond shaped regions to minimize jitter that would otherwise occur at four-way junctions
        t = 0.25
        if abs(int_x - board_coord[0]) > t and \
                        abs(int_y - board_coord[1]) > t:
            self.temp_coords = None
            return
        # exclude out-of-bounds locations
        if not (int_x >= 0 and int_x < self.dims[0] and
                int_y >= 0 and int_y < self.dims[1]):
            self.temp_coords = None
            return
        # check if the last stone was clicked
        if (int_x, int_y) != self.last_stone_coords[-1]:
            self.undo_button_down = 0
            return
        if self.undo_button_down == 1:
            if action == "up":
                self.undo_button_down = 0
                self.undo_move()
        else:
            if action == "down":
                self.undo_button_down = 1

    def check_capture_loc(self, state, x, y, player=None):
        # iterate over all connected stones
        # if any adjacent position is unoccupied, no capture happens
        connected_locs = [(x, y)]
        locs_to_check = [(x, y)]
        if x < 0 or x >= self.dims[0] or y < 0 or y >= self.dims[1]:
            return False
        player_at_loc = state[x][y]  # 1 or 2
        if player_at_loc == 0:
            return False
        if player is not None:
            if player_at_loc == player:
                return False
        # print "checking for capture of group at %i, %i"%(x,y)
        # print "stone %i"%player
        found_liberty = False
        while len(locs_to_check) > 0:
            # print "locs_to_check: "+str(locs_to_check)
            new_locs_to_check = []
            for i, j in locs_to_check:
                sc = [(i, j - 1), (i - 1, j), (i + 1, j), (i, j + 1)]
                hasNeighbor = False
                for c in sc:
                    if c[0] >= 0 and c[0] < self.dims[0] and c[1] >= 0 and c[1] < self.dims[1]:
                        v = state[c[0]][c[1]]
                        if v == 0:
                            # found a bordering unoccupied space, so no capture
                            return False
                            # found_liberty = True
                            # print "found liberty at %i, %i"%(c[0],c[1])
                        elif v == player_at_loc:
                            # print "found connected stone at %i, %i"%(c[0],c[1])
                            # if (c[0],c[1]) in new_locs_to_check:
                            #    print "skipping, loc is already in new_locs_to_check"
                            # if (c[0],c[1]) in connected_locs:
                            #    print "skipping, loc is already in connected_locs"
                            if (c[0], c[1]) not in new_locs_to_check and (c[0], c[1]) not in connected_locs:
                                # print "found connected stone at %i, %i"%(i,j)
                                new_locs_to_check.append((c[0], c[1]))
                    else:
                        pass
            locs_to_check = list(new_locs_to_check)
            connected_locs.extend(locs_to_check)
        connected_locs = list(set(connected_locs))
        # print "connected_locs: "+str(connected_locs)
        # remove captured stones
        updated_state = state.copy()
        for i, j in connected_locs:
            updated_state[i][j] = 0
        return updated_state

    def remove_dead(self):
        if self.temp_coords == None:
            return
        connected_locs = self.find_connected_locs(self.dead_removed_state, self.temp_coords)
        for i, j in connected_locs:
            self.dead_removed_state[i][j] = 0
        self.temp_coords = None

    def toggle_territory(self):
        if self.temp_coords == None:
            return
        connected_locs = self.find_connected_locs(self.dead_removed_state, self.temp_coords)
        for i, j in connected_locs:
            v = self.territory[i][j]
            if v == 0:
                self.territory[i][j] = 1
            elif v == 1:
                self.territory[i][j] = 2
            elif v == 2:
                self.territory[i][j] = 0
        self.temp_coords = None

    def assign_territory(self):
        ## automatically assign obvious territories
        # make list of all contiguous empty locations
        empty_regions = []
        for i in xrange(self.dims[0]):
            for j in xrange(self.dims[1]):
                if self.dead_removed_state[i][j] != 0:
                    continue
                empty_region = set(self.find_connected_locs(self.dead_removed_state, (i, j)))
                if empty_region not in empty_regions:
                    empty_regions.append(empty_region)
        # for each empty region, count unique neighbors (exact count doesn't matter)
        for r in empty_regions:
            found = {1: 0, 2: 0}
            for i, j in r:
                sc = [(i, j - 1), (i - 1, j), (i + 1, j), (i, j + 1)]
                for c in sc:
                    if not (c[0] >= 0 and c[0] < self.dims[0] and c[1] >= 0 and c[1] < self.dims[1]):
                        continue  # skip out-of-bounds
                    v = self.dead_removed_state[c[0]][c[1]]
                    if v != 0:
                        found[v] = 1
            # if only one player touches region, assign territory to that player
            if sum(found.values()) == 1:
                if found[1] == 1:
                    for i, j in r:
                        self.territory[i][j] = 1
                elif found[2] == 1:
                    for i, j in r:
                        self.territory[i][j] = 2

    def print_state(self, state):
        print ''
        for y in xrange(self.dims[1]):
            print ''.join(["%i" % x if x != 0 else '.' for x in state[:, y]])
        print ''

    def print_playable(self):
        for y in xrange(self.dims[1]):
            print ''.join(["%i" % x if x != 0 else '.' for x in self.playable[:, y]])

    def check_capture(self, state, x, y, player=None):
        # check for capture of any bordering stones    
        # This is inefficient, since we're fully iterating
        # over grouped stones multiple times
        sc = [(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)]
        # print "\nchecking for capture at %s, %s, %s, %s"%(sc[0],sc[1],sc[2],sc[3])
        # print "state:"

        updated_states = []
        for i, j in sc:
            updated_state = self.check_capture_loc(state, i, j, player=player)
            if updated_state is not False:
                updated_states.append(updated_state)
        # merge updated states (in case there are multiple unconnected killed groups)
        if len(updated_states) > 0:
            # print "multiple groups to be captured"
            updated_state = updated_states[0]
            for n in xrange(1, len(updated_states)):
                for i in xrange(self.dims[0]):
                    for j in xrange(self.dims[1]):
                        if updated_states[n][i][j] == 0:
                            updated_state[i][j] = updated_states[n][i][j]
            return updated_state
        else:
            return False

    def check_suicide(self, state, x, y):
        if self.check_capture_loc(state, x, y) is not False:
            return True
        else:
            return False

    def update_playable(self):
        # check each location on board for playability
        self.playable = self.states[-1] == 0  # exclude locations already played
        for i in xrange(self.dims[0]):
            for j in xrange(self.dims[1]):
                # print "checking playability at %i, %i"%(i,j)
                if self.playable[i][j] == 0:  # skip played positions
                    # print "skipping already played position"
                    continue
                # skip locations not bordered by any stones
                sc = [(i, j - 1), (i - 1, j), (i + 1, j), (i, j + 1)]
                hasNeighbor = False
                for c in sc:
                    if c[0] >= 0 and c[0] < self.dims[0] and c[1] >= 0 and c[1] < self.dims[1]:
                        # should make a func for within dims
                        if self.states[-1][c[0]][c[1]] != 0:
                            hasNeighbor = True
                            break
                    else:
                        continue
                if hasNeighbor is False:
                    # print "skipping position with no neighbors"
                    continue
                temp_state = self.states[-1].copy()
                temp_state[i][j] = self.current_player

                # check for capture or suicide
                capture_state = self.check_capture(temp_state, i, j, player=self.current_player)
                if capture_state is False:
                    suicide = self.check_suicide(temp_state, i, j)
                else:
                    suicide = self.check_suicide(capture_state, i, j)
                if suicide == True:
                    if capture_state is False:
                        self.playable[i][j] = 0  # disallow suicide moves
                # disallow moves that would result in a repeated game state
                if capture_state is not False:
                    # could iterate over all past states for super-ko, but longer calc
                    if np.array_equal(self.states[-2], capture_state):
                        self.playable[i][j] = 0
                        # self.print_state(self.states[-1])
                        # self.print_playable()

    def place_piece(self):
        if self.temp_coords == None:
            return
        if MUTE == False:
            choice(sounds).play()
        new_state = self.states[-1].copy()
        new_state[self.temp_coords[0]][self.temp_coords[1]] = self.current_player
        self.moves.append((self.current_player, self.temp_coords))
        # print "placed piece at %i, %i"%(self.temp_coords[0],self.temp_coords[1])
        capture_state = self.check_capture(new_state, self.temp_coords[0], self.temp_coords[1],
                                           player=self.current_player)
        if capture_state is not False:
            new_state = capture_state
        self.states.append(new_state)
        self.update_capture_counts()
        self.temp_coords = None
        self.state_index += 1
        if self.current_player == 1:
            self.current_player = 2
        elif self.current_player == 2:
            self.current_player = 1

        self.update_playable()
        # self.passed = False
        # print "updated playable positions"
        self.print_state(self.states[-1])

    def pass_turn(self):
        self.states.append(self.states[-1].copy())
        self.temp_coords = None
        self.state_index += 1
        self.moves.append((self.current_player, "pass"))
        # by AGA rules, passing costs a stone
        if self.current_player == 1:
            self.capture_counts[1].append(1)
            self.current_player = 2
        elif self.current_player == 2:
            self.capture_counts[2].append(1)
            self.current_player = 1
        self.update_playable()


board = Board(next(color_gen()), dims[dims_index])
screen.fill(bgcolor)
board.render()
pygame.display.flip()

need_render = True

while running:

    game_mode = board.game_modes[board.current_game_mode]
    if game_mode == "play":
        both = False
    else:
        both = True

    event = pygame.event.poll()
    if event.type == pygame.QUIT:
        break
    elif event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            break
        elif event.key == pygame.K_f:
            need_render = True
            # print "F key pressed"
            if fullscreen == False:
                fullscreen = True
                pygame.display.set_mode(full_res)
                current_res = full_res
                update_lw()
                # print "lw is %f"%lw
                pygame.display.toggle_fullscreen()
                board.prerender_cairo()
                # board.init_cairo_surface() # should move this outside the Board class
            else:
                fullscreen = False
                pygame.display.toggle_fullscreen()
                pygame.display.set_mode(window_res)
                current_res = window_res
                update_lw()
                # board.init_cairo_surface()
                board.prerender_cairo()
                # print "lw is %f"%lw
        elif event.key == pygame.K_g:
            print "g key pressed"
            need_render = True
            board.grid_brightness_index += 1
            if board.grid_brightness_index >= len(board.grid_brightness_factors):
                board.grid_brightness_index = 0
            board.set_grid_color()
            board.prerender_cairo()
    # For undo, require a mouse down on the last played location, and
    # a mouse up on the same location
    elif ( event.type == pygame.MOUSEBUTTONDOWN
           and event.button == LEFT
           and latency_timer.check() ):
        need_render = True
        mouse_down = True
        x, y = event.pos
        v = board.test_pass((x, y), both=both)
        if v is not False:
            board.button_down = v  # set button pressed
        else:
            board.button_down = 0
            board.update_temp_coords((x, y))
            board.check_undo((x, y), action="down")
            # print "mouse down at "+str(event.pos)
    elif ( event.type == pygame.MOUSEBUTTONUP
            and event.button == LEFT
            and latency_timer.check()
            and mouse_down == True ):
        need_render = True
        mouse_down = False
        x, y = event.pos
        # TODO: move this logic to a board class method
        if board.test_pass((x, y), both=both) is not False:
            # one of the player buttons was pressed
            if game_mode == "play":
                board.last_stone_coords.append(None)
                if len(board.moves) > 0 and board.moves[-1][1] == "pass":
                    # move to scoring stages if both players pass in turn
                    board.pass_turn()
                    # according to AGA rules, both players must play the same number of
                    # stones, so make additional pass if we end on player 2
                    if board.current_player == 2:
                        board.pass_turn()
                    print ">>>>>> Starting dead group removal stage"
                    notifier.update(text="Game over. Tap stones to remove dead groups. Tap other buttons to continue.", thresh=-1)
                    board.current_game_mode += 1
                    board.dead_removed_state = board.states[-1].copy()
                else:
                    if board.button_down == 3:
                        dims_index += 1
                        if dims_index > len(dims) - 1:
                            dims_index = dims_index - len(dims)
                        board = Board(next(color_gen()), dims[dims_index])
                    else:
                        notifier.update(text="Player %i passed"%board.current_player)
                        board.pass_turn()
            elif game_mode == "dead removal":
                print ">>>>>> Starting territory assignment stage"
                notifier.update(text="Game over. Tap territory to change assignment", thresh=-1)
                board.update_capture_counts()  # add removed dead groups to capture counts
                board.assign_territory()
                board.current_game_mode += 1
            elif game_mode == "territory assignment":
                print "\n\nGame complete:"
                print "Player 1 score: %0.1f" % board.final_scores[1]
                print "Player 2 score: %0.1f" % board.final_scores[2]
                print ">>>>>> Starting new game"
                notifier.update(text="Starting new game")
                board = Board(next(color_gen()), dims[dims_index])
        else:
            board.update_temp_coords((x, y), do_action=True)
            board.check_undo((x, y), action="up")
            # print "placed piece"
            #notifier.update(text="Placed piece for player %i"%(board.current_player))

        board.button_down = 0
        # print "mouse up at "+str(event.pos)

        latency_timer.reset()

    elif ( event.type == pygame.MOUSEMOTION
           and mouse_down == True
           and latency_timer.check() ):
        need_render = True
        x, y = event.pos
        v = board.test_pass((x, y), both=both)
        if v is not False:
            board.button_down = v  # set button pressed
        else:
            board.button_down = 0
            board.update_temp_coords((x, y))
            board.check_undo((x, y), action="move")
            # print "mouse moved to "+str(event.pos)
    elif event.type == pygame.USEREVENT and need_render == True:
        screen.fill(bgcolor)
        board.render()  # only do this so many times per second, and
        # only if we need to (something has changed)
        pygame.display.flip()
        need_render = False
    pygame.time.wait(0)
