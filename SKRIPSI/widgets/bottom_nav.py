"""widgets/bottom_nav.py - Bottom navigation bar."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.screenmanager import FadeTransition
from utils.theme import p

NAV_ITEMS=[('beranda','Beranda'),('jadwal','Jadwal'),('kalender','Kalender'),('alarm','Alarm')]

class BottomNav(BoxLayout):
    def __init__(self, sm, current='beranda', **kw):
        super().__init__(size_hint_y=None,height=dp(56),orientation='horizontal',
                         spacing=dp(2),padding=[dp(4),dp(4)],**kw)
        self.sm=sm; self._btns={}
        with self.canvas.before:
            Color(*p('nav')); self._bgr=Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=lambda *a:setattr(self._bgr,'pos',self.pos),
                  size=lambda *a:setattr(self._bgr,'size',self.size))
        for name,label in NAV_ITEMS:
            btn=self._mk(name,label,active=(name==current))
            self._btns[name]=btn; self.add_widget(btn)

    def _mk(self,name,label,active):
        btn=Button(text=label,font_size=dp(13),bold=active,background_normal='',
                   background_color=p('blue2') if active else p('card2'),
                   background_down='',color=p('txt') if active else p('txt2'),size_hint_x=1)
        btn.bind(on_press=lambda *a,n=name: self._go(n)); return btn

    def _go(self,name):
        if name not in self.sm.screen_names: return
        self.sm.transition=FadeTransition(duration=0.12)
        self.sm.current=name; self.set_active(name)

    def set_active(self,name):
        for n,btn in self._btns.items():
            active=(n==name)
            btn.background_color=p('blue2') if active else p('card2')
            btn.color=p('txt') if active else p('txt2'); btn.bold=active
