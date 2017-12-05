#!/usr/bin/env python2

import os
import wave
import pyaudio
import tempfile
import subprocess
import pygame
import time
import alsaaudio
import event_checker
import mplayer


def play(filename):
    soundObj = pygame.mixer.Sound(filename)
    soundObj.play()

def say(phrase):
    filename = tts(phrase)
    play(filename)
    os.remove(filename)


def tts(phrase):
    voice = "en"
    amplitude = 60
    pitch_adjustment = 50
    words_per_minute = 200

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        fname = f.name
    cmd = [
        'espeak', '-v', voice,
        '-a', str(amplitude),
        '-p', str(pitch_adjustment),
        '-s', str(words_per_minute),
        '-w', fname,
        phrase]

    with tempfile.TemporaryFile() as f:
        subprocess.call(cmd, stdout=f, stderr=f)
        f.seek(0)
        output = f.read()
    return fname


class Recorder():
    RATE = 22050
    CHUNK = 1024
    def __init__(self):
        self.audio_object = pyaudio.PyAudio()
        self.frames = []
        self.stream = None

    def start(self):
        play('sounds/beep_hi.wav')
        self.frames = []
        self.stream = self.audio_object.open(format=pyaudio.paInt16,
                                             channels=1,
                                             rate=self.RATE,
                                             input=True,
                                             stream_callback=self.record_callback)

    def record_callback(self, in_data, frame_count, time_info, status):
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    def terminate(self):
        self.audio_object.terminate()

    def flush(self, filename):
        self.stream.stop_stream()
        self.stream.close()
        with open(filename, "w+b") as f:
            wav_fp = wave.open(f, 'wb')
            wav_fp.setnchannels(1)
            wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wav_fp.setframerate(self.RATE)
            wav_fp.writeframes(''.join(self.frames))
            wav_fp.close()
        play("sounds/beep_lo.wav")


