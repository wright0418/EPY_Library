from machine import Pin, Timer
import utime
import math
import _thread


class Music:
    def __init__(self, tim, pin=Pin.epy.P9):
        self.tone_idx = {'R': 0, 'A': 0, 'Ab': -1, 'G#': -1, 'G': -2, 'Gb': -3, 'F#': -3, 'F': -4, 'E': -5,
                         'Eb': -6, 'D#': -6, 'D': -7, 'Db': -8, 'C#': -8, 'C': -9, 'B': 2, 'Bb': 1, 'A#': 1}
        self._freqA4 = 440  # Hz
        self._buzzer_pin = Pin(pin, Pin.OUT)
        self._timer = tim
        self._timer.init(freq=self._freqA4*2)
        self.ticks = 4
        self.bpm = 120
        self._lv = 4
        self._ticks = (60000/((self.bpm)*self.ticks))
        self._state = 'STOP'
        self.loop = False
        self.music = []
        _thread.start_new_thread(self.play_music, ())

    def play_music(self):
        while True:
            if self._state == "START":
                for play_tone in self.music:
                    #print ('-')
                    if self._state == "STOP":
                        break
                    play_tone = play_tone.split(":")
                    try:
                        tone_ = None
                        if play_tone[0][0] != 'R':
                            tone_ = play_tone[0][0:2] if len(
                                play_tone[0]) == 3 else play_tone[0][0:1]
                            if play_tone[0][-1].isdigit():
                                self._lv = int(play_tone[0][-1])
                            playFreq = self._freqA4 * \
                                math.pow(1.059463, (4-self._lv) * -
                                         12+self.tone_idx[tone_])
                        else:
                            playFreq = 0
                        if(len(play_tone) == 2):
                            self._ticks = (60000/((self.bpm)*self.ticks)
                                           )*(int(play_tone[1]))
                        self._playFreq(playFreq, int(self._ticks))
                    except KeyError:
                        print("tone not find")
                        self._state = "STOP"
                if self.loop and self._state != "STOP":
                    self._state = "START"
                else:
                    self._state = "STOP"
                    self.music = []
        # utime.sleep(0.1)

    def tempo(self, ticks=4, bpm=120):
        self.ticks = ticks
        self.bpm = bpm

    def _buzzer_toggle(self, t):
        self._buzzer_pin.value(~self._buzzer_pin.value() & 0x0001)

    def stop(self):
        self._state = "STOP"
        while self.music:
            pass

    def getState(self):
        return self._state

    def play(self, music, loop=False):
        if self._state == "START":
            self.stop()
        self.music = music
        self.loop = loop
        self._state = "START"

    def playFreq(self, playFreq, playtime_ms):
        if self._state == 'STOP':
            self._state = 'START'
            self._playFreq(playFreq, playtime_ms)
            self._state = 'STOP'

    def _playFreq(self, playFreq, playtime_ms):
        self._timer.init(freq=int(playFreq*2))
        self._timer.callback(self._buzzer_toggle)
        preTime = utime.ticks_ms()
        while (utime.ticks_ms() - preTime) < (playtime_ms):
            utime.sleep_ms(1)
        self._timer.callback(None)


if __name__ == '__main__':
    timer = Timer(0)
    music = Music(timer, pin=Pin.epy.P22)

    song_105 = ["E4:2", "E", "F", "E", "D", "E", "A3:4", "D4:2",
                "C", "A3", "C4:4", "D", "D:2", "D", "E", "D:2", "C", "D"]
    DoReMe = ["C", "D", "E", "F", "G", "A", "B"]

    music.play(song_105, loop=True)
    utime.sleep(3)
    music.play(DoReMe)
    utime.sleep(10)
    music.stop()
    music.play(song_105)
    utime.sleep(3)
    music.stop()

    for freq in range(10, 2000, 20):
        music.playFreq(freq, 20)

    for times in range(2):
        music.playFreq(950, 600)
        music.playFreq(700, 400)
