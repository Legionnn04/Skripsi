import os, sys

# Fix stdout/stderr None saat di-bundle PyInstaller --windowed
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')

sys.setrecursionlimit(50000)

"""
main.py - Entry point Aplikasi Asisten Virtual Pengolahan Jadwal + Alarm
Oleh: Jhesen Marlino Ibrahim - 2155201108
Universitas Muhammadiyah Bengkulu
"""
# Setup Windows environment
if sys.platform == 'win32':
    os.environ['GST_PLUGIN_SYSTEM_PATH_1_0'] = ''
    os.environ['GST_PLUGIN_PATH_1_0']        = ''
    os.environ['GST_PLUGIN_SYSTEM_PATH']     = ''
    os.environ['GST_PLUGIN_PATH']            = ''

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from utils.theme import p
from utils.audio import ALARM_ENGINE
from screens.splash import SplashScreen
from screens.beranda import BerandaScreen
from screens.jadwal import JadwalScreen
from screens.kalender import KalenderScreen
from screens.alarm import AlarmScreen


class AsistenJadwalApp(App):
    title = 'Asisten Jadwal + Alarm'

    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.12))
        sm.add_widget(SplashScreen())
        sm.add_widget(BerandaScreen())
        sm.add_widget(JadwalScreen())
        sm.add_widget(KalenderScreen())
        sm.add_widget(AlarmScreen())
        return sm

    def on_start(self):
        from kivy.core.window import Window
        try:
            Window.clearcolor = p('bg')
        except Exception:
            pass

    def on_stop(self):
        ALARM_ENGINE.stop()


if __name__ == '__main__':
    AsistenJadwalApp().run()