class Player():
    def __init__(self, width, height, blocksize):
        self.width, self.height, self.blocksize = width, height, blocksize
        self.color_board = (80, 100, 100)
        self.color_time_bar = (150, 150, 150)
        self.color_time_point = (20, 80, 80)
        self.color_player_button = (150, 150, 150)
        self.color_speed_bar = (150, 150, 150)
        self.color_speed_point = (20, 80, 80)
        self.color_volume_bar = (150, 150, 150)
        self.color_volume_point = (20, 80, 80)

        self.mplayer = mplayer.Player(('-vo', 'null'))
        self.last_action = event_checker.EVENT_NONE
        self.mixer = alsaaudio.Mixer()
        self.volume = self.mixer.getvolume()[0]
        self.speed = 30
        self.point = 0
        self.latest_volume = 0
        self.latest_speed = 0
        self.latest_point = 0
        self.filename = None

    def load(self, filename):
        self.point = 0
        self.filename = filename
        self.latest_point = 0
        self.mplayer.stop()
        self.mplayer.loadfile(self.filename)
        self.mplayer.pause()

    def on_action(self, action, pos, event):
        k = 0.618
        if action == event_checker.EVENT_RIGHT_CLICK:
            self.mplayer.stop()
        elif action == event_checker.EVENT_LEFT_CLICK or action == event_checker.EVENT_SPACE:
            if self.mplayer.time_pos and self.mplayer.time_pos > 0:
                self.mplayer.pause()
            else:
                self.mplayer.loadfile(self.filename)
                self.mplayer.pause()
                self.point = 0

        elif action == event_checker.EVENT_LEFT_DRAG:
            x, y = pos
            dx = 100*x/(self.width * (1 - (1-k) * (1-k))*k)
            if self.last_action != action:
                self.latest_point = self.point
            self.point = self.latest_point + int(dx)
            if self.point < 0:
                self.point = 0
            elif self.point > 100:
                self.point = 100
            self.mplayer.percent_pos = self.point

            dy = 100*y/(self.height * (1-k) * (1-k) * (1-k))
            if self.last_action != action:
                self.latest_volume = self.volume
            self.volume = self.latest_volume - int(dy)
            if self.volume < 0:
                self.volume = 0
            elif self.volume > 100:
                self.volume = 100
            self.mixer.setvolume(self.volume)

        elif action == event_checker.EVENT_RIGHT_DRAG:
            pass

        elif (action == event_checker.EVENT_WHEEL_UP or action == event_checker.EVENT_WHEEL_DOWN) or (
                action == event_checker.EVENT_KEYUP or action == event_checker.EVENT_KEYDOWN):

            if action == event_checker.EVENT_WHEEL_UP or action == event_checker.EVENT_KEYUP:
                dy = 10
            elif action == event_checker.EVENT_WHEEL_DOWN or action == event_checker.EVENT_KEYDOWN:
                dy = -10

            if event.button3 and not event.button1:
                self.speed += int(dy)
                if self.speed < 0:
                    self.speed = 0
                elif self.speed > 100:
                    self.speed = 100
                self.mplayer.speed = (0.7 + self.speed / 100.0)

            if not event.button1 and not event.button3:
                self.volume += int(dy)
                if self.volume < 0:
                    self.volume = 0
                elif self.volume > 100:
                    self.volume = 100
                self.mixer.setvolume(self.volume)

            if event.button1 and not event.button3:
                self.point += int(-dy/5)
                if self.point < 0:
                    self.point = 0
                elif self.point > 100:
                    self.point = 100
                self.mplayer.percent_pos = self.point

        elif action == event_checker.EVENT_BOTH:
            say("press both")
        elif action == event_checker.EVENT_BOTH_RELEASE or action == event_checker.EVENT_ENTER:
            if self.mplayer.time_pos and self.mplayer.time_pos > 0:
                self.mplayer.stop()
            self.point = 0
        self.last_action = action


    def draw_player(self, surface):
        self.point = self.mplayer.percent_pos
        k = 0.618
        # board
        color = self.color_board
        top = self.height * (1-k) * k
        left = self.width * (1-k) * (1-k) / 2
        height = self.height * (1-k) * (1-k)
        width = self.width * (1 - (1-k) * (1-k))
        rect = pygame.Rect(left, top, width, height)
        pygame.draw.rect(surface, color, rect, 0)

        # time bar
        color = self.color_time_bar
        time_top = top + height * k
        time_left = left + width * (1-k) / 2
        time_height = height * (1-k) * (1-k) * (1-k) * (1-k)
        time_width = width * k
        time_rect = pygame.Rect(time_left, time_top, time_width, time_height)
        pygame.draw.rect(surface, color, time_rect, 0)

        # time bar point
        color = self.color_player_button
        time_bar_point_d = time_height * 2
        time_bar_point_top = time_top + time_height/2
        time_bar_point_left = time_left + time_width * self.point/100
        pygame.draw.circle(surface, color, (int(time_bar_point_left), int(time_bar_point_top)), int(time_bar_point_d), 0)

        # speed bar
        color = self.color_speed_bar
        speed_height = height * (1-k)
        speed_top = top + (height - speed_height)/2
        speed_left = left + (time_left - left) * k
        speed_width = time_height
        speed_rect = pygame.Rect(speed_left, speed_top, speed_width, speed_height)
        pygame.draw.rect(surface, color, speed_rect, 0)

        # speed bar point
        color = self.color_player_button
        speed_bar_point_d = speed_width * 2
        speed_bar_point_top = speed_top + speed_height - speed_height * self.speed/100
        speed_bar_point_left = speed_left + speed_width/2
        pygame.draw.circle(surface, color, (int(speed_bar_point_left), int(speed_bar_point_top)), int(speed_bar_point_d), 0)

        # volume bar
        color = self.color_volume_bar
        volume_height = height * (1-k)
        volume_top = top + (height - volume_height)/2
        volume_width = time_height
        volume_left = left + (width - (time_left - left) * k) - volume_width
        volume_rect = pygame.Rect(volume_left, volume_top, volume_width, volume_height)
        pygame.draw.rect(surface, color, volume_rect, 0)

        # volume bar point
        color = self.color_player_button
        volume_bar_point_d = volume_width * 2
        volume_bar_point_top = volume_top + volume_height - volume_height * self.volume/100
        volume_bar_point_left = volume_left + volume_width/2
        pygame.draw.circle(surface, color, (int(volume_bar_point_left), int(volume_bar_point_top)), int(volume_bar_point_d), 0)

        # player button
        color = self.color_player_button
        player_d = height * (1-k) * (1-k)
        player_top = top + height * (1-k)
        player_left = left + width/2
        pygame.draw.circle(surface, color, (int(player_left), int(player_top)), int(player_d), 0)
