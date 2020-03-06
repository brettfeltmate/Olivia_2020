# -*- coding: utf-8 -*-

__author__ = "Brett Feltmate"

import klibs
from klibs import P
from klibs.KLUtilities import deg_to_px, smart_sleep, hide_mouse_cursor
from klibs.KLGraphics import fill, blit, flip, clear
from klibs.KLConstants import STROKE_CENTER, RC_KEYPRESS, TK_MS, NA
from klibs.KLAudio import Tone
from klibs.KLGraphics import KLDraw as kld
from klibs.KLResponseCollectors import KeyMap
from klibs.KLUserInterface import ui_request, any_key
from klibs.KLCommunication import message

import random
import sdl2

# Useful constants
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
RED = (255, 0, 0, 255)

VIS_LEFT = 'vis_left'
VIS_RIGHT = 'vis_right'
NO_CUE = 'no_cue'
TEMP_CUE = 'temporal'
LEFT = 'left'
RIGHT = 'right'
TOP_RIGHT = "top_right"
TOP_LEFT = 'top_left'
BOTTOM_RIGHT = 'bottom_right'
BOTTOM_LEFT = 'bottom_left'
FIX = 'fixation'


class Olivia_2020(klibs.Experiment):

    def setup(self):
        # Font styles for feedback
        self.txtm.add_style(label='correct', color=WHITE)
        self.txtm.add_style(label='incorrect', color=RED)

        # Stimulus properties #

        # Placeholder(s)
        placeholder_size = deg_to_px(2.0)
        uncued_thick = deg_to_px(0.2)
        cued_thick = deg_to_px(0.5)
        self.cued_stroke = [cued_thick, WHITE, STROKE_CENTER]
        self.uncued_stroke = [uncued_thick, WHITE, STROKE_CENTER]

        # Tone
        tone_type = 'sine'
        tone_duration = 50  # ms
        tone_volume = 0.6   # moderate volume

        # Fixation
        fix_size = deg_to_px(0.8)
        fix_thick = deg_to_px(0.1)

        # Target
        target_size = deg_to_px(0.8)

        # Stimlus construction
        self.fixation = kld.FixationCross(size=fix_size, thickness=fix_thick, fill=WHITE)
        self.audio_tone = Tone(duration=tone_duration, wave_type=tone_type, volume=tone_volume)
        self.target = kld.Circle(diameter=target_size, fill=WHITE)

        self.box_left = kld.Rectangle(width=placeholder_size, stroke=self.uncued_stroke)
        self.box_right = kld.Rectangle(width=placeholder_size, stroke=self.uncued_stroke)

        # Stimulus locations
        offset = deg_to_px(4.0) if P.development_mode else deg_to_px(8.0)  # Normal offset too wide for my laptop
        self.locs = {
            TOP_LEFT: [P.screen_c[0] - offset, P.screen_c[1] - offset],
            TOP_RIGHT: [P.screen_c[0] + offset, P.screen_c[1] - offset],
            BOTTOM_LEFT: [P.screen_c[0] - offset, P.screen_c[1] + offset],
            BOTTOM_RIGHT: [P.screen_c[0] + offset, P.screen_c[1] + offset]
        }

        coinflip = random.choice([True, False])

        if coinflip:
            self.left_key, self.right_key = 'up', 'down'
            self.keymap = KeyMap(
                "response", ['left', 'right'],
                [LEFT, RIGHT],
                [sdl2.SDLK_UP, sdl2.SDLK_DOWN]
            )

        else:
            self.left_key, self.right_key = 'down', 'up'
            self.keymap = KeyMap(
                "response", ['left', 'right'],
                [LEFT, RIGHT],
                [sdl2.SDLK_DOWN, sdl2.SDLK_UP]
            )

        factor_mask = {'cue_type': ['vis_left', 'vis_right', 'temporal', 'temporal', 'no_cue', 'no_cue'],
                       'tone_trial': [True, False]}

        self.ctoa_practice = [100, 250, 850]
        self.ctoa_testing = [100, 250, 850]

        random.shuffle(self.ctoa_practice)
        random.shuffle(self.ctoa_testing)


        self.insert_practice_block(block_nums=[1, 2, 3], trial_counts=12, factor_mask=factor_mask)

    def block(self):
        if P.block_number == 1:
            self.present_instructions()

        if P.practicing:
            self.ctoa = self.ctoa_practice.pop()

        else:
            self.ctoa = self.ctoa_testing.pop()

        if P.block_number > 1:
            progress = "Starting block {0} of {1}.".format(P.block_number, P.blocks_per_experiment)
            if P.practicing:
                progress += "\n[practice block]"
            else:
                progress += "\n[testing block]"

            self.anykey_msg(progress)



    def setup_response_collector(self):

        self.rc.uses(RC_KEYPRESS)
        self.rc.terminate_after = [600, TK_MS]
        self.rc.display_callback = self.display_refresh
        self.rc.display_kwargs = {'target': True}
        self.rc.keypress_listener.key_map = self.keymap
        self.rc.keypress_listener.interrupts = True

    def trial_prep(self):
        if self.cue_type == VIS_RIGHT:
            subset = [TOP_RIGHT, BOTTOM_RIGHT]

        elif self.cue_type == VIS_LEFT:
            subset = [BOTTOM_LEFT, TOP_LEFT]

        else:
            subset = None

        self.set_target_loc(subset)

        self.target_side = str.split(self.target_loc, '_')[1]

        events = []
        events.append(['cue_on', 250])
        events.append(['cue_off', events[-1][1] + 50])
        events.append(['target_on', events[-1][1] + self.ctoa])

        self.evm.register_tickets(events)

        self.pre_trial()

        self.display_refresh()

    def trial(self):
        hide_mouse_cursor()

        while self.evm.before('cue_on'):
            ui_request()

        self.display_refresh(cue=self.cue_type, tone=self.tone_trial)

        while self.evm.before('cue_off'):
            ui_request()

        self.display_refresh()

        while self.evm.before('target_on'):
            ui_request()

        self.rc.collect()

        if self.rc.keypress_listener.response_count != 0:
            response, rt = self.rc.keypress_listener.response()

        else:
            response, rt = NA, NA

        self.present_feedback(rt=rt, response=response)

        clear()

        return {
            "block_num": P.block_number,
            "trial_num": P.trial_number,
            "practicing": str(P.practicing),
            'cue_type': self.cue_type,
            'ctoa': self.ctoa,
            'target_loc': self.target_loc,
            'target_side': self.target_side,
            'tone_trial': str(self.tone_trial),
            'response': response,
            'rt': rt
        }

    def trial_clean_up(self):
        self.box_right.stroke = self.uncued_stroke
        self.box_left.stroke = self.uncued_stroke

    def clean_up(self):
        pass

    def pre_trial(self):

        fill()
        blit(self.fixation, location=P.screen_c, registration=5)
        flip()

        any_key()

    def display_refresh(self, cue=None, tone=False, target=False):

        fill()

        blit(self.fixation, location=P.screen_c, registration=5)

        if cue is not None:
            if cue == TEMP_CUE:
                self.box_left.stroke = self.cued_stroke
                self.box_right.stroke = self.cued_stroke

            elif cue == VIS_LEFT:
                self.box_left.stroke = self.cued_stroke

            elif cue == VIS_RIGHT:
                self.box_right.stroke = self.cued_stroke

        else:
            self.box_right.stroke = self.uncued_stroke
            self.box_left.stroke = self.uncued_stroke

        blit(self.box_left, registration=5, location=self.locs['top_left'])
        blit(self.box_left, registration=5, location=self.locs['bottom_left'])
        blit(self.box_right, registration=5, location=self.locs['top_right'])
        blit(self.box_right, registration=5, location=self.locs['bottom_right'])

        if target:
            blit(self.target, registration=5, location=self.locs[self.target_loc])

        flip()

        if tone:
            self.audio_tone.play()

    def present_feedback(self, rt, response):

        fill()

        if rt is not NA:
            # Round off decimals
            msg = int(rt)

        else:
            msg = "Respond faster!"

        style = "correct" if response == self.target_side else 'incorrect'

        message(msg, style=style, location=P.screen_c, registration=5, blit_txt=True)

        flip()

        smart_sleep(400)

    def set_target_loc(self, subset):

        if subset is not None:
            newDict = {key: value for (key, value) in self.locs.items() if key in subset}
            self.target_loc, self.target_coord = random.choice(newDict.items())

        else:
            self.target_loc, self.target_coord = random.choice(self.locs.items())

    def anykey_msg(self, msg):
        msg += "\n\n{press any key to continue}"

        fill()
        message(msg, location=P.screen_c, registration=5, align='center', blit_txt=True)
        flip()

        any_key()

    def present_instructions(self):

        msg = "During this experiment, each trial will begin with a cross centre-screen."

        self.anykey_msg(msg)

        fill()
        blit(self.fixation, location=P.screen_c, registration=5)
        flip()
        smart_sleep(1000)

        msg = ("When you see this, press spacebar to start the rest of the trial.\n" +
               "Once you do, four boxes will appear around it.")

        self.anykey_msg(msg)

        fill()
        blit(self.fixation, location=P.screen_c, registration=5)
        flip()

        smart_sleep(500)

        self.display_refresh()
        smart_sleep(1000)

        msg = ("Since you start each trial yourself, if your eyes get tired\n" +
               "you can take a moment before starting the next trial.")

        self.anykey_msg(msg)

        msg = "Shortly after the boxes appear, \nsome number of boxes may 'flash' and a tone might be played."

        self.anykey_msg(msg)

        self.cue_type = TEMP_CUE
        self.display_refresh()
        smart_sleep(250)
        self.display_refresh(cue=True, tone=True)
        smart_sleep(50)
        self.display_refresh()
        smart_sleep(1000)

        msg = "Once the boxes return to normal, a white circle will appear shortly after in one of the boxes."

        self.anykey_msg(msg)

        msg = ("If only the left or right boxes flash, the circle will appear on that side.\n" +
               "If all, or none, of the boxes flash, then the circle could appear on either side."
               )

        self.anykey_msg(msg)

        self.cue_type = VIS_LEFT
        self.target_loc = TOP_LEFT

        self.display_refresh()
        smart_sleep(250)
        self.display_refresh(cue=True, tone=True)
        smart_sleep(50)
        self.display_refresh()
        smart_sleep(250)
        self.display_refresh(target=True)
        smart_sleep(600)

        fill()
        blit(self.fixation, location=P.screen_c, registration=5)
        flip()
        smart_sleep(500)

        self.cue_type = VIS_RIGHT
        self.target_loc = BOTTOM_RIGHT

        self.display_refresh()
        smart_sleep(250)
        self.display_refresh(cue=True)
        smart_sleep(50)
        self.display_refresh()
        smart_sleep(250)
        self.display_refresh(target=True)
        smart_sleep(600)

        fill()
        blit(self.fixation, location=P.screen_c, registration=5)
        flip()
        smart_sleep(500)

        self.cue_type = TEMP_CUE
        self.target_loc = TOP_RIGHT

        self.display_refresh()
        smart_sleep(250)
        self.display_refresh(cue=True, tone=True)
        smart_sleep(50)
        self.display_refresh()
        smart_sleep(250)
        self.display_refresh(target=True)
        smart_sleep(600)

        fill()
        blit(self.fixation, location=P.screen_c, registration=5)
        flip()
        smart_sleep(500)

        self.cue_type = TEMP_CUE
        self.target_loc = BOTTOM_LEFT

        self.display_refresh()
        smart_sleep(250)
        self.display_refresh(cue=True, tone=True)
        smart_sleep(50)
        self.display_refresh()
        smart_sleep(250)
        self.display_refresh(target=True)
        smart_sleep(600)

        msg = ("Once the target appears, you task is to indicate on which side it appeared.\n" +
               "{0} key = left boxes, {1} key = right boxes"
               ).format(self.left_key.upper(), self.right_key.upper())

        self.anykey_msg(msg)

        msg = ("When you make a response, your reaction time will be provided to you.\n" +
               "Otherwise, you'll be asked to respond faster.\nTry to keep this number as" +
               " low as possible, while remaining accurate.")

        self.anykey_msg(msg)

        msg = ("Feedback for correct responses will be provided in white.\n" +
               "For incorrect responses, it will be in red.")

        self.anykey_msg(msg)

        msg = "The experiment will now begin with a few practice rounds to familiarize you with the task."

        self.anykey_msg(msg)
