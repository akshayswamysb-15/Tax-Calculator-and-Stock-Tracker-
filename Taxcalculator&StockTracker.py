import wx
import wx.lib.scrolledpanel as scrolled
import csv
import os
import datetime
import traceback
from io import StringIO
import matplotlib
matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import random
try:
    import yfinance as yf
except Exception:
    yf = None
try:
    import requests
except Exception:
    requests = None
DATA_DIR = os.path.abspath('.')
USERS_CSV = os.path.join(DATA_DIR, 'users.csv')
DEDUCTIONS_CSV = os.path.join(DATA_DIR, 'deductions.csv')
TAX_HISTORY_CSV = os.path.join(DATA_DIR, 'tax_history.csv')
PORTFOLIO_CSV = os.path.join(DATA_DIR, 'portfolio.csv')
CONFIG_CSV = os.path.join(DATA_DIR, 'config.csv') 
def ensure_csv(path, header):
    if not os.path.exists(path):
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)

ensure_csv(USERS_CSV, ['username', 'password'])
ensure_csv(DEDUCTIONS_CSV, ['code', 'amount', 'description'])
ensure_csv(TAX_HISTORY_CSV, ['username','date','gross_income','total_deductions','taxable_income','tax','total_tax'])
ensure_csv(PORTFOLIO_CSV, ['username','ticker','query_date','info_note'])
ensure_csv(CONFIG_CSV, ['key','value'])
def load_users():
    creds = {}
    with open(USERS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get('username'):
                creds[r['username']] = r['password']
    return creds

def save_user(username, password):
    with open(USERS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([username, password])

def load_deductions():
    d = {}
    with open(DEDUCTIONS_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            code = r.get('code')
            try:
                amt = float(r.get('amount') or 0)
            except:
                amt = 0.0
            desc = r.get('description') or ''
            if code:
                d[code] = {'amount': amt, 'description': desc}
    if not d:
        d = {
            'HRA': {'amount':150000.0, 'description':'House Rent Allowance cap example'},
            'L80C': {'amount':150000.0, 'description':'Section 80C investments cap example'},
            'MED': {'amount':25000.0, 'description':'Medical expense cap example'}
        }
        save_deductions(d)
    return d

def save_deductions(ded_dict):
    with open(DEDUCTIONS_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['code','amount','description'])
        for code, info in ded_dict.items():
            writer.writerow([code, info.get('amount', 0), info.get('description','')])

def append_tax_history(row):
    with open(TAX_HISTORY_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)

def append_portfolio_row(row):
    with open(PORTFOLIO_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)

def load_config():
    cfg = {}
    with open(CONFIG_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get('key'):
                cfg[r['key']] = r['value']
    return cfg
def compute_indian_style_tax(gross_income):
    slabs = [
        (250000, 0.0),
        (500000, 0.05),
        (1000000, 0.20),
        (float('inf'), 0.30)
    ]
    remaining = gross_income
    prev_limit = 0.0
    total_tax = 0.0
    breakdown = []
    for limit, rate in slabs:
        taxable_here = max(0.0, min(remaining, limit - prev_limit))
        tax_here = taxable_here * rate
        breakdown.append((f"{int(prev_limit)+1}-{('inf' if limit==float('inf') else int(limit))}", taxable_here, rate, tax_here))
        total_tax += tax_here
        prev_limit = limit
        remaining = gross_income - prev_limit
        if remaining <= 0:
            break
    return round(total_tax,2), breakdown
def fetch_stock_history_yfinance(ticker, period='1mo', interval='1d'):
    if not yf:
        raise RuntimeError('yfinance not available')
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period=period, interval=interval)
        dates = [d.to_pydatetime() for d in hist.index]
        closes = list(hist['Close'].astype(float))
        return dates, closes
    except Exception as e:
        raise

def fetch_stock_history_alpha_vantage(ticker, apikey, points=30):
    if not requests:
        raise RuntimeError('requests not available')
    url = 'https://www.alphavantage.co/query'
    params = {'function':'TIME_SERIES_DAILY_ADJUSTED','symbol':ticker,'outputsize':'compact','apikey':apikey}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if 'Time Series (Daily)' not in data:
        raise RuntimeError('Alpha Vantage returned unexpected data or limit reached')
    ts = data['Time Series (Daily)']
    sorted_dates = sorted(ts.keys())[-points:]
    dates = []
    closes = []
    for dt in sorted_dates:
        dates.append(datetime.datetime.strptime(dt, '%Y-%m-%d'))
        closes.append(float(ts[dt]['5. adjusted close']))
    return dates, closes

def generate_simulated_stock(ticker, points=30):
    base = random.uniform(50,500)
    dates = [datetime.datetime.now() - datetime.timedelta(days=(points-i)) for i in range(points)]
    prices = []
    p = base
    for i in range(points):
        p = max(1, p * (1 + random.uniform(-0.03,0.03)))
        prices.append(round(p, 2))
    return dates, prices

LIGHT_BG = "#FFF6EB"
CARD_BG = "#FFF1DB"
ACCENT = "#E66A4E"
TEXT_COLOR = "#2B2B2B"
INPUT_BG = "#FFFFFF"

class LoginPanel(wx.Panel):
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        s = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, label="Welcome — Login or Sign up")
        title_font = title.GetFont()
        title_font.PointSize += 6
        title_font = title_font.Bold()
        title.SetFont(title_font)
        title.SetForegroundColour(TEXT_COLOR)
        s.Add(title, 0, wx.ALL, 10)
        grid = wx.GridBagSizer(6,6)
        lbl_user = wx.StaticText(self, label="Username:")
        self.txt_user = wx.TextCtrl(self)
        lbl_pw = wx.StaticText(self, label="Password:")
        self.txt_pw = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        btn_login = wx.Button(self, label="Login")
        btn_signup = wx.Button(self, label="Sign up")
        self.info = wx.StaticText(self, label="")
        grid.Add(lbl_user, pos=(0,0), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
        grid.Add(self.txt_user, pos=(0,1), span=(1,3), flag=wx.EXPAND)
        grid.Add(lbl_pw, pos=(1,0), flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=4)
        grid.Add(self.txt_pw, pos=(1,1), span=(1,3), flag=wx.EXPAND)
        grid.Add(btn_login, pos=(2,1))
        grid.Add(btn_signup, pos=(2,2))
        grid.Add(self.info, pos=(3,0), span=(1,4), flag=wx.TOP | wx.LEFT, border=6)
        grid.AddGrowableCol(1)
        s.Add(grid, 0, wx.ALL|wx.EXPAND, 8)
        self.SetSizer(s)
        btn_login.Bind(wx.EVT_BUTTON, self.on_login)
        btn_signup.Bind(wx.EVT_BUTTON, self.on_signup)

    def on_login(self, event):
        u = self.txt_user.GetValue().strip()
        p = self.txt_pw.GetValue()
        if not u or not p:
            self.info.SetLabel("Enter username and password.")
            return
        creds = self.app_state['creds']
        if u in creds and creds[u] == p:
            self.info.SetLabel("Login successful.")
            self.app_state['current_user'] = u
            self.app_state['frame'].update_status(f"Logged in as {u}")
        else:
            self.info.SetLabel("Invalid credentials.")

    def on_signup(self, event):
        u = self.txt_user.GetValue().strip()
        p = self.txt_pw.GetValue()
        if not u or not p:
            self.info.SetLabel("Enter username and password to sign up.")
            return
        creds = self.app_state['creds']
        if u in creds:
            self.info.SetLabel("User already exists. Choose different username.")
            return
        save_user(u,p)
        creds[u] = p
        self.info.SetLabel("Signup successful. You may now login.")
        self.txt_pw.SetValue("")

class TaxPanel(wx.Panel):
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        s = wx.BoxSizer(wx.VERTICAL)
        header = wx.StaticText(self, label="Tax Calculator")
        hf = header.GetFont()
        hf.PointSize += 4
        header.SetFont(hf)
        header.SetForegroundColour(TEXT_COLOR)
        s.Add(header, 0, wx.ALL, 8)
        grid = wx.FlexGridSizer(5,2,8,8)
        grid.AddGrowableCol(1,1)
        grid.Add(wx.StaticText(self, label="Gross Annual Income:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.income = wx.TextCtrl(self)
        grid.Add(self.income, 1, wx.EXPAND)
        grid.Add(wx.StaticText(self, label="Enter Deduction Codes (comma separated):"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.ded_codes = wx.TextCtrl(self)
        grid.Add(self.ded_codes, 1, wx.EXPAND)
        grid.Add(wx.StaticText(self, label="(Optional) Add Other Deductions amount:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.other_ded = wx.TextCtrl(self)
        grid.Add(self.other_ded, 1, wx.EXPAND)
        btn_calc = wx.Button(self, label="Compute Tax")
        self.result = wx.StaticText(self, label="")
        grid.Add(btn_calc)
        grid.Add(self.result)
        s.Add(grid, 0, wx.ALL|wx.EXPAND, 8)
        self.breakdown_box = scrolled.ScrolledPanel(self, size=(-1,150))
        self.breakdown_box.SetBackgroundColour(CARD_BG)
        self.breakdown_box.SetupScrolling()
        s.Add(self.breakdown_box, 1, wx.ALL|wx.EXPAND, 8)
        btn_calc.Bind(wx.EVT_BUTTON, self.on_compute)
        self.SetSizer(s)

    def on_compute(self, event):
        user = self.app_state.get('current_user')
        if not user:
            wx.MessageBox("Please login first.", "Authentication required", wx.ICON_WARNING)
            return
        try:
            gi = float(self.income.GetValue() or 0)
        except:
            wx.MessageBox("Enter a valid number for income.", "Input error", wx.ICON_ERROR)
            return
        codes = [c.strip().upper() for c in (self.ded_codes.GetValue() or "").split(',') if c.strip()]
        ded_dict = self.app_state['deductions']
        total_deductions = 0.0
        used = []
        for c in codes:
            if c in ded_dict:
                total_deductions += ded_dict[c]['amount']
                used.append((c, ded_dict[c]['amount']))
        try:
            other = float(self.other_ded.GetValue() or 0)
        except:
            other = 0.0
        total_deductions += other
        taxable = max(0.0, gi - total_deductions)
        tax, breakdown = compute_indian_style_tax(taxable)
        self.result.SetLabel(f"Total deductions: {total_deductions:.2f} | Taxable income: {taxable:.2f} | Total tax: {tax:.2f}")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self.breakdown_box, label=f"Used deduction codes: {', '.join([c for c,_ in used]) or 'None'}"))
        for rng, amt, rate, tx in breakdown:
            sizer.Add(wx.StaticText(self.breakdown_box, label=f"Slab {rng} — taxable: {amt:.2f}, rate: {int(rate*100)}% => tax {tx:.2f}"))
        sizer.Add(wx.StaticText(self.breakdown_box, label=f"Other deductions: {other:.2f}"))
        for child in self.breakdown_box.GetChildren():
            child.Destroy()
        self.breakdown_box.SetSizer(sizer)
        self.breakdown_box.Layout()
        self.breakdown_box.SetupScrolling()
        row = [user, datetime.datetime.now().isoformat(), f"{gi:.2f}", f"{total_deductions:.2f}", f"{taxable:.2f}", f"{tax:.2f}", f"{tax:.2f}"]
        try:
            append_tax_history(row)
        except Exception as e:
            print("Failed to append tax history:", e)

class StockPanel(wx.Panel):
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        main = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self, label="Stock Tracker")
        tf = title.GetFont()
        tf.PointSize += 4
        title.SetFont(tf)
        title.SetForegroundColour(TEXT_COLOR)
        main.Add(title, 0, wx.ALL, 6)
        h = wx.BoxSizer(wx.HORIZONTAL)
        self.ticker = wx.TextCtrl(self)
        self.ticker.SetHint("E.g. AAPL or TCS.NS")
        btn_fetch = wx.Button(self, label="Fetch & Plot")
        h.Add(wx.StaticText(self, label="Ticker:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 6)
        h.Add(self.ticker, 1, wx.EXPAND|wx.RIGHT, 8)
        h.Add(btn_fetch, 0)
        main.Add(h, 0, wx.ALL|wx.EXPAND, 8)
        self.figure = Figure(figsize=(6,3))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        main.Add(self.canvas, 1, wx.ALL|wx.EXPAND, 8)
        btn_fetch.Bind(wx.EVT_BUTTON, self.on_fetch)
        self.SetSizer(main)

    def on_fetch(self, event):
        user = self.app_state.get('current_user')
        if not user:
            wx.MessageBox("Please login first.", "Authentication required", wx.ICON_WARNING)
            return
        t = (self.ticker.GetValue() or "").strip().upper()
        if not t:
            wx.MessageBox("Enter a ticker symbol.", "Input error", wx.ICON_ERROR)
            return
        dates = []
        prices = []
        tried = []
        try:
            if yf:
                dates, prices = fetch_stock_history_yfinance(t, period='1mo', interval='1d')
                tried.append('yfinance')
        except Exception as e:
            tried.append(f'yfinance-failed:{e}')
        if not dates:
            cfg = self.app_state.get('config', {})
            apikey = cfg.get('ALPHA_VANTAGE_KEY') or cfg.get('alphavantage') or cfg.get('alpha_vantage')
            if apikey and requests:
                try:
                    dates, prices = fetch_stock_history_alpha_vantage(t, apikey)
                    tried.append('alpha_vantage')
                except Exception as e:
                    tried.append(f'alpha_vantage-failed:{e}')
        if not dates:
            dates, prices = generate_simulated_stock(t, points=30)
            tried.append('simulated')
        try:
            self.ax.clear()
            self.ax.plot(dates, prices)
            self.ax.set_title(f"{t} — recent prices ({tried[-1]})")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price")
            self.figure.autofmt_xdate()
            self.canvas.draw()
        except Exception as e:
            traceback.print_exc()
            wx.MessageBox(f"Plot failed: {e}", "Plot error", wx.ICON_ERROR)
        try:
            append_portfolio_row([user, t, datetime.datetime.now().isoformat(), tried[-1]])
        except Exception as e:
            print("Failed to save portfolio row:", e)

class DeductionsPanel(wx.Panel):
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        s = wx.BoxSizer(wx.VERTICAL)
        header = wx.StaticText(self, label="Deductions Manager")
        hf = header.GetFont()
        hf.PointSize += 3
        header.SetFont(hf)
        header.SetForegroundColour(TEXT_COLOR)
        s.Add(header, 0, wx.ALL, 8)
        grid = wx.FlexGridSizer(3,4,8,8)
        grid.AddGrowableCol(1)
        grid.Add(wx.StaticText(self, label="Code:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.code = wx.TextCtrl(self)
        grid.Add(self.code, 0, wx.EXPAND)
        grid.Add(wx.StaticText(self, label="Amount:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.amount = wx.TextCtrl(self)
        grid.Add(self.amount, 0, wx.EXPAND)
        grid.Add(wx.StaticText(self, label="Description:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.desc = wx.TextCtrl(self)
        grid.Add(self.desc, 0, wx.EXPAND)
        btn_add = wx.Button(self, label="Add/Update")
        grid.Add(btn_add)
        s.Add(grid, 0, wx.ALL|wx.EXPAND, 8)
        btn_add.Bind(wx.EVT_BUTTON, self.on_add)
        self.d_list = wx.ListCtrl(self, style=wx.LC_REPORT)
        self.d_list.InsertColumn(0, "Code", width=100)
        self.d_list.InsertColumn(1, "Amount", width=100)
        self.d_list.InsertColumn(2, "Description", width=300)
        s.Add(self.d_list, 1, wx.ALL|wx.EXPAND, 8)
        self.SetSizer(s)
        self.refresh_list()

    def refresh_list(self):
        self.d_list.DeleteAllItems()
        for code, info in self.app_state['deductions'].items():
            idx = self.d_list.InsertItem(self.d_list.GetItemCount(), code)
            self.d_list.SetItem(idx,1,str(info.get('amount',0)))
            self.d_list.SetItem(idx,2,str(info.get('description','')))

    def on_add(self,event):
        c = self.code.GetValue().strip().upper()
        try:
            amt = float(self.amount.GetValue() or 0)
        except:
            wx.MessageBox("Enter valid numeric amount","Input error", wx.ICON_ERROR)
            return
        desc = self.desc.GetValue()
        if not c:
            wx.MessageBox("Enter code","Input error", wx.ICON_ERROR)
            return
        self.app_state['deductions'][c] = {'amount':amt,'description':desc}
        save_deductions(self.app_state['deductions'])
        self.refresh_list()

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Tax + Stock App", size=(800,600))
        self.app_state = {
            'creds': load_users(),
            'deductions': load_deductions(),
            'config': load_config(),
            'current_user': None,
            'frame': self
        }
        panel = wx.Panel(self)
        s = wx.BoxSizer(wx.VERTICAL)
        self.status = wx.StaticText(panel, label="Not logged in")
        s.Add(self.status, 0, wx.ALL, 4)
        self.notebook = wx.Notebook(panel)
        self.login_panel = LoginPanel(self.notebook, self.app_state)
        self.tax_panel = TaxPanel(self.notebook, self.app_state)
        self.stock_panel = StockPanel(self.notebook, self.app_state)
        self.ded_panel = DeductionsPanel(self.notebook, self.app_state)
        self.notebook.AddPage(self.login_panel, "Login")
        self.notebook.AddPage(self.tax_panel, "Tax Calculator")
        self.notebook.AddPage(self.stock_panel, "Stock Tracker")
        self.notebook.AddPage(self.ded_panel, "Deductions Manager")
        s.Add(self.notebook,1,wx.EXPAND)
        panel.SetSizer(s)
        self.Centre()
        self.Show()

    def update_status(self, msg):
        self.status.SetLabel(msg)

if __name__=="__main__":
    app = wx.App()
    frame = MainFrame()
    app.MainLoop()
