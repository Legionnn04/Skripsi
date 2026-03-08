"""utils/pet.py - Virtual pet helper."""
import os, sys, random
from kivy.clock import Clock
from datetime import datetime

PET_MESSAGES = ['Halo! Senang bertemu denganmu.','Aku akan mengingatkanmu nanti.',
                'Jangan lupa istirahat ya!','Ayo semangat jalani hari!']

PET_STICKERS = [
    {'file':'mengantuk.gif','msg':'Saya ngantuk...','start':22,'end':6,'dur':4},
    {'file':'berpikir.gif','msg':'Sedang berpikir...','dur':3},
    {'file':'kagum.gif','msg':'Wah, keren!','dur':2},
    {'file':'marah.gif','msg':'Aduh, marah nih!','dur':2},
    {'file':'menyapa.gif','msg':'Hai teman!','dur':4},
    {'file':'normal.png','msg':''},
    {'file':'mengingatkan.gif','msg':'Sudah kuingatkan, ya!','dur':3},
]

def _resolve_path(filename):
    """Resolve path file agar bisa ditemukan baik saat dev maupun di-bundle PyInstaller."""
    base = getattr(sys, '_MEIPASS', os.path.abspath('.'))
    full_path = os.path.join(base, filename)
    if os.path.exists(full_path):
        return full_path
    # fallback ke working directory
    fallback = os.path.join(os.path.abspath('.'), filename)
    if os.path.exists(fallback):
        return fallback
    return filename

def pet_say(msg=None, dur=3, sticker_override=None):
    from kivy.app import App
    app = App.get_running_app()
    if not app or not getattr(app,'root',None): return
    try:
        screen = app.root.get_screen('beranda')
        choice = None
        if sticker_override:
            choice = {'file':sticker_override}
        else:
            nowh = datetime.now().hour; candidates = []
            for stk in PET_STICKERS:
                s=stk.get('start'); e=stk.get('end')
                if s is not None and e is not None:
                    if s<=e:
                        if s<=nowh<e: candidates.append(stk)
                    else:
                        if nowh>=s or nowh<e: candidates.append(stk)
                else:
                    candidates.append(stk)
            choice = random.choice(candidates) if candidates else random.choice(PET_STICKERS)
        if hasattr(screen,'pet_img') and choice:
            path = choice.get('file')
            if path:
                full_path = _resolve_path(path)
                if os.path.exists(full_path):
                    screen.pet_img.source = full_path
        if msg is None and choice: msg=choice.get('msg','')
        if hasattr(screen,'pet_bubble'):
            screen.pet_bubble.text=msg or ''
            bubble_dur=choice.get('dur',dur) if choice else dur
            Clock.schedule_once(lambda dt: setattr(screen.pet_bubble,'text',''),bubble_dur)
        else:
            pet_lbl=screen.pet_msg; pet_lbl.text=msg or ''
            Clock.schedule_once(lambda dt: setattr(pet_lbl,'text',''),dur)
    except Exception: pass