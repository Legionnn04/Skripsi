"""utils/theme.py - Tema warna & pergantian tema otomatis."""
from datetime import datetime
from kivy.utils import get_color_from_hex
from kivy.core.window import Window

PAL = {
    'bg':'#0D1117','card':'#161B22','card2':'#21262D',
    'blue':'#58A6FF','blue2':'#1F6FEB','green':'#3FB950',
    'yellow':'#D29922','red':'#F85149','purple':'#BC8CFF',
    'orange':'#F0883E','orange2':'#9A3412','txt':'#E6EDF3',
    'txt2':'#8B949E','border':'#30363D','nav':'#0D1117',
}

THEME_PALETTES = {
    'morning':{'bg':'#FFF8E1','card':'#FFFDE7','card2':'#FFF3E0',
               'blue':'#90A4AE','orange':'#FFB74D','purple':'#CE93D8','txt':'#212121','txt2':'#455A64'},
    'day':{'bg':'#E3F2FD','card':'#FFFFFF','card2':'#E1F5FE',
            'blue':'#64B5F6','orange':'#FFCC80','purple':'#B39DDB','txt':'#212121','txt2':'#546E7A'},
    'evening':{'bg':'#F6E5CA','card':'#FFE0B2','card2':'#FFECB3',
                'blue':'#78909C','orange':'#FFAB91','purple':'#B39DDB','txt':'#212121','txt2':'#546E7A'},
    'night':{'bg':'#263238','card':'#37474F','card2':'#455A64',
              'blue':'#90A4AE','orange':'#FFCCBC','purple':'#B39DDB','txt':'#ECEFF1','txt2':'#B0BEC5'},
}

CURRENT_THEME = None

def p(k): return get_color_from_hex(PAL[k])

def get_time_of_day():
    h = datetime.now().hour
    if 5<=h<11: return 'morning'
    if 11<=h<17: return 'day'
    if 17<=h<19: return 'evening'
    return 'night'

def apply_theme(name):
    global CURRENT_THEME
    if name == CURRENT_THEME: return
    CURRENT_THEME = name
    PAL.update(THEME_PALETTES.get(name, {}))
    Window.clearcolor = p('bg')
    from kivy.app import App
    app = App.get_running_app()
    if not app or not getattr(app,'root',None): return
    sm = app.root; cur = sm.current
    sm.clear_widgets()
    from screens.splash   import SplashScreen
    from screens.beranda  import BerandaScreen
    from screens.jadwal   import JadwalScreen
    from screens.kalender import KalenderScreen
    from screens.alarm    import AlarmScreen
    for S in [SplashScreen,BerandaScreen,JadwalScreen,KalenderScreen,AlarmScreen]:
        sm.add_widget(S())
    sm.current = cur
