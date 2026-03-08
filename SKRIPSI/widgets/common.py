"""widgets/common.py - Helper widget: draw_bg, mk_lbl, mk_input, MBtn."""
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, RoundedRectangle
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from utils.theme import p, PAL

def draw_bg(w, clr_key='card', r=12):
    def _d(*a):
        w.canvas.before.clear()
        with w.canvas.before:
            Color(*p(clr_key)); RoundedRectangle(pos=w.pos,size=w.size,radius=[dp(r)])
    w.bind(pos=_d,size=_d); _d()

def mk_lbl(text, sz=13, clr='txt', bold=False, align='left', **kw):
    lb=Label(text=text,font_size=dp(sz),color=p(clr),bold=bold,halign=align,valign='middle',**kw)
    lb.bind(size=lb.setter('text_size')); return lb

def mk_input(**kw):
    d=dict(font_size=dp(13),background_normal='',background_color=p('card2'),
           foreground_color=p('txt'),cursor_color=p('blue'),hint_text_color=p('txt2'),
           size_hint_y=None,height=dp(44),padding=[dp(12),dp(12)],multiline=False)
    d.update(kw); return TextInput(**d)

def _style_colors(style):
    base={'primary':PAL.get('blue','#1F6FEB'),'success':PAL.get('green','#2EA043'),
          'danger':'#B91C1C','neutral':PAL.get('card','#21262D'),
          'orange':PAL.get('orange','#9A3412')}.get(style,PAL.get('blue','#1F6FEB'))
    n=get_color_from_hex(base); h=[max(0,c*.9) for c in n]; return n,h

class MBtn(Button):
    def __init__(self, style='primary', **kw):
        super().__init__(**kw)
        self.background_normal=''; self.background_down=''
        self.bold=True; self.color=p('txt')
        self._n,self._h=_style_colors(style); self.background_color=self._n
        self.bind(
            on_press=lambda *a: Animation(background_color=self._h,duration=0.1).start(self),
            on_release=lambda *a: Animation(background_color=self._n,duration=0.2).start(self))
