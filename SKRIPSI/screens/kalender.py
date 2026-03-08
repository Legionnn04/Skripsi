"""screens/kalender.py - Layar kalender bulanan."""
import calendar as _calendar
from datetime import datetime
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.metrics import dp
from screens.base import BaseScreen
from widgets.common import mk_lbl, MBtn
from widgets.jadwal_card import JadwalCard
from widgets.popups import TambahJadwalPopup
from utils.storage import load_jadwal, save_jadwal, load_alarm, save_alarm
from utils.theme import p

class KalenderScreen(BaseScreen):
    _NAV_KEY='kalender'
    def __init__(self,**kw): super().__init__(name='kalender',**kw); self._build_content()

    def _build_content(self):
        main=BoxLayout(orientation='vertical',padding=[dp(14),dp(14),dp(14),dp(8)],spacing=dp(10))
        hdr=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(8))
        back=MBtn(text='Kembali',style='neutral',size_hint_x=None,width=dp(90),font_size=dp(12))
        back.bind(on_press=lambda *a: setattr(self.manager,'current','beranda')); hdr.add_widget(back)
        hdr.add_widget(mk_lbl('Kalender',19,bold=True,size_hint_y=None,height=dp(34))); main.add_widget(hdr)
        # kalender grid di dalam ScrollView agar aman di layar kecil
        cal_sc=ScrollView(size_hint_y=None,height=dp(210),do_scroll_x=False)
        self.cal_grid=BoxLayout(orientation='vertical',spacing=dp(2),size_hint_y=None)
        self.cal_grid.bind(minimum_height=self.cal_grid.setter('height'))
        cal_sc.add_widget(self.cal_grid); main.add_widget(cal_sc)
        self._show_month(datetime.now().year,datetime.now().month)
        self.detail_box=BoxLayout(orientation='vertical',size_hint_y=None)
        self.detail_box.bind(minimum_height=self.detail_box.setter('height'))
        sc=ScrollView(); sc.add_widget(self.detail_box); main.add_widget(sc)
        self._set_content(main)

    def _show_month(self,year,month):
        self.cal_grid.clear_widgets()
        names=['Min','Sen','Sel','Rab','Kam','Jum','Sab']
        row=BoxLayout(size_hint_y=None,height=dp(22))
        for n in names: row.add_widget(mk_lbl(n,10,'txt2',size_hint_x=1,align='center'))
        self.cal_grid.add_widget(row)
        for week in _calendar.Calendar().monthdayscalendar(year,month):
            row=BoxLayout(size_hint_y=None,height=dp(28))
            for d in week:
                if d==0: row.add_widget(Widget())
                else:
                    btn=Button(text=str(d),font_size=dp(11),background_normal='',
                               background_color=p('card2'),color=p('txt'),size_hint_x=1)
                    ds=f"{year}-{month:02d}-{d:02d}"; btn.bind(on_press=lambda x,s=ds: self._show_day(s))
                    row.add_widget(btn)
            self.cal_grid.add_widget(row)

    def _show_day(self,date_str):
        self.detail_box.clear_widgets()
        f=[j for j in load_jadwal() if j.get('tanggal')==date_str]
        if not f:
            self.detail_box.add_widget(Label(text='Tidak ada jadwal untuk '+date_str,font_size=dp(13),color=p('txt2'),size_hint_y=None,height=dp(70)))
        else:
            for j in f: self.detail_box.add_widget(JadwalCard(j,on_delete=self._del,on_edit=self._edit,on_public=self._pub))

    def _del(self,j):
        aid=j.get('alarm_id')
        if aid:
            al=load_alarm(); al=[a for a in al if a.get('id')!=aid]; save_alarm(al)
        save_jadwal([x for x in load_jadwal() if x.get('id')!=j.get('id')]); self._show_day(j.get('tanggal',''))

    def _edit(self,j):
        def _save_cb(info):
            info['id']=j.get('id'); info['dibuat']=j.get('dibuat')
            lst=load_jadwal()
            for idx,x in enumerate(lst):
                if x.get('id')==j.get('id'): lst[idx]=info; break
            save_jadwal(lst); self._show_day(info.get('tanggal',''))
        p2=TambahJadwalPopup(on_save=_save_cb,jadwal=j); p2.title='Ubah Jadwal'; p2.open()

    def _pub(self,j):
        lst=load_jadwal()
        for x in lst:
            if x.get('id')==j.get('id'): x['public']=not x.get('public',False)
        save_jadwal(lst); self._show_day(j.get('tanggal',''))