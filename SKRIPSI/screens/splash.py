"""screens/splash.py - Layar splash dengan logo kampus."""
import sys, os
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from utils.theme import p

def _res(filename):
    base = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    return os.path.join(base, filename)

class SplashScreen(Screen):
    def __init__(self, **kw):
        super().__init__(name='splash', **kw)
        root = FloatLayout()
        with root.canvas.before:
            Color(*p('bg')); Rectangle(pos=root.pos, size=Window.size)
        img = Image(source=_res('logokampus.png'), allow_stretch=True, keep_ratio=True,
                    size_hint=(0.6, 0.6), pos_hint={'center_x': .5, 'center_y': .5})
        root.add_widget(img)
        self.add_widget(root)

    def on_enter(self):
        def goto(dt):
            if self.manager: self.manager.current = 'beranda'
            else: Clock.schedule_once(goto, 0.5)
        Clock.schedule_once(goto, 2.2)