import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime

CONFIG_PATH = 'location_config.json'


def _load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_config(cfg):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(cfg, f, indent=4)


class PeriodTimingsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Edit Period Timings')
        self.root.geometry('520x380')
        self._build()
        self._load()

    def _build(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(frame, text='Edit per-period start/end & grace minutes', font=('Arial', 11, 'bold'))
        header.grid(row=0, column=0, columnspan=4, pady=(0, 10))

        ttk.Label(frame, text='Period').grid(row=1, column=0, sticky='w')
        ttk.Label(frame, text='Start (HH:MM)').grid(row=1, column=1, sticky='w')
        ttk.Label(frame, text='End (HH:MM)').grid(row=1, column=2, sticky='w')
        ttk.Label(frame, text='Grace (min)').grid(row=1, column=3, sticky='w')

        self.entries = {}
        for i in range(1, 7):
            r = i + 1
            ttk.Label(frame, text=f'Period {i}').grid(row=r, column=0, sticky='w', pady=6)
            sv_start = tk.StringVar()
            sv_end = tk.StringVar()
            sv_grace = tk.StringVar()
            e_start = ttk.Entry(frame, textvariable=sv_start, width=12)
            e_end = ttk.Entry(frame, textvariable=sv_end, width=12)
            e_grace = ttk.Entry(frame, textvariable=sv_grace, width=6)
            e_start.grid(row=r, column=1, padx=6)
            e_end.grid(row=r, column=2, padx=6)
            e_grace.grid(row=r, column=3, padx=6)
            self.entries[str(i)] = (sv_start, sv_end, sv_grace)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=9, column=0, columnspan=4, pady=(18, 0))
        ttk.Button(btn_frame, text='Save', command=self.save).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text='Reset to Defaults', command=self.reset_defaults).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text='Close', command=self.root.destroy).pack(side=tk.LEFT, padx=8)

    def _load(self):
        cfg = _load_config()
        tr = cfg.get('attendance_time_restrictions', {})
        period_timings = tr.get('period_timings', {})

        # Populate entries (leave blank if missing)
        for p, (svs, sve, svg) in self.entries.items():
            info = period_timings.get(p, {})
            svs.set(info.get('start', ''))
            sve.set(info.get('end', ''))
            svg.set(str(info.get('grace_minutes', '')))

    def _validate_time(self, tstr):
        if not tstr:
            return False
        try:
            datetime.strptime(tstr, '%H:%M')
            return True
        except Exception:
            return False

    def save(self):
        # Validate and save to location_config.json
        new_periods = {}
        for p, (svs, sve, svg) in self.entries.items():
            s = svs.get().strip()
            e = sve.get().strip()
            g = svg.get().strip()
            if not s or not e:
                messagebox.showerror('Validation', f'Please supply start/end for Period {p}')
                return
            if not self._validate_time(s) or not self._validate_time(e):
                messagebox.showerror('Validation', f'Invalid time format for Period {p}. Use HH:MM')
                return
            try:
                gi = int(g) if g else 0
            except Exception:
                messagebox.showerror('Validation', f'Invalid grace minutes for Period {p}')
                return
            new_periods[p] = {'start': s, 'end': e, 'grace_minutes': gi}

        # Load config, update and save
        cfg = _load_config()
        if 'attendance_time_restrictions' not in cfg:
            cfg['attendance_time_restrictions'] = {}
        cfg['attendance_time_restrictions']['period_timings'] = new_periods
        _save_config(cfg)
        messagebox.showinfo('Saved', 'Period timings updated successfully')

    def reset_defaults(self):
        # Reset to the sample defaults used by the project
        defaults = {
            "1": {"start": "09:00", "end": "09:50", "grace_minutes": 5},
            "2": {"start": "10:00", "end": "10:50", "grace_minutes": 5},
            "3": {"start": "11:00", "end": "11:50", "grace_minutes": 5},
            "4": {"start": "12:00", "end": "12:50", "grace_minutes": 5},
            "5": {"start": "14:00", "end": "14:50", "grace_minutes": 5},
            "6": {"start": "15:00", "end": "15:50", "grace_minutes": 5}
        }
        for p, info in defaults.items():
            svs, sve, svg = self.entries[p]
            svs.set(info['start'])
            sve.set(info['end'])
            svg.set(str(info['grace_minutes']))


if __name__ == '__main__':
    root = tk.Tk()
    PeriodTimingsGUI(root)
    root.mainloop()
