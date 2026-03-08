"""screens/base.py - BaseScreen dengan content area + nav bar placeholder."""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from utils.theme import p
from widgets.bottom_nav import BottomNav

class BaseScreen(Screen):
    _NAV_KEY = 'beranda'
    def __init__(self, **kw):
        super().__init__(**kw)
        self._wrap=BoxLayout(orientation='vertical')
        with self._wrap.canvas.before:
            Color(*p('bg')); self._bgr=Rectangle(pos=self._wrap.pos,size=self._wrap.size)
        self._wrap.bind(pos=lambda *a:setattr(self._bgr,'pos',self._wrap.pos),
                        size=lambda *a:setattr(self._bgr,'size',self._wrap.size))
        self._content_area=BoxLayout(orientation='vertical',size_hint_y=1)
        self._wrap.add_widget(self._content_area)
        self._nav_placeholder=BoxLayout(size_hint_y=None,height=dp(64))
        self._wrap.add_widget(self._nav_placeholder)
        self._nav=None; self.add_widget(self._wrap)

    def _set_content(self, widget):
        self._content_area.add_widget(widget)

    def on_enter(self):
        if self._nav is None:
            self._nav=BottomNav(self.manager,current=self._NAV_KEY)
            self._nav_placeholder.add_widget(self._nav)
        else:
            self._nav.set_active(self._NAV_KEY)
