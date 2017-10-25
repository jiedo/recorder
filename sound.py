#!/usr/bin/env python2

import os
import wave
import pyaudio
import tempfile
import subprocess
import pygame
import time


def activeListenToAllOptions(audio_object):
    """
        Records until a second of silence or times out after 12 seconds
        Returns a list of the matching options or None
    """
    RATE = 16000
    CHUNK = 1024
    LISTEN_TIME = 4
    play('sounds/beep_hi.wav')
    # prepare recording stream
    stream = audio_object.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=RATE,
                              input=True,
                              frames_per_buffer=CHUNK)
    frames = []
    # increasing the range # results in longer pause after command
    # generation
    for i in range(0, RATE / CHUNK * LISTEN_TIME):
        data = stream.read(CHUNK)
        frames.append(data)

    play('sounds/beep_lo.wav')
    # save the audio data
    stream.stop_stream()
    stream.close()

    filename = "rec/%d.%d" % (int(time.time()), 4)
    with open(filename, "w+b") as f:
        wav_fp = wave.open(f, 'wb')
        wav_fp.setnchannels(1)
        wav_fp.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
        wav_fp.setframerate(RATE)
        wav_fp.writeframes(''.join(frames))
        wav_fp.close()


def play(filename):
    # FIXME: Use platform-independent audio-output here
    # See issue jasperproject/jasper-client#188
    soundObj = pygame.mixer.Sound(filename)
    soundObj.play()
    return
    cmd = ['aplay', '-D', 'default', str(filename)]
    with tempfile.TemporaryFile() as f:
        subprocess.call(cmd, stdout=f, stderr=f)
        f.seek(0)
        output = f.read()


def say(phrase):
    voice = "en"
    pitch_adjustment = 40
    words_per_minute = 200

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        fname = f.name
    cmd = ['espeak', '-v', voice,
                     '-p', str(pitch_adjustment),
                     '-s', str(words_per_minute),
                     '-w', fname,
                     phrase]

    with tempfile.TemporaryFile() as f:
        subprocess.call(cmd, stdout=f, stderr=f)
        f.seek(0)
        output = f.read()
    play(fname)
    os.remove(fname)


class Recorder():
    RATE = 22000
    CHUNK = 1024

    def __init__(self):
        self.audio_object = pyaudio.PyAudio()
        self.frames = []
        self.stream = None

    def start(self):
        play('sounds/beep_hi.wav')
        # prepare recording stream
        self.stream = self.audio_object.open(format=pyaudio.paInt16,
                   channels=1,
                   rate=self.RATE,
                   input=True,
                   frames_per_buffer=self.CHUNK)
        self.frames = []

    def breath(self):
        # 0.1 second delay
        for i in range(0, self.RATE / self.CHUNK /10):
            data = self.stream.read(self.CHUNK)
            self.frames.append(data)

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
        self.filename = None
        self.color_board = (80, 100, 100)
        self.color_time_bar = (150, 150, 150)
        self.color_time_point = (20, 80, 80)
        self.color_player_button = (150, 150, 150)
        self.color_speed_bar = (150, 150, 150)
        self.color_speed_point = (20, 80, 80)
        self.color_volume_bar = (150, 150, 150)
        self.color_volume_point = (20, 80, 80)

        self.speed = 50
        self.volume = 50
        self.point = 50

        self.latest_speed = 50
        self.latest_volume = 50
        self.latest_point = 50

        self.last_action = ""
        self.soundObj = None
        self.is_stated = False
        self.is_paused = False

    def load(self, filename):
        self.filename = filename
        pygame.mixer.music.load(filename)
        self.point = 0
        self.latest_point = 0
        self.is_stated = False
        self.is_paused = False
        self.soundObj = pygame.mixer.Sound(filename)


    def on_action(self, action, pos, event):
        k = 0.618

        if action == "enter":
            say("play or pause")
        elif action == "right":
            pygame.mixer.music.rewind()
            self.is_stated = False
        elif action == "left":
            if not self.is_stated:
                pygame.mixer.music.play()
                self.is_stated = True
                self.is_paused = False
            else:
                if self.is_paused == False:
                    pygame.mixer.music.pause()
                    self.is_paused = True
                else:
                    pygame.mixer.music.unpause()
                    self.is_paused = False

        elif action == "left-drag":
            x, _ = pos
            dx = 100*x/(self.width * (1 - (1-k) * (1-k))*k)
            if self.last_action != action:
                self.latest_point = self.point
            self.point = self.latest_point + int(dx)
            if self.point < 0:
                self.point = 0
            elif self.point > 100:
                self.point = 100
            # pygame.mixer.music.set_pos(self.point*100)

        elif action == "right-drag":
            _, y = pos
            dy = 100*y/(self.height * (1-k) * (1-k) * (1-k))
            if self.last_action != action:
                self.latest_speed = self.speed
            self.speed = self.latest_speed + int(dy)
            if self.speed < 0:
                self.speed = 0
            elif self.speed > 100:
                self.speed = 100

        elif action == "wheel-up" or action == "wheel-down":
            if action == "wheel-up":
                dy = 10
            elif action == "wheel-down":
                dy = -10
            self.volume += int(dy)
            if self.volume < 0:
                self.volume = 0
            elif self.volume > 100:
                self.volume = 100
            pygame.mixer.music.set_volume(self.volume/100.0)

        elif action == "both":
            say("press both ")
        elif action == "!both":
            say("release both ")

        self.last_action = action


    def draw_player(self, surface):
        self.point = int(pygame.mixer.music.get_pos()/100)
        if self.point > 100:
            self.point = 100
        # volume = pygame.mixer.music.get_volume()
        # self.volume = volume

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
        speed_bar_point_top = speed_top + speed_height * self.speed/100
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
