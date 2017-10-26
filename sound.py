#!/usr/bin/env python2

import os
import wave
import pyaudio
import tempfile
import subprocess
import pygame
import time
import alsaaudio


def play(filename):
    soundObj = pygame.mixer.Sound(filename)
    soundObj.play()


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
        self.filename = None
        self.color_board = (80, 100, 100)
        self.color_time_bar = (150, 150, 150)
        self.color_time_point = (20, 80, 80)
        self.color_player_button = (150, 150, 150)
        self.color_speed_bar = (150, 150, 150)
        self.color_speed_point = (20, 80, 80)
        self.color_volume_bar = (150, 150, 150)
        self.color_volume_point = (20, 80, 80)

        self.speed = 30
        self.volume = 50
        self.point = 0
        self.latest_speed = 30
        self.latest_volume = 50
        self.latest_point = 0

        self.last_action = ""
        self.audio_object = pyaudio.PyAudio()
        self.mixer = alsaaudio.Mixer()

        self.volume = self.mixer.getvolume()[0]


    def play_callback(self, in_data, frame_count, time_info, status):
        data = self.wf.readframes(frame_count)
        self.point = 100 * self.wf.tell() / self.nframes
        return (data, pyaudio.paContinue)


    def load(self, filename):
        self.filename = filename
        self.wf = wave.open(self.filename, 'rb')
        self.nframes = self.wf.getnframes()
        self.nchannels = self.wf.getnchannels()
        self.nsampwidth = self.wf.getsampwidth()
        self.nframerate = self.wf.getframerate()
        self.point = 0
        self.latest_point = 0
        self.stream = None
        self.init_stream()


    def init_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.stream = self.audio_object.open(format=self.audio_object.get_format_from_width(self.nsampwidth),
                                  channels=self.nchannels,
                                  rate=int(self.nframerate * (0.7 + self.speed / 100.0)),
                                  output=True,
                                  stream_callback=self.play_callback)


    def on_action(self, action, pos, event):
        k = 0.618

        if action == "enter":
            say("play or pause")
        elif action == "right":
            self.stream.close()
            self.wf.close()
        elif action == "left":
            if self.stream.is_active():
                self.stream.stop_stream()
            elif not self.stream.is_stopped():
                self.stream.stop_stream()
                self.wf.rewind()
                self.point = 0
            else:
                self.stream.start_stream()

        elif action == "left-drag":
            x, y = pos
            dx = 100*x/(self.width * (1 - (1-k) * (1-k))*k)
            if self.last_action != action:
                self.latest_point = self.point
            self.point = self.latest_point + int(dx)
            if self.point < 0:
                self.point = 0
            elif self.point > 100:
                self.point = 100
            self.wf.setpos(int(self.point * self.nframes / 100))

            dy = 100*y/(self.height * (1-k) * (1-k) * (1-k))
            if self.last_action != action:
                self.latest_volume = self.volume
            self.volume = self.latest_volume - int(dy)
            if self.volume < 0:
                self.volume = 0
            elif self.volume > 100:
                self.volume = 100
            self.mixer.setvolume(self.volume)

        elif action == "right-drag":
            pass

        elif action == "wheel-up" or action == "wheel-down":
            if action == "wheel-up":
                dy = 10
            elif action == "wheel-down":
                dy = -10
            self.speed += int(dy)
            if self.speed < 0:
                self.speed = 0
            elif self.speed > 100:
                self.speed = 100

            self.init_stream()

        elif action == "both":
            say("press both ")
        elif action == "!both":
            if self.stream.is_active():
                self.stream.stop_stream()
            elif not self.stream.is_stopped():
                self.stream.stop_stream()
            self.wf.rewind()
            self.point = 0
        self.last_action = action


    def draw_player(self, surface):
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
