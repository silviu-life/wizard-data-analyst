#!/usr/bin/env python3
"""Raw data dump of a fictional global B2B SaaS company (Lumora Software), written to ../date/.

One simulation (seed 42) feeds every file, so sources reconcile: Stripe charges match CRM customers,
ad clicks match GA4 sessions, enterprise invoices (PDF only) match HubSpot deals, the GL matches all of it.
The planted stories are in ce_e_ascuns_in_date.md next to this script; nothing inside date/ points to them.

  pip install numpy openpyxl reportlab python-docx
  python3 genereaza_date_demo.py        # writes ./date/ (~1,800 files, ~70 MB, ~30 s)
"""
import calendar, csv, json, math, os, random, re, string, unicodedata
from collections import defaultdict
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from email.utils import make_msgid

import numpy as np
from docx import Document
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = os.path.join(os.getcwd(), 'date')  # writes ./date/ in the folder you run it from
random.seed(42)
rng = np.random.default_rng(42)

START, END, EXPORTED = date(2024, 1, 1), date(2026, 9, 30), date(2026, 10, 1)
DAYS = [START + timedelta(i) for i in range((END - START).days + 1)]
MONTHS = sorted({(d.year, d.month) for d in DAYS})
QUARTERS = sorted({(y, (m - 1) // 3 + 1) for y, m in MONTHS})
MNAME = calendar.month_name


def out(*parts):
    p = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def midx(d): return (d.year - START.year) * 12 + d.month - 1
def month_end(y, m): return date(y, m, calendar.monthrange(y, m)[1])
def pois(lam): return int(rng.poisson(max(lam, 0)))
def rid(prefix, n): return prefix + ''.join(random.choices(string.ascii_letters + string.digits, k=n))
def ascii_(s): return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
def clamp(v, a, b): return max(a, min(b, v))


def add_months(d, n):
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


# ───────────────────────── world ─────────────────────────
# name, iso2, region, weight inside region, sloppy variants seen in CRM / invoices
COUNTRIES = [
    ('United States', 'US', 'North America', 80, ['USA', 'US', 'United States of America', 'U.S.']),
    ('Canada', 'CA', 'North America', 11, ['CA']),
    ('United Kingdom', 'GB', 'EMEA', 18, ['UK', 'Great Britain', 'England']),
    ('Germany', 'DE', 'EMEA', 16, ['Deutschland', 'DE']),
    ('France', 'FR', 'EMEA', 10, ['FR']),
    ('Netherlands', 'NL', 'EMEA', 8, ['The Netherlands', 'Holland']),
    ('Spain', 'ES', 'EMEA', 6, ['España']),
    ('Italy', 'IT', 'EMEA', 5, ['Italia']),
    ('Sweden', 'SE', 'EMEA', 5, ['Sverige']),
    ('Switzerland', 'CH', 'EMEA', 4, ['Schweiz']),
    ('Poland', 'PL', 'EMEA', 4, ['Polska']),
    ('Romania', 'RO', 'EMEA', 4, ['România']),
    ('Ireland', 'IE', 'EMEA', 3, ['Eire']),
    ('Belgium', 'BE', 'EMEA', 3, ['Belgique']),
    ('Denmark', 'DK', 'EMEA', 3, ['Danmark']),
    ('Israel', 'IL', 'EMEA', 3, ['IL']),
    ('United Arab Emirates', 'AE', 'EMEA', 3, ['UAE']),
    ('South Africa', 'ZA', 'EMEA', 3, ['RSA']),
    ('Norway', 'NO', 'EMEA', 2, ['Norge']),
    ('Portugal', 'PT', 'EMEA', 2, ['PT']),
    ('Finland', 'FI', 'EMEA', 2, ['Suomi']),
    ('Austria', 'AT', 'EMEA', 2, ['Österreich']),
    ('Czechia', 'CZ', 'EMEA', 2, ['Czech Republic']),
    ('Turkey', 'TR', 'EMEA', 2, ['Türkiye']),
    ('Saudi Arabia', 'SA', 'EMEA', 1, ['KSA']),
    ('Nigeria', 'NG', 'EMEA', 1, ['NG']),
    ('Egypt', 'EG', 'EMEA', 1, ['EG']),
    ('Australia', 'AU', 'APAC', 20, ['AU']),
    ('India', 'IN', 'APAC', 18, ['IN']),
    ('Japan', 'JP', 'APAC', 14, ['日本']),
    ('Singapore', 'SG', 'APAC', 8, ['SG']),
    ('South Korea', 'KR', 'APAC', 6, ['Korea, Republic of', 'Korea']),
    ('New Zealand', 'NZ', 'APAC', 4, ['NZ']),
    ('Indonesia', 'ID', 'APAC', 4, ['ID']),
    ('Philippines', 'PH', 'APAC', 3, ['PH']),
    ('Vietnam', 'VN', 'APAC', 3, ['Viet Nam']),
    ('Malaysia', 'MY', 'APAC', 3, ['MY']),
    ('Taiwan', 'TW', 'APAC', 3, ['Taiwan, Province of China']),
    ('Thailand', 'TH', 'APAC', 2, ['TH']),
    ('Hong Kong', 'HK', 'APAC', 2, ['Hong Kong SAR']),
    ('Brazil', 'BR', 'LATAM', 30, ['Brasil']),
    ('Mexico', 'MX', 'LATAM', 25, ['México']),
    ('Argentina', 'AR', 'LATAM', 12, ['AR']),
    ('Colombia', 'CO', 'LATAM', 12, ['CO']),
    ('Chile', 'CL', 'LATAM', 10, ['CL']),
    ('Peru', 'PE', 'LATAM', 5, ['Perú']),
    ('Uruguay', 'UY', 'LATAM', 3, ['UY']),
    ('Costa Rica', 'CR', 'LATAM', 3, ['CR']),
]
NC = len(COUNTRIES)
REGIONS = ['North America', 'EMEA', 'APAC', 'LATAM']
REG_IDX = np.array([REGIONS.index(c[2]) for c in COUNTRIES])
WITHIN = np.array([c[3] / sum(x[3] for x in COUNTRIES if x[2] == c[2]) for c in COUNTRIES])
REGION_W0, REGION_W1 = np.array([.46, .34, .12, .08]), np.array([.34, .31, .25, .10])  # APAC doubles its share
UTC_OFF = {'North America': -6, 'EMEA': 1, 'APAC': 8, 'LATAM': -4}
REGION_CHURN = {'North America': 1.0, 'EMEA': .95, 'APAC': .85, 'LATAM': 1.3}
EU_VAT = {'DE', 'FR', 'NL', 'ES', 'IT', 'SE', 'PL', 'RO', 'IE', 'BE', 'DK', 'PT', 'FI', 'AT', 'CZ'}


def country_w(d, region=None):
    t = (d - START).days / (END - START).days
    rw = REGION_W0 + (REGION_W1 - REGION_W0) * t if region is None else np.array([r == region for r in REGIONS], float)
    w = rw[REG_IDX] * WITHIN
    return w / w.sum()


def currency(iso):
    if iso in {'DE', 'FR', 'NL', 'ES', 'IT', 'IE', 'BE', 'PT', 'FI', 'AT'}: return 'EUR'
    return {'GB': 'GBP', 'AU': 'AUD', 'CA': 'CAD', 'JP': 'JPY'}.get(iso, 'USD')


FX0 = {'USD': 1, 'EUR': 1.08, 'GBP': 1.27, 'AUD': .66, 'CAD': .74, 'JPY': .0068}
LOCAL = {'USD': 1, 'EUR': .92, 'GBP': .79, 'AUD': 1.5, 'CAD': 1.35, 'JPY': 150}


def fx(cur, d):  # USD per 1 unit of cur
    if cur == 'USD': return 1.0
    k, t = list(FX0).index(cur), (d - START).days
    return FX0[cur] * (1 + .035 * math.sin(t / 110 + k) + .01 * math.sin(t / 17 + 2 * k))


def local_price(usd, cur):
    v = usd * LOCAL[cur]
    return round(v, -1) if cur == 'JPY' else round(v)


def money(v, cur): return round(v) if cur == 'JPY' else round(v, 2)


SEASON = {1: 1.08, 2: 1.04, 3: 1.06, 4: 1.0, 5: 1.0, 6: .95, 7: .88, 8: .80, 9: 1.08, 10: 1.06, 11: 1.02, 12: .72}
DOW = [1.10, 1.15, 1.12, 1.05, .90, .45, .50]
BF = [(date(2024, 11, 25), date(2024, 12, 2)), (date(2025, 11, 24), date(2025, 12, 1))]
OUTAGE = date(2025, 6, 12)
INSIGHTS_LAUNCH = date(2025, 4, 1)
PRICE_UP = date(2026, 1, 1)


def in_bf(d): return any(a <= d <= b for a, b in BF)
def growth(d): return 1.028 ** midx(d)


# ───────────────────────── people & companies ─────────────────────────
FIRST = {
    'North America': ['James', 'Emily', 'Michael', 'Olivia', 'David', 'Ava', 'Daniel', 'Sarah', 'Ryan', 'Megan', 'Tyler', 'Jessica', 'Kevin', 'Ashley', 'Brandon', 'Lauren', 'Chris', 'Hannah', 'Jason', 'Rachel'],
    'EMEA': ['Lukas', 'Sophie', 'Thomas', 'Emma', 'Matteo', 'Chloé', 'Jan', 'Anna', 'Oliver', 'Lea', 'Andrei', 'Ioana', 'Pablo', 'Lucía', 'Erik', 'Maja', 'Noah', 'Amira', 'Pieter', 'Zeynep'],
    'APAC': ['Hiroshi', 'Yuki', 'Arjun', 'Priya', 'Wei', 'Mei', 'Jack', 'Charlotte', 'Min-jun', 'Ji-woo', 'Rahul', 'Ananya', 'Takeshi', 'Sakura', 'Liam', 'Grace', 'Budi', 'Siti', 'Minh', 'Linh'],
    'LATAM': ['Mateo', 'Valentina', 'Santiago', 'Camila', 'Lucas', 'Isabela', 'Diego', 'Mariana', 'Gabriel', 'Sofía', 'Joaquín', 'Martina', 'Felipe', 'Daniela', 'Rafael', 'Ana', 'Tomás', 'Paula', 'Bruno', 'Julia'],
}
LAST = {
    'North America': ['Smith', 'Johnson', 'Williams', 'Brown', 'Miller', 'Davis', 'Garcia', 'Wilson', 'Anderson', 'Taylor', 'Thomas', 'Moore', 'Martin', 'Lee', 'Clark', 'Walker', 'Hall', 'Young', 'King', 'Wright'],
    'EMEA': ['Müller', 'Schmidt', 'Dubois', 'Rossi', 'Jansen', 'Popescu', 'Ionescu', 'García', 'Nowak', 'Andersson', 'Hansen', 'Smith', 'Jones', 'Bernard', 'Kowalski', 'Novák', 'Yılmaz', 'Cohen', 'Murphy', 'Weber'],
    'APAC': ['Tanaka', 'Suzuki', 'Sharma', 'Patel', 'Chen', 'Wang', 'Kim', 'Park', 'Nguyen', 'Tran', 'Singh', 'Watanabe', 'Lim', 'Tan', 'Wilson', 'Taylor', 'Santoso', 'Reyes', 'Wong', 'Lee'],
    'LATAM': ['Silva', 'Santos', 'Oliveira', 'González', 'Rodríguez', 'Martínez', 'López', 'Pérez', 'Gómez', 'Fernández', 'Souza', 'Costa', 'Ramírez', 'Torres', 'Flores', 'Rojas', 'Díaz', 'Morales', 'Castro', 'Vargas'],
}
PRE = ['Blue', 'North', 'Bright', 'Peak', 'Silver', 'Quantum', 'Harbor', 'Atlas', 'Nova', 'Cedar', 'Summit', 'Vertex', 'Lumen', 'Iron', 'Pixel', 'Green', 'Swift', 'Clear',
       'Prime', 'Orbit', 'Echo', 'Delta', 'Maple', 'Coral', 'Falcon', 'Granite', 'Helix', 'Kite', 'Lotus', 'Metro', 'Nimbus', 'Oak', 'Pine', 'Rapid', 'Sage', 'Terra', 'Urban',
       'Vivid', 'Wave', 'Zen', 'Amber', 'Bold', 'Cobalt', 'Dune', 'Ember', 'Fjord', 'Glow', 'Hive', 'Indigo', 'Jade', 'Keystone', 'Lark', 'Mosaic', 'Nest', 'Opal', 'Polar', 'Quill', 'Ridge', 'Solar', 'Tidal']
POST = ['works', 'labs', 'logic', 'soft', 'media', 'data', 'systems', 'studio', 'digital', 'tech', 'craft', 'ware', 'flow', 'point', 'line', 'hub', 'bridge', 'forge', 'stack',
        'cloud', 'mind', 'scale', 'path', 'gate', 'base', 'loop', 'spark', 'field', 'grid', 'wise']
IND_WORD = [''] * 6 + [' Logistics', ' Health', ' Capital', ' Foods', ' Consulting', ' Retail', ' Energy', ' Group', ' Partners', ' Studio', ' Learning', ' Robotics']
SUFFIX = {'US': ['Inc.', 'LLC', 'Corp.'], 'CA': ['Inc.', 'Ltd.'], 'GB': ['Ltd', 'plc'], 'IE': ['Ltd'], 'DE': ['GmbH', 'AG'], 'AT': ['GmbH'], 'CH': ['AG', 'GmbH'],
          'FR': ['SAS', 'SA'], 'NL': ['B.V.'], 'BE': ['BV', 'SA'], 'ES': ['S.L.', 'S.A.'], 'IT': ['S.r.l.', 'S.p.A.'], 'PT': ['Lda'], 'SE': ['AB'], 'DK': ['ApS'],
          'NO': ['AS'], 'FI': ['Oy'], 'PL': ['sp. z o.o.'], 'RO': ['SRL', 'S.A.'], 'CZ': ['s.r.o.'], 'AU': ['Pty Ltd'], 'NZ': ['Ltd'], 'IN': ['Pvt Ltd'],
          'JP': ['K.K.', 'Co., Ltd.'], 'SG': ['Pte Ltd'], 'BR': ['Ltda', 'S.A.'], 'MX': ['S.A. de C.V.'], 'AR': ['S.A.', 'S.R.L.'], 'CO': ['S.A.S.'], 'CL': ['SpA'],
          'KR': ['Co., Ltd.'], 'HK': ['Limited'], 'MY': ['Sdn Bhd'], 'ID': ['PT'], 'ZA': ['(Pty) Ltd']}
TLD = {'US': '.com', 'GB': '.co.uk', 'AU': '.com.au', 'BR': '.com.br', 'JP': '.co.jp', 'NZ': '.co.nz', 'MX': '.com.mx', 'KR': '.co.kr', 'ZA': '.co.za', 'AR': '.com.ar'}
INDUSTRIES = ['Software', 'Marketing & Advertising', 'Consulting', 'E-commerce', 'Education', 'Healthcare', 'Financial Services', 'Manufacturing', 'Non-profit', 'Media',
              'Logistics', 'Real Estate', 'Construction', 'Government']
IND_W = np.array([18, 14, 12, 10, 7, 6, 7, 6, 4, 5, 4, 3, 3, 1], float); IND_W /= IND_W.sum()
CITIES = {'US': ['New York, NY', 'Austin, TX', 'Chicago, IL', 'Seattle, WA', 'Denver, CO', 'Boston, MA'], 'CA': ['Toronto, ON', 'Vancouver, BC', 'Montréal, QC'],
          'GB': ['London', 'Manchester', 'Bristol', 'Edinburgh'], 'DE': ['Berlin', 'München', 'Hamburg', 'Köln'], 'FR': ['Paris', 'Lyon', 'Nantes'],
          'NL': ['Amsterdam', 'Rotterdam', 'Utrecht'], 'AU': ['Sydney NSW', 'Melbourne VIC', 'Brisbane QLD'], 'JP': ['Tokyo', 'Osaka', 'Fukuoka'],
          'IN': ['Bengaluru', 'Mumbai', 'Pune', 'Hyderabad'], 'BR': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte'], 'MX': ['Ciudad de México', 'Guadalajara', 'Monterrey'],
          'SG': ['Singapore'], 'RO': ['Cluj-Napoca', 'București', 'Iași'], 'ES': ['Madrid', 'Barcelona', 'Valencia']}
used_names = set()


def company_name(iso, unique=True):
    base = ''
    for _ in range(60):
        base = random.choice(PRE) + random.choice(POST) + random.choice(IND_WORD)
        if not unique or base not in used_names: break
    else:
        base += ' ' + random.choice(['Global', 'International', 'Holdings', 'Solutions', 'Works'])
    used_names.add(base)
    suf = random.choice(SUFFIX.get(iso, ['Ltd']))
    return (('PT ' + base) if suf == 'PT' else f'{base} {suf}'), base


def domain_of(base, iso):
    return re.sub('[^a-z]', '', base.lower())[:22] + ('.com' if random.random() < .45 else TLD.get(iso, '.' + iso.lower()))


def person(region):
    f, l = random.choice(FIRST[region]), random.choice(LAST[region])
    return f, l


def email_of(f, l, dom):
    pat = random.random()
    f2, l2 = ascii_(f).lower().replace(' ', '').replace('-', ''), ascii_(l).lower().replace(' ', '')
    local = f'{f2}.{l2}' if pat < .6 else (f'{f2[0]}{l2}' if pat < .85 else f2)
    return f'{local}@{dom}'


def city(iso): return random.choice(CITIES.get(iso, ['—']))


# ───────────────────────── acquisition ─────────────────────────
# activation rate, paid rate given activated, signups per session
CH_RATES = {'Organic Search': (.46, .30, .021), 'Direct': (.50, .33, .030), 'Referral': (.56, .34, .045), 'Partners': (.64, .44, .060),
            'Paid Search': (.42, .29, None), 'Paid Social': (.30, .22, None)}
ORGANIC_BASE = {'Organic Search': 8.0, 'Direct': 3.2, 'Referral': 2.0, 'Partners': .85}
REFERRERS = ['g2.com', 'capterra.com', 'producthunt.com', 'medium.com', 'youtube.com', 'reddit.com', 'news.ycombinator.com', 'getapp.com']
PARTNERS = [('Northbeam Consulting', 'North America'), ('Agile Partners GmbH', 'EMEA'), ('Kaizen Digital', 'APAC'), ('Brightpath Solutions', 'EMEA'),
            ('Andes Digital', 'LATAM'), ('Southern Cross IT', 'APAC'), ('Loop Advisory', 'EMEA'), ('Pragmatica', 'LATAM'), ('Clearview Partners', 'North America')]

C = lambda *a: dict(zip(['platform', 'name', 'start', 'end', 'budget', 'model', 'unit', 'ctr', 'cvr', 'q', 'region'], a))
CAMPAIGNS = [
    C('google', 'GS_Brand_Global', '2024-01-01', None, 110, 'cpc', .95, .090, .120, 1.15, None),
    C('google', 'GS_Generic_ProjectMgmt_NA', '2024-01-01', None, 380, 'cpc', 4.10, .034, .048, 1.00, 'North America'),
    C('google', 'GS_Generic_ProjectMgmt_EMEA', '2024-01-01', None, 260, 'cpc', 3.00, .036, .046, 1.00, 'EMEA'),
    C('google', 'GS_Competitor_Conquest_NA', '2024-04-01', None, 180, 'cpc', 6.40, .022, .030, .85, 'North America'),
    C('google', 'GS_Generic_LATAM', '2024-06-03', None, 80, 'cpc', .90, .041, .040, .80, 'LATAM'),
    C('google', 'GS_Generic_APAC', '2025-01-06', None, 170, 'cpc', 1.70, .039, .058, 1.15, 'APAC'),
    C('google', 'PMax_Global', '2025-03-03', None, 320, 'cpc', 1.55, .018, .034, .62, None),
    C('google', 'GS_Insights_Launch', '2025-04-01', '2025-07-31', 240, 'cpc', 2.80, .030, .050, 1.20, None),
    C('meta', 'FB_Prospecting_LAL_NA', '2024-01-01', '2026-06-14', 280, 'cpm', 14.0, .011, .026, .70, 'North America'),
    C('meta', 'FB_Prospecting_Broad_EMEA', '2024-01-01', None, 200, 'cpm', 9.0, .012, .022, .70, 'EMEA'),
    C('meta', 'FB_Retargeting_Global', '2024-01-01', None, 85, 'cpm', 21.0, .021, .060, 1.00, None),
    C('meta', 'FB_BlackFriday_2024', '2024-11-21', '2024-12-02', 850, 'cpm', 16.0, .019, .050, .45, None),
    C('meta', 'IG_Reels_Awareness_Global', '2025-02-03', None, 240, 'cpm', 6.5, .007, .010, .50, None),
    C('meta', 'FB_Prospecting_APAC', '2025-05-05', None, 150, 'cpm', 5.0, .013, .024, .90, 'APAC'),
    C('meta', 'FB_BlackFriday_2025', '2025-11-20', '2025-12-01', 1050, 'cpm', 17.5, .018, .045, .40, None),
    C('meta', 'Meta_AdvantagePlus_2026', '2026-01-12', None, 420, 'cpm', 11.0, .010, .018, .45, None),
    C('linkedin', 'LI_Leadgen_EMEA', '2024-01-01', None, 230, 'cpc', 7.60, .0065, .050, 1.60, 'EMEA'),
    C('linkedin', 'LI_ABM_Enterprise_NA', '2024-03-04', None, 360, 'cpc', 9.40, .0055, .042, 2.00, 'North America'),
    C('linkedin', 'LI_Webinar_Q3_2025', '2025-07-01', '2025-09-30', 190, 'cpc', 6.90, .0070, .060, 1.30, None),
    C('linkedin', 'LI_ABM_APAC', '2025-09-01', None, 140, 'cpc', 6.20, .0060, .045, 1.70, 'APAC'),
]
for c in CAMPAIGNS:
    c['start'] = date.fromisoformat(c['start'])
    c['end'] = date.fromisoformat(c['end']) if c['end'] else END
    c['id'] = str(random.randint(10 ** 10, 10 ** 11))

signups, customers, ad_rows = [], [], []
ga = defaultdict(lambda: [0.0, 0, 0])  # (day, ga channel, country idx) -> sessions, sign_up, first_board_created
PLAN_LABEL = {'starter': 'Starter', 'team': 'Team', 'business': 'Business', 'enterprise': 'Enterprise'}


def new_signup(d, ch, w, q=1.0, camp=None, partner=None, src=''):
    ci = int(rng.choice(NC, p=w))
    iso, region = COUNTRIES[ci][1], COUNTRIES[ci][2]
    hour = int((rng.normal(13, 3) - UTC_OFF[region]) % 24)
    ts = datetime(d.year, d.month, d.day, hour, random.randint(0, 59), random.randint(0, 59))
    f, l = person(region)
    cname, base = company_name(iso, unique=False)
    dom = domain_of(base, iso) if random.random() < .8 else random.choice(['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com'])
    pa, pp, _ = CH_RATES[ch]
    act = random.random() < min(.95, pa * q ** .3)
    s = dict(id=len(signups) + 1, ts=ts, ch=ch, camp=camp['name'] if camp else '', platform=camp['platform'] if camp else '', src=src, ci=ci, q=q, act=act,
             partner=partner, promo=in_bf(d), first=f, last=l, email=email_of(f, l, dom), company=cname, base=base, cust=None,
             industry=INDUSTRIES[rng.choice(len(INDUSTRIES), p=IND_W)])
    s['act_date'] = d + timedelta(days=random.randint(0, 6)) if act else None
    signups.append(s)
    gch = 'Referral' if ch == 'Partners' else ch
    if random.random() < .9: ga[(d, gch, ci)][1] += 1  # cookie consent: ~10% of sign-ups never reach GA4
    if act and s['act_date'] <= END and random.random() < .9: ga[(s['act_date'], gch, ci)][2] += 1
    if act and random.random() < min(.9, pp * q ** .5 * (1.15 if s['promo'] else 1)):
        paid = d + timedelta(days=random.randint(1, 14))
        if paid <= END: make_selfserve(s, paid)


def gen_acquisition():
    for d in DAYS:
        g, se, w = growth(d), SEASON[d.month], DOW[d.weekday()]
        cw = country_w(d)
        for ch, base in ORGANIC_BASE.items():
            lam = base * g * se * w * (1.35 if in_bf(d) else 1)
            sess = int(lam / CH_RATES[ch][2] * rng.lognormal(0, .08))
            for i in np.nonzero(alloc := rng.multinomial(sess, cw))[0]:
                ga[(d, 'Referral' if ch == 'Partners' else ch, int(i))][0] += alloc[i]
            for _ in range(pois(lam)):
                if ch == 'Partners':
                    pn, preg = PARTNERS[rng.choice(len(PARTNERS))]
                    new_signup(d, ch, country_w(d, preg) if random.random() < .75 else cw, 1.1, partner=pn, src=pn)
                else:
                    src = {'Organic Search': random.choices(['google', 'bing', 'duckduckgo', 'yahoo'], [88, 7, 4, 1])[0], 'Direct': '',
                           'Referral': random.choice(REFERRERS)}[ch]
                    new_signup(d, ch, cw, 1.0, src=src)
        for c in CAMPAIGNS:
            if not (c['start'] <= d <= c['end']): continue
            mi = midx(d)
            weekend = d.weekday() >= 5
            budget = c['budget'] * 1.012 ** mi * (.6 + .4 * se) * (.65 if weekend and c['platform'] != 'meta' else 1) * rng.lognormal(0, .12)
            if c['model'] == 'cpc':
                cpc = c['unit'] * rng.lognormal(0, .1) * (1 + .004 * mi)
                clicks = pois(budget / cpc)
                spend = clicks * cpc
                imps = int(clicks / (c['ctr'] * rng.lognormal(0, .1))) if clicks else pois(budget / cpc / c['ctr'])
            else:
                imps = int(budget / c['unit'] * 1000 * rng.lognormal(0, .05))
                clicks = int(rng.binomial(imps, min(.5, c['ctr'] * rng.lognormal(0, .1))))
                spend = budget
            cvr = c['cvr'] * (.62 if c['platform'] == 'meta' and d >= PRICE_UP else 1) * (1.4 if in_bf(d) and 'BlackFriday' in c['name'] else 1)
            n = int(rng.binomial(clicks, min(.9, cvr)))
            w2 = country_w(d, c['region'])
            ch = 'Paid Search' if c['platform'] == 'google' else 'Paid Social'
            for i in np.nonzero(alloc := rng.multinomial(int(clicks * .85), w2))[0]:
                ga[(d, ch, int(i))][0] += alloc[i]
            src = {'google': 'google', 'linkedin': 'linkedin'}.get(c['platform']) or ('instagram' if c['name'].startswith('IG') else 'facebook')
            first_id = len(signups)
            for _ in range(n): new_signup(d, ch, w2, c['q'], camp=c, src=src)
            conv = round(n * rng.uniform(1.05, 1.45))  # platforms over-attribute
            ad_rows.append(dict(d=d, c=c, imps=imps, clicks=clicks, spend=round(spend, 2), signups=n, conv=conv,
                                value=round(conv * rng.uniform(90, 140), 2), sids=range(first_id, len(signups))))


# ───────────────────────── subscriptions ─────────────────────────
BASE_CHURN = {'starter': .055, 'team': .030, 'business': .016}
UNIT_USD = {'starter': 12, 'business': 45}


def unit_usd(plan, d): return (29 if d >= PRICE_UP else 25) if plan == 'team' else UNIT_USD[plan]


def churn_p(c, nd):
    h = BASE_CHURN[c['plan']] * REGION_CHURN[c['region']] * c['q'] ** -.4 * (2.0 if c['promo'] else 1)
    if c['promo'] and abs((nd - c['start']).days - 365) < 40: h *= 3  # discount ends
    if OUTAGE <= nd <= date(2025, 8, 15): h *= 1.35
    if date(2026, 1, 20) <= nd <= date(2026, 4, 30): h *= {'team': 2.8, 'starter': 1.4}.get(c['plan'], 1)
    if c['billing'] == 'annual':
        if c['plan'] == 'team' and nd.year == 2026: h *= 1.6
        return 1 - (1 - h * .55) ** 12
    return h


def new_customer_id(): return f'LUM-{len(customers) + 1:05d}'


def make_selfserve(s, paid):
    q = s['q']
    pw = [.15, .45, .40] if q > 1.4 else ([.60, .33, .07] if q < .6 else [.45, .40, .15])
    if s['ch'] == 'Partners': pw = [.2, .45, .35]
    plan = random.choices(['starter', 'team', 'business'], pw)[0]
    seats = {'starter': random.randint(1, 5), 'team': clamp(round(rng.lognormal(math.log(6), .55)), 3, 60),
             'business': clamp(round(rng.lognormal(math.log(12), .5)), 10, 300)}[plan]
    iso = COUNTRIES[s['ci']][1]
    cname, base = company_name(iso)  # paying customers get unique names
    dom = domain_of(base, iso)
    s['company'], s['email'] = cname, email_of(s['first'], s['last'], dom)
    c = dict(id=new_customer_id(), kind='self', signup=s, company=cname, ci=s['ci'], region=COUNTRIES[s['ci']][2], plan=plan, seats=seats,
             billing='annual' if random.random() < {'starter': .2, 'team': .3, 'business': .45}[plan] else 'monthly',
             cur=currency(iso), start=paid, churn=None, churn_type=None, events=[], charges=[], invoices=[], q=q, promo=s['promo'],
             addon=paid >= INSIGHTS_LAUNCH and plan != 'starter' and random.random() < {'team': .2, 'business': .35}[plan],
             stripe=rid('cus_', 14), email=s['email'], contact=f"{s['first']} {s['last']}", partner=s['partner'], industry=s['industry'])
    s['cust'] = c
    customers.append(c)
    sim_selfserve(c)


def charge(c, ts, amt, status):
    if START <= ts.date() <= END:
        c['charges'].append(dict(ts=ts, amt=amt, status=status, plan=c['plan'], seats=c['seats'], billing=c['billing'],
                                 coupon='BF40' if c['promo'] and ts.date() < c['start'] + timedelta(365) else ''))


def end_sub(c, d, kind):
    c['churn'], c['churn_type'] = d, kind
    c['events'].append((d, 0.0, c['plan'], 0, False))


def sim_selfserve(c):
    k, months = 0, (12 if c['billing'] == 'annual' else 1)
    while True:
        d = add_months(c['start'], k)
        if d > END: return
        unit = local_price(unit_usd(c['plan'], d), c['cur']) + (local_price(8, c['cur']) if c['addon'] else 0)
        disc = .4 if c['promo'] and d < c['start'] + timedelta(365) else 0
        amt = money(c['seats'] * unit * months * (1 - disc), c['cur'])
        ts = datetime(d.year, d.month, d.day, random.randint(0, 23), random.randint(0, 59), random.randint(0, 59))
        if random.random() < .035:
            charge(c, ts, amt, 'failed')
            if random.random() < .6:
                charge(c, ts + timedelta(days=random.randint(1, 5), hours=random.randint(0, 12)), amt, 'paid')
            else:
                return end_sub(c, d, 'involuntary')
        else:
            status = 'refunded' if random.random() < .008 else 'paid'
            charge(c, ts, amt, status)
            if status == 'refunded' and random.random() < .5:
                return end_sub(c, d + timedelta(days=random.randint(1, 10)), 'voluntary')
        c['events'].append((d, amt / months * fx(c['cur'], d), c['plan'], c['seats'], c['addon']))
        k += months
        nd = add_months(c['start'], k)
        if nd > END: return
        if random.random() < churn_p(c, nd):
            return end_sub(c, nd, 'voluntary')
        f = 10 if months == 12 else 1
        if random.random() < .025 * f * .8: c['seats'] = math.ceil(c['seats'] * rng.uniform(1.08, 1.3))
        elif random.random() < .015 * f * .6: c['seats'] = max(1, math.floor(c['seats'] * rng.uniform(.65, .9)))
        if c['plan'] == 'starter' and (c['seats'] > 5 or random.random() < .015 * f): c['plan'] = 'team'; c['seats'] = max(3, c['seats'])
        elif c['plan'] == 'team' and random.random() < .008 * f: c['plan'] = 'business'; c['seats'] = max(10, c['seats'])
        if nd >= INSIGHTS_LAUNCH and c['plan'] != 'starter' and not c['addon'] and random.random() < .035 * f * .85: c['addon'] = True


# ───────────────────────── enterprise sales ─────────────────────────
REPS = [('Jordan Blake', 'North America', date(2023, 5, 1), None), ('Priya Natarajan', 'North America', date(2023, 9, 1), None),
        ('Marcus Webb', 'North America', date(2023, 2, 1), date(2025, 10, 31)), ('Alexis Moreno', 'North America', date(2025, 11, 3), None),
        ('Dana Kowalczyk', 'North America', date(2025, 2, 3), None),
        ('Sophie Laurent', 'EMEA', date(2023, 1, 9), None), ('Lukas Brandt', 'EMEA', date(2023, 6, 1), None), ('Ioana Marin', 'EMEA', date(2025, 3, 3), None),
        ('Kenji Watanabe', 'APAC', date(2023, 10, 2), None), ('Chloe Tan', 'APAC', date(2025, 6, 2), None), ('Camila Rojas', 'LATAM', date(2024, 4, 15), None)]
DEAL_BASE = {'North America': 5.0, 'EMEA': 4.2, 'APAC': 1.5, 'LATAM': 1.1}
WIN = {'North America': .24, 'EMEA': .29, 'APAC': .27, 'LATAM': .18}
LOST_REASONS = ['Chose competitor - price', 'Chose competitor - features', 'No decision / stalled', 'Budget cut', 'Security review not passed',
                'Went with incumbent tool', 'Timing - revisit next FY', 'Champion left company']
deals = []


def rep_for(region, d):
    act = [r for r in REPS if r[1] == region and r[2] <= d and (r[3] is None or r[3] >= d)]
    return random.choice(act)[0] if act else 'Jordan Blake'  # LATAM was covered from North America before Camila


def gen_deals():
    n = 0
    for y, m in MONTHS:
        mi = (y - 2024) * 12 + m - 1
        for region, base in DEAL_BASE.items():
            lam = base * 1.025 ** mi * (1.7 if region == 'APAC' and y >= 2025 else 1) * (1.3 if region == 'North America' and date(y, m, 1) >= date(2025, 2, 1) else 1)
            for _ in range(pois(lam)):
                n += 1
                created = date(y, m, random.randint(1, calendar.monthrange(y, m)[1]))
                cycle = int(rng.lognormal(math.log(72), .45))
                close = created + timedelta(days=cycle)
                ci = int(rng.choice(NC, p=country_w(created, region)))
                iso = COUNTRIES[ci][1]
                seats = clamp(int(rng.lognormal(math.log(60), .7)), 30, 2000)
                price = round(rng.uniform(44, 62), 2)
                addon = random.random() < (.45 if created >= INSIGHTS_LAUNCH else 0)
                win = WIN[region]
                if region == 'North America' and date(2026, 4, 1) <= close <= date(2026, 6, 30): win = .09  # lost a string of deals to a competitor
                if region == 'EMEA' and close.year == 2026: win = .35
                src = random.choices(['Outbound', 'Inbound - LinkedIn', 'Partner', 'Event', 'Inbound - Website'], [52, 20, 10, 10, 8])[0]
                cname, base = company_name(iso)
                if close > END:
                    prog = (END - created).days / cycle
                    stage = 'Discovery' if prog < .25 else 'Demo scheduled' if prog < .5 else 'Proposal sent' if prog < .75 else 'Negotiation'
                    close_out = close
                else:
                    stage = 'Closed won' if random.random() < win else 'Closed lost'
                    close_out = close if stage == 'Closed won' else created + timedelta(days=int(cycle * rng.uniform(.4, 1)))
                f, l = person(region)
                dl = dict(id=f'{18_000_000_000 + n * 7919}', company=cname, base=base, ci=ci, region=region, created=created, close=close_out, stage=stage,
                          seats=seats, price=price, addon=addon, amount=round(seats * (price + (6 if addon else 0)) * 12, 0), rep=rep_for(region, created),
                          source=src, lost=random.choice(LOST_REASONS) if stage == 'Closed lost' else '', contact=f'{f} {l}', email=email_of(f, l, domain_of(base, iso)),
                          industry=INDUSTRIES[rng.choice(len(INDUSTRIES), p=IND_W)])
                if stage == 'Closed lost' and region == 'North America' and date(2026, 4, 1) <= close_out <= date(2026, 6, 30):
                    dl['lost'] = random.choice(['Chose competitor - price', 'Chose competitor - price', 'Chose competitor - AI features'])
                deals.append(dl)
                if stage == 'Closed won':
                    start = close_out + timedelta(days=random.randint(5, 20))
                    if start <= END: make_enterprise(dl, start)


def make_enterprise(dl, start):
    iso = COUNTRIES[dl['ci']][1]
    cur = currency(iso) if currency(iso) in ('EUR', 'GBP') else 'USD'
    c = dict(id=new_customer_id(), kind='ent', deal=dl, company=dl['company'], ci=dl['ci'], region=dl['region'], plan='enterprise', seats=dl['seats'],
             billing='annual' if random.random() < .7 else 'quarterly', cur=cur, start=start, churn=None, churn_type=None, events=[], charges=[], invoices=[],
             q=1.5, promo=False, addon=dl['addon'], stripe='', email=dl['email'], contact=dl['contact'], partner=None, price=dl['price'],
             terms=random.choice([30, 30, 30, 45, 60]), po=f'PO-{random.randint(10000, 99999)}' if random.random() < .6 else '', industry=dl['industry'])
    dl['cust'] = c
    customers.append(c)
    services = round(rng.uniform(4, 25)) * 1000
    c['invoices'].append(dict(date=start, kind='services', lines=[('Onboarding & implementation services (fixed fee)', 1, local_price(services, cur) if cur != 'USD' else services)]
                              + ([('Premium support — 12 months', 1, local_price(9600, cur))] if random.random() < .35 else [])))
    k = 0
    while True:
        s = add_months(start, 12 * k)
        if s > END: return
        if k:
            churn = .07 * (2 if c['region'] == 'North America' and s.year == 2026 else 1)
            if random.random() < churn: return end_sub(c, s, 'voluntary')
            if random.random() < .45: c['seats'] = math.ceil(c['seats'] * rng.uniform(1.1, 1.6))
            elif random.random() < .1: c['seats'] = math.floor(c['seats'] * rng.uniform(.7, .9))
            if not c['addon'] and s >= INSIGHTS_LAUNCH and random.random() < .3: c['addon'] = True
            c['price'] = round(c['price'] * 1.04, 2)
        unit = c['price'] if cur == 'USD' else round(c['price'] * LOCAL[cur], 2)
        add = 6 if cur == 'USD' else round(6 * LOCAL[cur], 2)
        periods = [(s, 12)] if c['billing'] == 'annual' else [(add_months(s, 3 * i), 3) for i in range(4)]
        for pd, mths in periods:
            if pd > END: break
            lines = [(f'Lumora Enterprise platform — {c["seats"]} seats × {mths} months ({pd:%d %b %Y} – {add_months(pd, mths) - timedelta(1):%d %b %Y})', c['seats'] * mths, unit)]
            if c['addon']: lines.append((f'Lumora Insights add-on — {c["seats"]} seats × {mths} months', c['seats'] * mths, add))
            c['invoices'].append(dict(date=pd, kind='subscription', lines=lines))
        c['events'].append((s, c['seats'] * (c['price'] + (6 if c['addon'] else 0)), 'enterprise', c['seats'], c['addon']))
        k += 1


def gen_legacy():
    """Customers won 2021–2023 (founded 2021). Their pre-2024 billing is not part of the dump, only their CRM records and later renewals."""
    d0 = date(2021, 1, 1)
    w = REGION_W0[REG_IDX] * WITHIN; w = w / w.sum()
    for k in range(36):
        y, m = 2021 + k // 12, k % 12 + 1
        for _ in range(pois(28 + 2.2 * k)):
            d = date(y, m, random.randint(1, 28))
            ch = random.choices(['Organic Search', 'Direct', 'Referral', 'Partners'], [55, 20, 18, 7])[0]
            ci = int(rng.choice(NC, p=w)); region = COUNTRIES[ci][2]
            f, l = person(region)
            s = dict(id=len(signups) + 1, ts=datetime(y, m, d.day, random.randint(6, 20), random.randint(0, 59)), ch=ch, camp='', platform='',
                     src={'Organic Search': 'google', 'Direct': '', 'Referral': random.choice(REFERRERS)}.get(ch, ''), ci=ci, q=1.1, act=True,
                     partner=random.choice(PARTNERS)[0] if ch == 'Partners' else None, promo=False, first=f, last=l, email='', company='', base='',
                     cust=None, industry=INDUSTRIES[rng.choice(len(INDUSTRIES), p=IND_W)], act_date=d)
            signups.append(s)
            make_selfserve(s, d + timedelta(days=random.randint(1, 14)))
    for _ in range(46):
        region = random.choices(REGIONS, [55, 35, 7, 3])[0]
        created = d0 + timedelta(days=random.randint(0, 3 * 365 - 120))
        ci = int(rng.choice(NC, p=country_w(START, region))); iso = COUNTRIES[ci][1]
        cname, base = company_name(iso)
        f, l = person(region)
        seats = clamp(int(rng.lognormal(math.log(60), .7)), 30, 1500)
        price = round(rng.uniform(46, 60), 2)
        reps = [r[0] for r in REPS if r[1] == region and r[2] < START] or ['Jordan Blake']
        dl = dict(id='', company=cname, base=base, ci=ci, region=region, created=created, close=created + timedelta(days=80), stage='Closed won', seats=seats,
                  price=price, addon=False, amount=seats * price * 12, rep=random.choice(reps), source='Outbound', lost='', contact=f'{f} {l}',
                  email=email_of(f, l, domain_of(base, iso)), industry=INDUSTRIES[rng.choice(len(INDUSTRIES), p=IND_W)])
        make_enterprise(dl, dl['close'] + timedelta(days=10))


# ───────────────────────── derived state ─────────────────────────
def mrr_at(c, t):
    v = 0.0
    for d, m, *_ in c['events']:
        if d > t: break
        v = m
    return v


def active(c, t): return c['start'] <= t and (c['churn'] is None or c['churn'] > t)


def seats_at(c, t):
    v = 0
    for d, _, _, s, _ in c['events']:
        if d > t: break
        v = s
    return v


def build_monthly():
    M = {}
    prev = {c['id']: mrr_at(c, START - timedelta(1)) for c in customers}
    for y, m in MONTHS:
        t = month_end(y, m)
        row = dict(mrr_self=0., mrr_ent=0., mrr_region=defaultdict(float), customers=0, ent_customers=0, new=0, churned=0, seats=defaultdict(int),
                   new_mrr=0., exp_mrr=0., con_mrr=0., churn_mrr=0., addon_seats=defaultdict(int))
        for c in customers:
            v = mrr_at(c, t)
            p = prev.get(c['id'], 0.)
            if v > 0:
                row['customers'] += 1
                row['ent_customers'] += c['kind'] == 'ent'
                row['mrr_ent' if c['kind'] == 'ent' else 'mrr_self'] += v
                row['mrr_region'][c['region']] += v
                st = seats_at(c, t)
                row['seats'][c['region']] += st
                if c['events'] and any(e[4] for e in c['events'] if e[0] <= t): row['addon_seats'][c['region']] += st
            if p == 0 and v > 0: row['new'] += 1; row['new_mrr'] += v
            elif p > 0 and v == 0: row['churned'] += 1; row['churn_mrr'] += p
            elif v > p: row['exp_mrr'] += v - p
            elif v < p: row['con_mrr'] += p - v
            prev[c['id']] = v
        M[(y, m)] = row
    return M


# ───────────────────────── writers: marketing ─────────────────────────
def w_csv(path, header, rows, delim=',', pre_lines=(), encoding='utf-8'):
    with open(path, 'w', newline='', encoding=encoding) as f:
        for l in pre_lines: f.write(l + '\n')
        wr = csv.writer(f, delimiter=delim)
        wr.writerow(header)
        wr.writerows(rows)


def fmt_num(v, dec=2): return f'{v:,.{dec}f}'


def write_ads():
    by = defaultdict(list)
    for r in ad_rows: by[(r['c']['platform'], r['d'].year, r['d'].month)].append(r)
    for (pf, y, m), rows in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
        rows.sort(key=lambda r: (r['d'], r['c']['name']))
        last = month_end(y, m)
        if pf == 'google':  # Google Ads UI export: title lines, thousands separators, % strings, totals row
            body = [[r['d'].isoformat(), r['c']['name'], r['c']['id'], 'Enabled', 'Search' if 'PMax' not in r['c']['name'] else 'Performance Max', 'USD',
                     fmt_num(r['imps'], 0), fmt_num(r['clicks'], 0), f"{(r['clicks'] / r['imps'] * 100 if r['imps'] else 0):.2f}%",
                     fmt_num(r['spend'] / r['clicks'] if r['clicks'] else 0), fmt_num(r['spend']), f"{r['conv']:.2f}", fmt_num(r['value'])] for r in rows]
            tot = ['Total: Account', '', '', '', '', 'USD', fmt_num(sum(r['imps'] for r in rows), 0), fmt_num(sum(r['clicks'] for r in rows), 0), '--', '--',
                   fmt_num(sum(r['spend'] for r in rows)), f"{sum(r['conv'] for r in rows):.2f}", fmt_num(sum(r['value'] for r in rows))]
            w_csv(out('marketing', 'google_ads', f'Campaign report_{y}-{m:02d}.csv'),
                  ['Day', 'Campaign', 'Campaign ID', 'Campaign status', 'Campaign type', 'Currency code', 'Impr.', 'Clicks', 'CTR', 'Avg. CPC', 'Cost', 'Conversions', 'Conv. value'],
                  body + [tot], pre_lines=['Campaign report', f'{MNAME[m]} 1, {y} - {MNAME[m]} {last.day}, {y}'])
        elif pf == 'meta':  # Meta account bills in EUR; blank results, percent as plain number
            body = []
            for r in rows:
                e = 1 / fx('EUR', r['d'])
                reach = int(r['imps'] / rng.uniform(1.4, 2.6))
                body.append([r['d'].isoformat(), r['d'].isoformat(), r['c']['name'], 'active' if r['c']['end'] >= END else 'completed',
                             f"{r['spend'] * e:.2f}", r['imps'], reach, r['clicks'], f"{r['clicks'] / r['imps'] * 100:.4f}" if r['imps'] else '',
                             r['conv'] or '', 'Website registrations completed' if r['conv'] else '', f"{r['spend'] * e / r['conv']:.2f}" if r['conv'] else '',
                             f"{r['value'] * e:.2f}" if r['conv'] else '0'])
            w_csv(out('marketing', 'meta_ads', f'Lumora-Ads-Campaigns-{MNAME[m][:3]}-1-{y}-{MNAME[m][:3]}-{last.day}-{y}.csv'),
                  ['Reporting starts', 'Reporting ends', 'Campaign name', 'Campaign delivery', 'Amount spent (EUR)', 'Impressions', 'Reach', 'Link clicks',
                   'CTR (link click-through rate)', 'Results', 'Result indicator', 'Cost per result', 'Website registrations conversion value'], body)
        else:  # LinkedIn Campaign Manager: metadata block, M/D/YYYY dates, CTR as fraction
            body = [[f'{r["d"].month}/{r["d"].day}/{r["d"].year}', 'Lumora Software', r['c']['name'], r['c']['id'], 'Lead Generation' if 'Leadgen' in r['c']['name'] else 'Website Conversions',
                     f"{r['spend']:.2f}", r['imps'], r['clicks'], f"{r['clicks'] / r['imps']:.5f}" if r['imps'] else '0', f"{r['spend'] / r['clicks']:.2f}" if r['clicks'] else '',
                     r['conv'] if 'Leadgen' not in r['c']['name'] else 0, r['conv'] if 'Leadgen' in r['c']['name'] else 0] for r in rows]
            w_csv(out('marketing', 'linkedin_ads', f'campaign_performance_report_{y}{m:02d}.csv'),
                  ['Start Date (in UTC)', 'Account Name', 'Campaign Name', 'Campaign ID', 'Campaign Objective', 'Total Spent', 'Impressions', 'Clicks', 'Click Through Rate',
                   'Average CPC', 'Conversions', 'Leads'], body,
                  pre_lines=['Campaign Performance Report (in USD)', f'Report Start: {m}/1/{y}, 12:00 AM', f'Report End: {m}/{last.day}/{y}, 11:59 PM',
                             f'Date Generated: {add_months(date(y, m, 1), 1):%b %d, %Y}, 9:04 AM', 'Time Zone: UTC', ''])


def write_ga4():
    by = defaultdict(list)
    for (d, ch, ci), (s, su, ac) in ga.items():
        s = int(max(s, su / .06 if su else 0))
        if s or su or ac: by[(d.year, d.month)].append((d, ch, ci, s, su, ac))
    for (y, m), rows in sorted(by.items()):
        rows.sort(key=lambda r: (r[0], r[1], COUNTRIES[r[2]][0]))
        body = [[r[0].strftime('%Y%m%d'), r[1], COUNTRIES[r[2]][0], r[3], int(r[3] * rng.uniform(.55, .72)), int(r[3] * rng.uniform(.07, .14)), r[4], r[5]] for r in rows]
        w_csv(out('marketing', 'ga4', f'ga4_traffic_acquisition_{y}{m:02d}.csv'),
              ['Date', 'Session default channel group', 'Country', 'Sessions', 'Engaged sessions', 'Views (/pricing)', 'Key events (sign_up)', 'Key events (first_board_created)'],
              body, pre_lines=['# ----------------------------------------', '# Traffic acquisition: Session default channel group', '# Account: Lumora Software',
                               '# Property: lumora.io - GA4', f'# Start date: {y}{m:02d}01', f'# End date: {month_end(y, m):%Y%m%d}', '# ----------------------------------------'])


# ───────────────────────── writers: CRM & billing ─────────────────────────
def country_sloppy(ci, p=.3):
    n, _, _, _, var = COUNTRIES[ci]
    if random.random() < .03: return ''
    return random.choice(var) if random.random() < p else n


def size_bucket(seats):
    return '1-10' if seats < 6 else '11-50' if seats < 30 else '51-200' if seats < 120 else '201-1000' if seats < 600 else '1000+'


def crm_date(ts):  # contacts migrated from the old CRM before July 2024 keep US-style dates
    return ts.strftime('%m/%d/%Y %H:%M') if ts.date() < date(2024, 7, 1) else ts.strftime('%Y-%m-%d %H:%M')


def write_crm():
    rows = []
    for s in signups:
        c = s['cust']
        stage = ('Former customer' if c['churn'] else 'Customer') if c else ('Product Qualified Lead' if s['act'] and s['act_date'] <= END else 'Lead')
        src_label = {'Organic Search': 'Organic Search', 'Direct': 'Direct Traffic', 'Referral': 'Referrals', 'Partners': 'Offline Sources', 'Paid Search': 'Paid Search',
                     'Paid Social': 'Paid Social'}[s['ch']]
        rows.append([s['id'] + 100000, s['first'], s['last'], s['email'], s['company'], country_sloppy(s['ci']), s['industry'] if random.random() > .12 else '',
                     size_bucket(c['seats']) if c else '', crm_date(s['ts']), stage, src_label, s['src'], s['camp'] or (s['partner'] or ''),
                     c['start'].isoformat() if c else '', PLAN_LABEL[c['plan']] if c else '', c['seats'] if c else '', c['billing'] if c else '',
                     c['stripe'] if c else '', c['churn'].isoformat() if c and c['churn'] else '', 'Yes' if s['act'] and s['act_date'] <= END else 'No'])
    for _ in range(int(len(rows) * .012)):  # duplicates with different email casing
        r = list(random.choice(rows)); r[0] = random.randint(400000, 499999); r[3] = r[3].title(); rows.append(r)
    rows.sort(key=lambda r: r[0])
    w_csv(out('crm', 'hubspot_contacts_export_2026-10-01.csv'),
          ['Record ID', 'First Name', 'Last Name', 'Email', 'Company Name', 'Country/Region', 'Industry', 'Company size', 'Create Date', 'Lifecycle Stage',
           'Original Source', 'Original Source Drill-Down 1', 'Original Source Drill-Down 2', 'Became a Customer Date', 'Plan', 'Seats', 'Billing Period',
           'Stripe Customer ID', 'Churn Date', 'Activated (first board created)'], rows)
    comp = []
    for c in customers:
        mrr = mrr_at(c, END)
        comp.append([c['id'], c['company'], country_sloppy(c['ci'], .2), c['region'] if random.random() > .05 else '', c['industry'], PLAN_LABEL[c['plan']],
                     'Sales-led' if c['kind'] == 'ent' else 'Self-serve', c['start'].isoformat(), c['churn'].isoformat() if c['churn'] else '',
                     round(mrr * 12, 2), seats_at(c, END) or seats_at(c, c['churn'] - timedelta(1) if c['churn'] else END), c['deal']['rep'] if c['kind'] == 'ent' else '',
                     c['stripe'], c['contact'], c['email']])
    w_csv(out('crm', 'hubspot_companies_export_2026-10-01.csv'),
          ['Company ID', 'Company name', 'Country/Region', 'Region', 'Industry', 'Plan', 'Motion', 'Customer since', 'Churned on', 'ARR (USD)', 'Seats',
           'Account owner', 'Stripe customer ID', 'Primary contact', 'Primary contact email'], comp)


def write_deals():
    for y in (2024, 2025, 2026):
        wb = Workbook(); ws = wb.active; ws.title = 'Deals'
        hdr = ['Deal ID', 'Deal Name', 'Pipeline', 'Deal Stage', 'Amount', 'Create Date', 'Close Date', 'Deal owner', 'Region', 'Original Source',
               'Closed Lost Reason', 'Number of seats', 'Associated Company', 'Country', 'Industry', 'Primary contact']
        if y == 2024: hdr[4] = 'Amount (USD)'  # renamed the column in 2025
        ws.append(hdr)
        for c in ws[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='FF7A59')
        for dl in [d for d in deals if d['created'].year == y]:
            ws.append([dl['id'], f"{dl['company']} - Lumora Enterprise", 'Enterprise', dl['stage'], dl['amount'], dl['created'], dl['close'] if dl['stage'].startswith('Closed') else dl['close'],
                       dl['rep'], dl['region'], dl['source'], dl['lost'], dl['seats'], dl['company'], COUNTRIES[dl['ci']][0], dl['industry'], dl['contact']])
        wb.save(out('sales', f'hubspot_deals_export_created_{y}.xlsx'))


def stripe_desc(ch):
    return f"Lumora {PLAN_LABEL[ch['plan']]} — {ch['seats']} seat{'s' if ch['seats'] > 1 else ''} ({ch['billing']})"


def write_stripe():
    rows = []
    for c in customers:
        iso = COUNTRIES[c['ci']][1]
        for ch in c['charges']:
            rows.append((ch['ts'], c, ch, rid('ch_3', 24), iso))
    rows.sort(key=lambda r: r[0])
    by = defaultdict(list)
    for r in rows: by[(r[0].year, r[0].month)].append(r)
    for (y, m), rs in sorted(by.items()):
        if (y, m) in ((2025, 3), (2026, 2)):  # export date range overlapped the previous month by a few days
            pm = add_months(date(y, m, 1), -1)
            rs = [r for r in by[(pm.year, pm.month)] if r[0].day >= 26] + rs
        new = date(y, m, 1) >= date(2025, 7, 1)
        body = []
        for ts, c, ch, cid, iso in rs:
            amt, cur = ch['amt'], c['cur']
            usd = round(amt * fx(cur, ts.date()), 2)
            fee = round(usd * .029 + .30, 2) if ch['status'] != 'failed' else 0
            refunded = amt if ch['status'] == 'refunded' else 0
            if not new:
                body.append([cid, stripe_desc(ch), ts.strftime('%Y-%m-%d %H:%M:%S'), f'{amt:.2f}', f'{refunded:.2f}', cur.lower(), f'{usd:.2f}',
                             f'{(usd if refunded else 0):.2f}', f'{fee:.2f}', 'usd', {'paid': 'Paid', 'failed': 'Failed', 'refunded': 'Refunded'}[ch['status']],
                             c['stripe'], c['email'], iso if random.random() > .02 else '', ch['plan'], ch['seats'], ch['coupon']])
            else:
                minor = int(round(amt * (1 if cur == 'JPY' else 100)))
                body.append([cid, ts.strftime('%Y-%m-%dT%H:%M:%SZ'), minor, minor if refunded else 0, cur.lower(), f'{usd:.2f}', f'{fee:.2f}',
                             {'paid': 'succeeded', 'failed': 'failed', 'refunded': 'refunded'}[ch['status']], c['stripe'], c['email'], iso,
                             stripe_desc(ch), ch['plan'], ch['seats'], ch['coupon']])
        if not new:
            w_csv(out('billing', 'stripe', f'payments_{y}-{m:02d}.csv'),
                  ['id', 'Description', 'Created (UTC)', 'Amount', 'Amount Refunded', 'Currency', 'Converted Amount', 'Converted Amount Refunded', 'Fee',
                   'Converted Currency', 'Status', 'Customer ID', 'Customer Email', 'Card Issue Country', 'plan (metadata)', 'seats (metadata)', 'Coupon'], body)
        else:
            w_csv(out('billing', 'stripe', f'unified_payments_{y}-{m:02d}.csv'),
                  ['id', 'created', 'amount', 'amount_refunded', 'currency', 'converted_amount', 'fee', 'status', 'customer', 'customer_email', 'card_country',
                   'description', 'metadata[plan]', 'metadata[seats]', 'discount_coupon'], body)


# ───────────────────────── writers: PDFs ─────────────────────────
ENT_US = ['Lumora Software, Inc.', '535 Mission Street, 14th Floor', 'San Francisco, CA 94105, USA', 'Tax ID: 87-1234567']
ENT_EU = ['Lumora Software Europe B.V.', 'Keizersgracht 241', '1016 EA Amsterdam, The Netherlands', 'VAT: NL862345791B01 · KvK 81234567']
invoice_register = []


def pdf_lines(cv, x, y, lines, size=9, lead=12, font='Helvetica'):
    cv.setFont(font, size)
    for l in lines:
        cv.drawString(x, y, l); y -= lead
    return y


def write_invoices():
    seq = defaultdict(int)
    allinv = sorted([(inv['date'], c, inv) for c in customers for inv in c['invoices'] if inv['date'] >= START], key=lambda t: (t[0], t[1]['id']))
    for d, c, inv in allinv:
        eu = c['region'] == 'EMEA'
        seq[(eu, d.year)] += 1
        no = f'LSE-{d.year}-{seq[(eu, d.year)]:04d}' if eu else f'INV-{d.year}{seq[(eu, d.year)]:05d}'
        due = d + timedelta(days=c['terms'])
        iso = COUNTRIES[c['ci']][1]
        cur = c['cur']
        sub = round(sum(q * p for _, q, p in inv['lines']), 2)
        vat = round(sub * .21, 2) if iso == 'NL' else 0  # domestic NL charges VAT; other EU is reverse charge
        total = round(sub + vat, 2)
        late = rng.normal(4, 12) + (12 if c['region'] in ('APAC', 'LATAM') else 0)
        paid = due + timedelta(days=int(late))
        if paid > EXPORTED or random.random() < .015: paid = None
        invoice_register.append(dict(no=no, c=c, date=d, due=due, cur=cur, sub=sub, vat=vat, total=total, paid=paid, kind=inv['kind']))
        p = out('billing', 'invoices', str(d.year), f'{no}_{re.sub("[^A-Za-z0-9]+", "-", ascii_(c["company"]))[:40]}.pdf')
        cv = canvas.Canvas(p, pagesize=A4); W, H = A4
        cv.setTitle(f'Invoice {no}'); cv.setAuthor('Lumora Software')
        cv.setFillColorRGB(.36, .29, .85); cv.rect(0, H - 18, W, 18, fill=1, stroke=0); cv.setFillColorRGB(0, 0, 0)
        cv.setFont('Helvetica-Bold', 20); cv.drawString(40, H - 60, 'lumora')
        pdf_lines(cv, 40, H - 80, ENT_EU if eu else ENT_US, 8, 10)
        cv.setFont('Helvetica-Bold', 16); cv.drawRightString(W - 40, H - 60, 'INVOICE')
        pdf_lines(cv, W - 200, H - 80, [f'Invoice no.:  {no}', f'Issue date:   {d:%d %B %Y}', f'Due date:     {due:%d %B %Y}', f'Terms:        Net {c["terms"]}',
                                        f'Customer PO:  {c["po"] or "—"}', f'Currency:     {cur}'], 9, 12)
        cv.setFont('Helvetica-Bold', 10); cv.drawString(40, H - 175, 'Bill to')
        pdf_lines(cv, 40, H - 190, [c['company'], f'Attn: {c["contact"]} · {c["email"]}', city(iso), country_sloppy(c['ci'], .15) or COUNTRIES[c['ci']][0]], 9, 12)
        y = H - 260
        cv.setFillColorRGB(.95, .94, .99); cv.rect(40, y - 4, W - 80, 16, fill=1, stroke=0); cv.setFillColorRGB(0, 0, 0)
        cv.setFont('Helvetica-Bold', 9)
        cv.drawString(46, y, 'Description'); cv.drawRightString(W - 200, y, 'Qty'); cv.drawRightString(W - 120, y, 'Unit price'); cv.drawRightString(W - 46, y, 'Amount')
        cv.setFont('Helvetica', 8.5)
        for desc, q, up in inv['lines']:
            y -= 18
            cv.drawString(46, y, desc[:92]); cv.drawRightString(W - 200, y, f'{q:,}'); cv.drawRightString(W - 120, y, f'{up:,.2f}'); cv.drawRightString(W - 46, y, f'{q * up:,.2f}')
        y -= 30
        for lbl, v in [('Subtotal', sub), ('VAT 21%' if vat else 'VAT', vat), (f'Total due ({cur})', total)]:
            cv.setFont('Helvetica-Bold' if lbl.startswith('Total') else 'Helvetica', 10)
            cv.drawRightString(W - 120, y, lbl); cv.drawRightString(W - 46, y, f'{v:,.2f}'); y -= 16
        notes = []
        if eu and iso in EU_VAT and iso != 'NL': notes.append('VAT reverse charge — Article 196, Council Directive 2006/112/EC.')
        if not eu and iso == 'US': notes.append('Sales tax not applicable — exemption certificate on file.')
        notes += ['', 'Payment by bank transfer to:',
                  'ING Bank N.V. · IBAN NL91 INGB 0006 1234 56 · BIC INGBNL2A' if eu else 'Silicon Valley Bank · ACH 121140399 · Acct 3301234567 · SWIFT SVBKUS6S',
                  f'Please quote invoice number {no} as payment reference.']
        pdf_lines(cv, 40, y - 20, notes, 8.5, 12)
        cv.setFont('Helvetica', 7); cv.drawString(40, 30, 'Lumora Software · lumora.io · billing@lumora.io'); cv.drawRightString(W - 40, 30, 'Page 1 of 1')
        cv.save()


def write_order_forms():
    for dl in deals:
        c = dl.get('cust')
        if not c: continue
        p = out('sales', 'order_forms', f'OrderForm_{dl["close"]:%Y%m%d}_{re.sub("[^A-Za-z0-9]+", "-", ascii_(dl["company"]))[:40]}.pdf')
        cv = canvas.Canvas(p, pagesize=A4); W, H = A4
        cv.setFont('Helvetica-Bold', 18); cv.drawString(40, H - 60, 'Lumora Enterprise — Order Form')
        cur = c['cur']
        unit = dl['price'] if cur == 'USD' else round(dl['price'] * LOCAL[cur], 2)
        acv = dl['seats'] * (unit + ((6 if cur == 'USD' else round(6 * LOCAL[cur], 2)) if dl['addon'] else 0)) * 12
        y = pdf_lines(cv, 40, H - 95, [
            f'Order Form No.: OF-{dl["close"].year}-{int(dl["id"]) % 10000:04d}          Effective date: {c["start"]:%B %d, %Y}',
            '', f'Customer: {dl["company"]}', f'Address: {city(COUNTRIES[dl["ci"]][1])}, {COUNTRIES[dl["ci"]][0]}', f'Customer contact: {dl["contact"]} <{dl["email"]}>',
            '', f'Provider: {(ENT_EU if dl["region"] == "EMEA" else ENT_US)[0]}', f'Account Executive: {dl["rep"]}', '',
            'SUBSCRIPTION', f'  Product: Lumora Enterprise (SSO, audit log, dedicated CSM, 99.9% SLA)', f'  Seats: {dl["seats"]}',
            f'  Price: {cur} {unit:,.2f} per seat per month', f'  Lumora Insights add-on: {"Included at " + cur + " " + str(6 if cur == "USD" else round(6 * LOCAL[cur], 2)) + " per seat per month" if dl["addon"] else "Not included"}',
            f'  Subscription term: 12 months from the Effective date, renewing automatically for successive 12-month terms',
            f'  Annual contract value: {cur} {acv:,.2f}', f'  Billing frequency: {"Annually in advance" if c["billing"] == "annual" else "Quarterly in advance"}',
            f'  Payment terms: Net {c["terms"]} days', '', 'TERMS',
            '  This Order Form is governed by the Lumora Master Subscription Agreement available at lumora.io/legal/msa.',
            '  Price increases on renewal are capped at 5% per year. Additional seats are co-termed and prorated.', '', '',
            'Signed for the Customer:                                  Signed for Lumora:', f'{dl["contact"]:<58}{dl["rep"]}',
            f'Date: {dl["close"]:%Y-%m-%d}                                         Date: {dl["close"]:%Y-%m-%d}'], 10, 15)
        cv.save()


def write_ar():
    wb = Workbook(); ws = wb.active; ws.title = 'Receipts'
    ws.append(['Lumora Software — cash receipts on invoiced customers (bank reconciliation)']); ws.append([f'Exported {EXPORTED:%d.%m.%Y}']); ws.append([])
    ws.append(['Invoice', 'Customer', 'Invoice date', 'Due date', 'Currency', 'Invoice total', 'Received on', 'Amount received', 'Bank'])
    for r in sorted(invoice_register, key=lambda r: r['date']):
        if r['paid']:
            ws.append([r['no'], r['c']['company'], r['date'], r['due'], r['cur'], r['total'], r['paid'], r['total'] if random.random() > .02 else round(r['total'] - 25, 2),
                       'ING NL' if r['no'].startswith('LSE') else 'SVB'])
    ws2 = wb.create_sheet('Open items')
    ws2.append(['Invoice', 'Customer', 'Invoice date', 'Due date', 'Currency', 'Open amount', 'Days overdue'])
    for r in invoice_register:
        if not r['paid']: ws2.append([r['no'], r['c']['company'], r['date'], r['due'], r['cur'], r['total'], max(0, (EXPORTED - r['due']).days)])
    wb.save(out('finance', 'AR_receipts_and_open_items_2026-09.xlsx'))


# ───────────────────────── writers: product & support ─────────────────────────
HOUR_CURVE = [.02, .01, .01, .01, .01, .02, .05, .12, .35, .70, .95, 1.0, .80, .85, .95, .90, .75, .55, .30, .18, .12, .08, .05, .03]
WEEK = [.95, 1.05, 1.05, 1.0, .85, .12, .10]


def write_usage(M):
    for y, m in MONTHS:
        row = M[(y, m)]
        lines = []
        for day in range(1, calendar.monthrange(y, m)[1] + 1):
            d = date(y, m, day)
            for h in range(24):
                for r in REGIONS:
                    lt = datetime(y, m, day, h) + timedelta(hours=UTC_OFF[r])
                    f = HOUR_CURVE[lt.hour] * WEEK[lt.weekday()] * (1.04 if d.month in (3, 10) else 1)
                    if d == OUTAGE and 13 <= h <= 18: f *= .04
                    if d == OUTAGE + timedelta(1): f *= .9
                    if d == date(2026, 2, 3) and h == 15: f *= .3
                    au = pois(row['seats'][r] * .22 * f)
                    rep = pois(row['addon_seats'][r] * .05 * f) if d >= INSIGHTS_LAUNCH else 0
                    lines.append(json.dumps({'hour': f'{d}T{h:02d}:00:00Z', 'region': r, 'active_users': au, 'sessions': pois(au * 1.4),
                                             'boards_created': pois(au * .03), 'tasks_completed': pois(au * 2.1), 'api_calls': pois(au * 38),
                                             'reports_generated': rep}, separators=(',', ':')))
        with open(out('product', 'usage', f'usage_hourly_{y}-{m:02d}.jsonl'), 'w') as f: f.write('\n'.join(lines) + '\n')


SUBJECTS = {
    'Billing': ['Invoice copy needed', 'Charged twice this month?', 'Update billing address / VAT number', 'Card declined', 'Why did our price go up?',
                'Refund request', 'Switch to annual billing', 'Receipt in EUR instead of USD'],
    'Technical Support': ['Boards not loading', 'Slack integration stopped syncing', 'Export to CSV fails', 'API rate limit 429 errors', 'SSO login loop',
                          'Notifications not arriving', 'Gantt view very slow with 2k tasks', 'Mobile app crashes on Android'],
    'Onboarding': ['How do I import from Trello?', 'Need help setting up workspaces', 'Training session for our team', 'Best practices for templates'],
    'Account Management': ['Add 10 more seats', 'Downgrade to Starter', 'Cancel subscription', 'Transfer ownership of workspace', 'Request for DPA / security docs'],
}


def write_zendesk(M):
    active_by_m = {}
    for y, m in MONTHS:
        t = date(y, m, 15)
        lst = [c for c in customers if active(c, t)]
        active_by_m[(y, m)] = (lst, np.array([math.sqrt(max(1, seats_at(c, t) or c['seats'])) for c in lst]))
    tid = 48210
    by_q = defaultdict(list)
    for d in DAYS:
        lst, w = active_by_m[(d.year, d.month)]
        if not lst: continue
        lam = len(lst) * .011 * (.35 if d.weekday() >= 5 else 1)
        extra = {OUTAGE: 230, OUTAGE + timedelta(1): 140, OUTAGE + timedelta(2): 45}.get(d, 0)
        billing_wave = date(2026, 1, 5) <= d <= date(2026, 2, 28)
        if billing_wave: lam *= 1.35
        p = w / w.sum()
        n_normal = pois(lam)
        for k in range(n_normal + extra):
            c = lst[int(rng.choice(len(lst), p=p))]
            incident = k >= n_normal
            if incident:
                grp, subj, tags = 'Technical Support', random.choice(['Lumora is down?', 'Cannot access boards — 502 error', 'Outage right now?', 'Data missing after outage']), 'incident_20250612 outage'
            elif billing_wave and random.random() < .3:
                grp, subj, tags = 'Billing', random.choice(['Why did our price go up?', 'Price increase not communicated', 'New price for Team plan']), 'billing price_increase_2026'
            else:
                grp = random.choices(list(SUBJECTS), [28, 45, 12, 15])[0]
                subj = random.choice(SUBJECTS[grp])
                tags = grp.lower().replace(' ', '_')
            if c['kind'] == 'ent': tags += ' enterprise'
            ts = datetime(d.year, d.month, d.day, int((rng.normal(13, 3) - UTC_OFF[c['region']]) % 24), random.randint(0, 59), random.randint(0, 59))
            prio = random.choices(['Low', 'Normal', 'High', 'Urgent'], [20, 55, 20, 5] if not incident else [0, 10, 40, 50])[0]
            fr = rng.lognormal(math.log({'Urgent': 25, 'High': 70, 'Normal': 140, 'Low': 300}[prio]), .7) * (6 if incident else 1) * (.7 if c['kind'] == 'ent' else 1)
            res = fr + rng.lognormal(math.log(600), 1.0) * (1.6 if grp == 'Technical Support' else 1)
            solved = ts + timedelta(minutes=res)
            status = 'Closed' if solved.date() < EXPORTED - timedelta(4) else ('Solved' if solved.date() <= EXPORTED else random.choice(['Open', 'Pending']))
            pgood = .5 if incident else .68 if 'price_increase' in tags else .9 if fr < 240 else .78
            if status in ('Open', 'Pending'): sat = 'Unoffered'
            elif random.random() < .6: sat = ('Good' if random.random() < pgood else 'Bad') if random.random() < .38 else 'Offered'
            else: sat = 'Unoffered'
            ch = random.choices(['Email', 'Web form', 'Chat', 'API'], [45, 30, 22 if d >= date(2025, 1, 15) else 0, 3])[0]
            by_q[(d.year, (d.month - 1) // 3 + 1)].append([tid, subj, c['contact'], c['email'], c['company'], grp, prio, status, ch, ts.strftime('%Y-%m-%d %H:%M:%S'),
                                                           solved.strftime('%Y-%m-%d %H:%M:%S') if status in ('Closed', 'Solved') else '', round(fr),
                                                           round(res) if status in ('Closed', 'Solved') else '', sat, tags, PLAN_LABEL[c['plan']]])
            tid += 1
    for (y, q), rows in sorted(by_q.items()):
        w_csv(out('support', 'zendesk', f'zendesk_tickets_{y}-Q{q}.csv'),
              ['Id', 'Subject', 'Requester', 'Requester email', 'Organization', 'Group', 'Priority', 'Status', 'Via', 'Created at', 'Solved at',
               'First reply time in minutes', 'Full resolution time in minutes', 'Satisfaction Score', 'Tags', 'Plan [custom]'], rows)


NPS_TXT = {
    'pro': ['Love the boards, the whole team lives in Lumora now.', 'Insights reports save me hours every Monday.', 'Super easy to onboard new people.',
            'Best project tool we have tried, and we tried many.', 'Support is fast and friendly.', 'The templates are great and the Slack integration just works.',
            'Clean UI, fast, does exactly what we need.', 'Our clients love the shared boards.'],
    'pas': ['Good tool, but the Jira integration could be better.', 'Does the job. Reporting is a bit basic.', 'Fine for us, mobile app needs work.',
            'Solid, but gets slow with very large boards.', 'Would like more automation rules.', 'OK value for money.'],
    'det': ['Too slow with large boards.', 'Support took days to answer.', 'Missing Gantt dependencies we need.', 'Too expensive for a small team.',
            'Integrations keep breaking.', 'Hard to find things, navigation is confusing.'],
    'outage': ['The outage in June cost us a full afternoon of work.', 'After the June downtime our management lost trust in the tool.'],
    'price': ['Price went up almost 20% and we got nothing new.', 'The Team plan price increase was badly communicated.', 'Looking at alternatives after the price increase.'],
}
NPS_LOCAL = {'DE': ['Sehr gutes Tool, aber zu teuer geworden.', 'Funktioniert zuverlässig, Support ist top.', 'Die Preiserhöhung war nicht ok.'],
             'BR': ['Ferramenta excelente, a equipe toda usa.', 'Ficou caro depois do aumento de preço.', 'Integrações poderiam ser melhores.'],
             'MX': ['Muy buena herramienta, fácil de usar.', 'El precio subió demasiado.', 'Soporte lento en español.'],
             'ES': ['Muy buena herramienta, fácil de usar.', 'El precio subió demasiado.'],
             'JP': ['とても使いやすいです。', '大きなボードだと動作が遅いです。', '日本語サポートがもっと欲しい。'],
             'FR': ['Très bon outil, simple à prendre en main.', "Trop cher depuis l'augmentation."]}


def write_nps():
    rid_ = 1
    for y, q in QUARTERS:
        t = date(y, q * 3 - 1, 10)
        if t > END: continue
        wb = Workbook(); ws = wb.active; ws.title = 'Responses'
        ws.append(['#', 'How likely are you to recommend Lumora to a friend or colleague?', "What's the main reason for your score?", 'Which plan are you on?',
                   'email', 'Start Date (UTC)', 'Submit Date (UTC)', 'Network ID'])
        for c in [c for c in customers if active(c, t)]:
            if random.random() > (.06 if c['kind'] == 'self' else .25): continue
            mu = 7.5 + (.6 if c['kind'] == 'ent' else 0) - (1.0 if c['promo'] else 0) + (.4 if c['addon'] else 0) - (.3 if c['plan'] == 'starter' else 0)
            ctx = None
            if (y, q) == (2025, 3) and random.random() < .35: mu -= 2.2; ctx = 'outage'
            if y == 2026 and q <= 2 and c['plan'] == 'team' and random.random() < .5: mu -= 2.6; ctx = 'price'
            sc = int(clamp(round(rng.normal(mu, 2.0)), 0, 10))
            iso = COUNTRIES[c['ci']][1]
            if random.random() < .25: txt = ''
            elif ctx and sc <= 7: txt = random.choice(NPS_TXT[ctx])
            elif iso in NPS_LOCAL and random.random() < .4: txt = random.choice(NPS_LOCAL[iso])
            else: txt = random.choice(NPS_TXT['pro' if sc >= 9 else 'pas' if sc >= 7 else 'det'])
            st = datetime(t.year, t.month, t.day) + timedelta(days=random.randint(0, 20), minutes=random.randint(0, 1439))
            ws.append([rid_, sc, txt, PLAN_LABEL[c['plan']] if random.random() > .1 else "I'm not sure", c['email'], st.strftime('%Y-%m-%d %H:%M:%S'),
                       (st + timedelta(seconds=random.randint(25, 400))).strftime('%Y-%m-%d %H:%M:%S'), rid('', 10).lower()])
            rid_ += 1
        wb.save(out('support', 'nps', f'NPS_survey_{y}_Q{q}.xlsx'))


def write_partners():
    rows_q = defaultdict(list)
    for c in customers:
        if not c['partner']: continue
        for ch in c['charges']:
            d = ch['ts'].date()
            if ch['status'] == 'paid' and d < c['start'] + timedelta(365):
                usd = ch['amt'] * fx(c['cur'], d)
                rows_q[(d.year, (d.month - 1) // 3 + 1)].append([c['partner'], c['company'], c['stripe'], c['start'].isoformat(), d.isoformat(), f'{usd:.2f}', '20%', f'{usd * .2:.2f}'])
    for (y, q), rows in sorted(rows_q.items()):
        w_csv(out('partners', f'partner_commissions_{y}Q{q}.csv'),
              ['Partner', 'Customer', 'Stripe customer', 'Customer since', 'Payment date', 'Payment (USD)', 'Commission rate', 'Commission (USD)'], sorted(rows))
    return rows_q


# ───────────────────────── finance ─────────────────────────
HC0 = {'Engineering': 24, 'Product': 6, 'Sales': 10, 'Marketing': 6, 'Customer Success': 8, 'G&A': 6}
HC1 = {'Engineering': 58, 'Product': 13, 'Sales': 31, 'Marketing': 15, 'Customer Success': 25, 'G&A': 15}
SAL = {'Engineering': 12600, 'Product': 13000, 'Sales': 10800, 'Marketing': 9900, 'Customer Success': 6900, 'G&A': 9200}
TOOLS = [('Slack Technologies', 'Slack Business+', 15), ('Atlassian', 'Jira & Confluence', 14), ('HubSpot Inc.', 'HubSpot Sales/Marketing Hub', 0), ('Zendesk Inc.', 'Zendesk Suite', 0),
         ('Figma Inc.', 'Figma Organization', 9), ('Google Ireland Ltd', 'Google Workspace', 18), ('GitHub Inc.', 'GitHub Enterprise', 21), ('Datadog Inc.', 'Datadog', 0)]
EVENTS = {(2024, 3): ('SaaS Connect Berlin — booth', 38000), (2024, 6): ('B2B Growth Summit London', 22000), (2024, 11): ('Web Builders Lisbon — sponsorship', 61000),
          (2025, 3): ('SaaS Connect Berlin — booth', 42000), (2025, 5): ('APAC SaaS Week Singapore', 35000), (2025, 9): ('ProductCon NYC — sponsorship', 54000),
          (2025, 11): ('Web Builders Lisbon — sponsorship', 66000), (2026, 3): ('SaaS Connect Berlin — booth', 45000), (2026, 5): ('APAC SaaS Week Tokyo', 48000)}


def headcount(y, m):
    t = ((y - 2024) * 12 + m - 1) / (len(MONTHS) - 1)
    hc = {}
    for k in HC0:
        tt = t ** 1.1
        if k == 'Sales' and (y, m) >= (2025, 2): tt = min(1, tt + .2)  # sales hiring push
        hc[k] = int(round(HC0[k] + (HC1[k] - HC0[k]) * tt))
    return hc


def build_finance(M, partner_rows):
    F = {}
    spend = defaultdict(float)
    for r in ad_rows: spend[(r['d'].year, r['d'].month, r['c']['platform'])] += r['spend']
    stripe = defaultdict(lambda: [0., 0., 0.])
    for c in customers:
        for ch in c['charges']:
            if ch['status'] == 'failed': continue
            k = (ch['ts'].year, ch['ts'].month)
            usd = ch['amt'] * fx(c['cur'], ch['ts'].date())
            stripe[k][0] += usd; stripe[k][1] += usd * .029 + .3
            if ch['status'] == 'refunded': stripe[k][2] += usd
    inv = defaultdict(lambda: [0., 0.])
    for r in invoice_register:
        inv[(r['date'].year, r['date'].month)][0 if r['kind'] == 'subscription' else 1] += r['sub'] * fx(r['cur'], r['date'])
    services_rev = {k: v[1] for k, v in inv.items()}
    comm = defaultdict(float)
    for (y, q), rows in partner_rows.items(): comm[(y, q)] = sum(float(r[7]) for r in rows)
    for y, m in MONTHS:
        mi = (y - 2024) * 12 + m - 1
        hc = headcount(y, m)
        infl = 1.03 ** (y - 2024)
        row = M[(y, m)]
        seats = sum(row['seats'].values())
        new_ent_acv = sum(dl['amount'] for dl in deals if dl['stage'] == 'Closed won' and (dl['close'].year, dl['close'].month) == (y, m))
        f = dict(hc=hc, rev_self=row['mrr_self'], rev_ent=row['mrr_ent'], rev_services=services_rev.get((y, m), 0.),
                 aws=21000 + 1.15 * seats * rng.lognormal(0, .04) + (9000 if (y, m) == (2025, 6) else 0), tools3p=4200 + .25 * seats,
                 support_cogs=hc['Customer Success'] * SAL['Customer Success'] * infl * .5,
                 ads={p: spend[(y, m, p)] for p in ('google', 'meta', 'linkedin')}, sal={k: hc[k] * SAL[k] * infl for k in hc},
                 commission=new_ent_acv * .10, events=EVENTS.get((y, m), (None, 0))[1], partner_comm=comm.get((y, (m - 1) // 3 + 1), 0) / 3,
                 rent=38000 + 16000 * 1.08 + (12000 if y >= 2025 else 0), legal=rng.uniform(3000, 12000) + (45000 if m == 3 else 0),
                 recruiting=max(0, sum(hc.values()) - sum(headcount(*(add_months(date(y, m, 1), -1).timetuple()[:2])).values()) if mi else 0) * 6500,
                 tools=sum(hc.values()) * 95 + 5200 + 0.02 * seats, travel=sum(hc.values()) * rng.uniform(120, 260),
                 stripe=stripe[(y, m)], invoiced=inv[(y, m)][0], new_ent_acv=new_ent_acv)
        f['sm'] = sum(f['ads'].values()) + f['sal']['Sales'] + f['sal']['Marketing'] + f['commission'] + f['events'] + f['partner_comm']
        f['rnd'] = f['sal']['Engineering'] + f['sal']['Product'] + f['tools'] * .6
        f['ga'] = f['sal']['G&A'] + f['rent'] + f['legal'] + f['recruiting'] + f['travel'] + f['tools'] * .4 + f['stripe'][1]
        f['revenue'] = f['rev_self'] + f['rev_ent'] + f['rev_services']
        f['cogs'] = f['aws'] + f['tools3p'] + f['support_cogs']
        f['sal']['Customer Success'] *= .5  # other half sits in COGS
        f['ebitda'] = f['revenue'] - f['cogs'] - f['sm'] - f['rnd'] - f['ga'] - f['sal']['Customer Success']
        F[(y, m)] = f
    return F


def eu_num(v): return f'{v:,.2f}'.replace(',', ' ').replace('.', ',').replace(' ', '.')


def write_gl(F):
    for (y, m), f in F.items():
        rows, j = [], 1
        last = month_end(y, m)

        def add(day, acct, name, cc, party, desc, debit=0., credit=0.):
            nonlocal j
            rows.append([f'{min(day, last.day):02d}/{m:02d}/{y}', f'JE-{y}{m:02d}-{j:04d}', acct, name, cc, party, desc, eu_num(debit) if debit else '', eu_num(credit) if credit else '', 'USD'])
            j += 1
        add(last.day, '4000', 'Subscription revenue - card (Stripe)', 'REV', 'Stripe Payments Europe Ltd', f'Stripe gross charges {MNAME[m]} {y}', credit=f['stripe'][0])
        if f['stripe'][2]: add(last.day, '4090', 'Refunds', 'REV', 'Stripe Payments Europe Ltd', 'Refunds issued', debit=f['stripe'][2])
        for r in [r for r in invoice_register if (r['date'].year, r['date'].month) == (y, m)]:
            add(r['date'].day, '4010' if r['kind'] == 'subscription' else '4100', 'Subscription revenue - invoiced' if r['kind'] == 'subscription' else 'Professional services',
                'REV', r['c']['company'], f"Invoice {r['no']} ({r['cur']} {r['total']:,.2f})", credit=r['sub'] * fx(r['cur'], r['date']))
        for dept, v in f['sal'].items():
            add(25, '6000', 'Salaries & wages', dept, 'Payroll (Deel / Gusto)', f'Payroll {MNAME[m]} {y} — {f["hc"][dept]} FTE', debit=v * (2 if dept == 'Customer Success' else 1) * .82)
            add(25, '6010', 'Employer taxes & benefits', dept, 'Payroll (Deel / Gusto)', f'Employer contributions {MNAME[m]}', debit=v * (2 if dept == 'Customer Success' else 1) * .18)
        if f['commission']: add(last.day, '6020', 'Sales commissions', 'Sales', 'Payroll (Deel / Gusto)', 'Commission on closed-won enterprise ACV', debit=f['commission'])
        add(3, '5000', 'Hosting - AWS', 'COGS', 'Amazon Web Services EMEA SARL', f'AWS invoice {MNAME[m]} {y}', debit=f['aws'])
        add(5, '5010', 'Third-party software (COGS)', 'COGS', 'Twilio / SendGrid / Algolia', 'Usage-based vendors', debit=f['tools3p'])
        add(last.day, '6100', 'Payment processing fees', 'G&A', 'Stripe Payments Europe Ltd', 'Stripe fees', debit=f['stripe'][1])
        g = f['ads']['google']
        if g: add(2, '6200', 'Advertising - search', 'Marketing', 'Google Ireland Ltd', f'Google Ads {MNAME[m]} {y}', debit=g)
        mt, k = f['ads']['meta'], 0
        while mt > 1:  # Meta bills every time the threshold is hit
            part = min(mt, 6000 if k else rng.uniform(2000, 6000)); mt -= part; k += 1
            add(random.randint(1, last.day), '6201', 'Advertising - social', 'Marketing', 'Meta Platforms Ireland Ltd', f'Facebook Ads threshold billing #{k}', debit=part)
        if f['ads']['linkedin']: add(last.day, '6201', 'Advertising - social', 'Marketing', 'LinkedIn Ireland Unlimited Co.', f'Campaign Manager {MNAME[m]} {y}', debit=f['ads']['linkedin'])
        if f['events']: add(15, '6210', 'Events & sponsorships', 'Marketing', 'Event organiser', EVENTS[(y, m)][0], debit=f['events'])
        if f['partner_comm']: add(last.day, '6220', 'Partner commissions', 'Sales', 'Partner payouts', 'Partner referral commissions (accrual)', debit=f['partner_comm'])
        for vendor, desc, per_head in TOOLS:
            add(random.randint(1, 10), '6300', 'Software subscriptions', 'G&A', vendor, desc, debit=per_head * sum(f['hc'].values()) if per_head else rng.uniform(1800, 5200))
        add(1, '6400', 'Rent', 'G&A', 'Mission Street Properties LLC', 'Office rent San Francisco', debit=38000)
        add(1, '6400', 'Rent', 'G&A', 'Cluj Business Campus SRL', 'Office rent Cluj-Napoca (EUR 16,000)', debit=16000 * fx('EUR', date(y, m, 1)))
        if y >= 2025: add(1, '6400', 'Rent', 'G&A', 'Spaces Amsterdam Zuidas', 'Office rent Amsterdam', debit=12000)
        add(random.randint(5, 25), '6500', 'Legal & audit', 'G&A', random.choice(['Cooley LLP', 'Baker McKenzie', 'NautaDutilh']), 'Legal fees', debit=f['legal'] - (45000 if m == 3 else 0))
        if m == 3: add(28, '6500', 'Legal & audit', 'G&A', 'Deloitte Accountants B.V.', f'Statutory audit FY{y - 1}', debit=45000)
        if f['recruiting']: add(20, '6600', 'Recruiting', 'G&A', random.choice(['Hays plc', 'Michael Page', 'Workable']), 'Placement fees', debit=f['recruiting'])
        for _ in range(random.randint(25, 60)):  # employee expenses
            add(random.randint(1, last.day), '6700', 'Travel & meals', random.choice(list(HC0)), random.choice(['Uber', 'Booking.com', 'Lufthansa', 'Delta Air Lines', 'Airbnb', 'Restaurant', 'WeWork']),
                'Employee expense claim', debit=rng.lognormal(math.log(f['travel'] / 40), .8))
        w_csv(out('finance', 'general_ledger', f'GL_export_{y}-{m:02d}.csv'),
              ['Date', 'Journal', 'Account', 'Account name', 'Cost center', 'Counterparty', 'Description', 'Debit', 'Credit', 'Currency'], rows, delim=';', encoding='utf-8-sig')


def k(v): return round(v / 1000, 1)


def build_budget(M, F):
    """Plans made at the start of each year: last December grown at an assumed monthly rate."""
    B = {}
    for y, rate, uplift in ((2024, 1.045, 0), (2025, 1.040, 0), (2026, 1.035, .06)):
        if y == 2024: base_row, base_f, share = M[(2024, 1)], F[(2024, 1)], None
        else: base_row, base_f = M[(y - 1, 12)], F[(y - 1, 12)]
        last_year = [(yy, mm) for yy, mm in MONTHS if yy == y - 1] or [(2024, 1), (2024, 2), (2024, 3)]
        reg_share = {r: sum(M[k_]['mrr_region'][r] for k_ in last_year) for r in REGIONS}
        tot = sum(reg_share.values()); reg_share = {r: v / tot for r, v in reg_share.items()}
        new_avg = sum(M[k_]['new'] for k_ in last_year[-6:]) / len(last_year[-6:])
        ads_avg = {p: sum(F[k_]['ads'][p] for k_ in last_year) / len(last_year) for p in ('google', 'meta', 'linkedin')}
        for m in range(1, 13):
            g = rate ** (m if y > 2024 else m - 1)
            self_ = base_f['rev_self'] * g * (1 + uplift)
            ent = base_f['rev_ent'] * g
            B[(y, m)] = dict(rev_self=self_, rev_ent=ent, rev_services=sum(F[k_]['rev_services'] for k_ in last_year) / len(last_year) * 1.15,
                             new=new_avg * rate ** m, mrr_region={r: (self_ + ent) * reg_share[r] for r in REGIONS},
                             new_by_region={r: new_avg * rate ** m * reg_share[r] for r in REGIONS},
                             ads={'google': ads_avg['google'] * 1.15, 'meta': ads_avg['meta'] * (1.5 if y == 2026 else 1.1), 'linkedin': ads_avg['linkedin'] * 1.2},
                             hc=headcount(y, m) if y < 2026 else {kk: v + (2 if kk == 'Engineering' else 1) for kk, v in headcount(y, m).items()})
            B[(y, m)]['revenue'] = self_ + ent + B[(y, m)]['rev_services']
    return B


def write_budgets(B):
    hdr_fill = PatternFill('solid', fgColor='1F3864')
    for y in (2024, 2025, 2026):
        wb = Workbook(); ws = wb.active; ws.title = 'Revenue plan'
        ws.append([f'Lumora Software — Budget FY{y} (approved by the board {date(y - 1, 12, 12):%d %b %Y})']); ws.append(['USD']); ws.append([])
        ws.append(['Line'] + [MNAME[m][:3] + f'-{y % 100}' for m in range(1, 13)] + [f'FY{y}'])
        for c in ws[4]: c.font = Font(bold=True, color='FFFFFF'); c.fill = hdr_fill
        for lbl, key in [('Subscription revenue — self-serve', 'rev_self'), ('Subscription revenue — enterprise', 'rev_ent'), ('Professional services', 'rev_services'), ('Total revenue', 'revenue')]:
            vals = [round(B[(y, m)][key]) for m in range(1, 13)]; ws.append([lbl] + vals + [sum(vals)])
        ws2 = wb.create_sheet('Targets by region')
        ws2.append(['Region', 'Metric'] + [f'{y}-{m:02d}' for m in range(1, 13)])
        for r in REGIONS:
            ws2.append([r, 'MRR end of month (USD)'] + [round(B[(y, m)]['mrr_region'][r]) for m in range(1, 13)])
            ws2.append([r, 'New paying customers'] + [round(B[(y, m)]['new_by_region'][r]) for m in range(1, 13)])
        ws3 = wb.create_sheet('Marketing budget')
        ws3.append(['Channel'] + [MNAME[m][:3] for m in range(1, 13)])
        for p, lbl in (('google', 'Google Ads'), ('meta', 'Meta (Facebook/Instagram)'), ('linkedin', 'LinkedIn Ads')):
            ws3.append([lbl] + [round(B[(y, m)]['ads'][p] * SEASON[m] / 1000) * 1000 for m in range(1, 13)])
        ws4 = wb.create_sheet('Headcount plan')
        ws4.append(['Department'] + [MNAME[m][:3] for m in range(1, 13)])
        for d_ in HC0: ws4.append([d_] + [B[(y, m)]['hc'][d_] for m in range(1, 13)])
        for wsx in wb.worksheets: wsx.column_dimensions['A'].width = 36
        wb.save(out('finance', 'budget', f'Budget_FY{y}_final.xlsx'))


def write_mgmt_accounts(M, F, B):
    for (y, m), f in F.items():
        b = B.get((y, m))
        wb = Workbook(); ws = wb.active; ws.title = 'P&L'
        ws.append(['Lumora Software — Management Accounts']); ws['A1'].font = Font(bold=True, size=14)
        ws.append([f'Period: {MNAME[m]} {y}']); ws.append(["All figures in USD '000 unless stated"]); ws.append([])
        ws.append(['', 'Actual', 'Budget', 'Variance', 'Var %'])
        for c in ws[5]: c.font = Font(bold=True)

        def line(lbl, a, bud=None, bold=False):
            bv = k(bud) if bud is not None else None
            ws.append([lbl, k(a), bv if b else 'n/a', round(k(a) - bv, 1) if b and bv is not None else '', f'{(a / bud - 1) * 100:.1f}%' if b and bud else ''])
            if bold:
                for c in ws[ws.max_row]: c.font = Font(bold=True)
        line('Subscription revenue — self-serve', f['rev_self'], b and b['rev_self'])
        line('Subscription revenue — enterprise', f['rev_ent'], b and b['rev_ent'])
        line('Professional services', f['rev_services'], b and b['rev_services'])
        line('Total revenue', f['revenue'], b and b['revenue'], True)
        ws.append([])
        line('Hosting (AWS)', f['aws']); line('Third-party software', f['tools3p']); line('Customer support (50% of CS team)', f['support_cogs'])
        line('Cost of revenue', f['cogs'], None, True)
        line('Gross profit', f['revenue'] - f['cogs'], None, True)
        ws.append([f'Gross margin', f"{(1 - f['cogs'] / f['revenue']) * 100:.1f}%" if f['revenue'] else ''])
        ws.append([])
        line('Paid media', sum(f['ads'].values()), b and sum(b['ads'].values()))
        line('Sales & marketing salaries', f['sal']['Sales'] + f['sal']['Marketing'])
        line('Sales commissions', f['commission']); line('Events', f['events']); line('Partner commissions', f['partner_comm'])
        line('Sales & marketing', f['sm'], None, True)
        line('Research & development', f['rnd'], None, True)
        line('Customer success (other 50%)', f['sal']['Customer Success'], None, True)
        line('General & administrative', f['ga'], None, True)
        ws.append([])
        line('EBITDA', f['ebitda'], None, True)
        ws.column_dimensions['A'].width = 42
        row = M[(y, m)]
        ws2 = wb.create_sheet('KPIs')
        mrr = row['mrr_self'] + row['mrr_ent']
        for kk, v in [('MRR (USD)', round(mrr)), ('ARR (USD)', round(mrr * 12)), ('Paying customers', row['customers']), ('  of which enterprise', row['ent_customers']),
                      ('New paying customers', row['new']), ('Churned customers', row['churned']), ('Headcount (FTE)', sum(f['hc'].values())),
                      ('New enterprise ACV booked (USD)', round(f['new_ent_acv'])), ('Paid media spend (USD)', round(sum(f['ads'].values())))]:
            ws2.append([kk, v])
        ws2.column_dimensions['A'].width = 34
        wb.save(out('finance', 'management_accounts', f'MA_{y}-{m:02d}_{MNAME[m][:3]}.xlsx'))


def write_quotas():
    won = defaultdict(float)
    for dl in deals:
        if dl['stage'] == 'Closed won': won[(dl['close'].year, dl['region'])] += dl['amount']
    for y in (2024, 2025, 2026):
        wb = Workbook(); ws = wb.active; ws.title = 'Quotas'
        ws.append([f'Enterprise AE quotas FY{y} — new ACV (USD)']); ws.append([])
        ws.append(['Rep', 'Region', 'Q1', 'Q2', 'Q3', 'Q4', 'FY'])
        for r in REGIONS:
            base = (won[(2024, r)] * .8 if y == 2024 else won[(y - 1, r)] * 1.35) / 4
            for rep, reg, s, e in REPS:
                if reg != r: continue
                qs = []
                for q in range(1, 5):
                    qs_d, qe_d = date(y, 3 * q - 2, 1), month_end(y, 3 * q)
                    n_active = len([x for x in REPS if x[1] == r and x[2] <= qe_d and (x[3] is None or x[3] >= qs_d)])
                    on = s <= qe_d and (e is None or e >= qs_d)
                    qs.append(round(base * 1.05 ** (q - 1) / max(1, n_active) / 5000) * 5000 if on else 0)
                if any(qs): ws.append([rep, r] + qs + [sum(qs)])
        ws.column_dimensions['A'].width = 22
        wb.save(out('sales', 'quotas', f'AE_quotas_FY{y}.xlsx'))


def write_headcount():
    wb = Workbook(); ws = wb.active; ws.title = 'Headcount'
    ws.append(['Month'] + list(HC0) + ['Total'])
    for y, m in MONTHS:
        hc = headcount(y, m); ws.append([f'{MNAME[m][:3]} {y}'] + list(hc.values()) + [sum(hc.values())])
    wb.save(out('hr', 'headcount_by_department.xlsx'))


# ───────────────────────── unstructured: board, notes, inbox ─────────────────────────
def q_months(y, q): return [(y, m) for m in range(3 * q - 2, 3 * q + 1) if (y, m) in dict.fromkeys(MONTHS)]


HIGHLIGHTS = {
    (2024, 1): ['Closed 2023 with a clean audit; Cluj engineering hub at 20 engineers.', 'LinkedIn lead-gen in EMEA is our best paid source by pipeline quality.'],
    (2024, 2): ['Competitor-conquest search campaign launched in North America (April).', 'Hired Camila Rojas to open LATAM sales.'],
    (2024, 3): ['Self-serve signups up QoQ despite August seasonality.', 'First APAC enterprise logos via Kenji Watanabe.'],
    (2024, 4): ['Black Friday promo (40% off first year) drove a record signup week; watch retention of these cohorts.', 'Web Builders Lisbon sponsorship.'],
    (2025, 1): ['Opened Amsterdam office; EU entity now invoices EMEA customers.', 'Launched APAC search campaigns in January; early CAC is the lowest of any region.',
                'Sales hiring push: +5 AEs/SDRs in Q1.'],
    (2025, 2): ['Lumora Insights add-on launched 1 April ($8/seat/month).', 'Major outage on 12 June (≈5 hours, database failover). Root cause: storage migration. Credits issued to enterprise customers.'],
    (2025, 3): ['Post-outage churn above plan in Team/Starter; NPS dropped this quarter.', 'Q3 webinar series on LinkedIn produced strong enterprise pipeline.'],
    (2025, 4): ['Board approved Team plan price increase from $25 to $29/seat effective 1 Jan 2026.', 'Black Friday 2025 promo repeated with larger Meta budget.',
                'Marcus Webb (AE, North America) left in October; accounts reassigned.'],
    (2026, 1): ['Team plan price increase live. Billing tickets up sharply in Jan–Feb; churn in Team monthly well above plan.',
                'Moved Meta budget into Advantage+ — platform reports strong conversions but downstream conversion to paid is weak.'],
    (2026, 2): ['North America enterprise lost several late-stage deals to a lower-priced competitor with AI features.', 'EMEA ahead of plan for the third straight quarter.',
                'Paused FB_Prospecting_LAL_NA mid-June.'],
    (2026, 3): ['APAC now ~a quarter of new paying customers. Opening a Singapore entity is on the agenda.', 'Q3 planning: re-balance paid social away from Meta.'],
}


def write_board(M, F, B):
    for y, q in QUARTERS:
        ms = q_months(y, q)
        if not ms: continue
        e, s_ = ms[-1], add_months(date(*ms[0], 1), -1)
        rowe = M[e]; mrr_e = rowe['mrr_self'] + rowe['mrr_ent']
        prev = M.get((s_.year, s_.month)); mrr_p = (prev['mrr_self'] + prev['mrr_ent']) if prev else None
        rev = sum(F[k_]['revenue'] for k_ in ms); bud = sum(B[k_]['revenue'] for k_ in ms) if all(k_ in B for k_ in ms) else None
        new = sum(M[k_]['new'] for k_ in ms); churned = sum(M[k_]['churned'] for k_ in ms)
        ebitda = sum(F[k_]['ebitda'] for k_ in ms); ads = sum(sum(F[k_]['ads'].values()) for k_ in ms)
        acv = sum(F[k_]['new_ent_acv'] for k_ in ms)
        p = out('board', f'Board_Update_{y}_Q{q}.pdf')
        cv = canvas.Canvas(p, pagesize=A4); W, H = A4
        cv.setFont('Helvetica-Bold', 18); cv.drawString(40, H - 60, f'Lumora Software — Board Update Q{q} {y}')
        cv.setFont('Helvetica-Oblique', 9); cv.drawString(40, H - 76, 'Confidential — prepared by the CEO and CFO for the Board of Directors')
        lines = ['KEY METRICS', f'  ARR at quarter end:            ${mrr_e * 12 / 1e6:,.2f}M' + (f'   ({(mrr_e / mrr_p - 1) * 100:+.1f}% QoQ)' if mrr_p else ''),
                 f'  Revenue in quarter:            ${rev / 1e6:,.2f}M' + (f'   vs budget ${bud / 1e6:,.2f}M ({(rev / bud - 1) * 100:+.1f}%)' if bud else ''),
                 f'  Paying customers:              {rowe["customers"]:,}  (enterprise: {rowe["ent_customers"]})',
                 f'  New paying customers:          {new:,}      Churned: {churned:,}', f'  New enterprise ACV booked:     ${acv / 1e3:,.0f}k',
                 f'  Paid media spend:              ${ads / 1e3:,.0f}k', f'  EBITDA:                        ${ebitda / 1e3:,.0f}k',
                 f'  Headcount:                     {sum(F[e]["hc"].values())}', '', 'HIGHLIGHTS & ISSUES'] + [f'  • {h}' for h in HIGHLIGHTS.get((y, q), [])]
        nq = add_months(date(*e, 1), 1)
        if (nq.year, nq.month) in B:
            nb = [add_months(nq, i) for i in range(3)]
            nb = [(d.year, d.month) for d in nb if (d.year, d.month) in B]
            lines += ['', 'TARGETS FOR NEXT QUARTER', f'  Revenue: ${sum(B[k_]["revenue"] for k_ in nb) / 1e6:,.2f}M',
                      f'  New paying customers: {round(sum(B[k_]["new"] for k_ in nb)):,}', f'  MRR at end of quarter: ${B[nb[-1]]["rev_self"] / 1e3 + B[nb[-1]]["rev_ent"] / 1e3:,.0f}k']
        pdf_lines(cv, 40, H - 110, lines, 10, 15)
        cv.showPage()
        cv.setFont('Helvetica-Bold', 13); cv.drawString(40, H - 60, 'Appendix — MRR by region at quarter end (USD)')
        pdf_lines(cv, 40, H - 90, [f'  {r:<16}{rowe["mrr_region"][r]:>14,.0f}' for r in REGIONS], 10, 15, 'Courier')
        cv.save()


def write_growth_notes(M, F):
    for y, m in MONTHS:
        cur = [s for s in signups if (s['ts'].year, s['ts'].month) == (y, m)]
        by_ch = defaultdict(int)
        for s in cur: by_ch[s['ch']] += 1
        sp = F[(y, m)]['ads']
        camp = defaultdict(lambda: [0., 0, 0.])
        for r in ad_rows:
            if (r['d'].year, r['d'].month) == (y, m): camp[r['c']['name']][0] += r['spend']; camp[r['c']['name']][1] += r['conv']; camp[r['c']['name']][2] += r['value']
        top = sorted(camp.items(), key=lambda kv: -kv[1][0])[:5]
        notes = [f'# Growth weekly — {MNAME[m]} {y} (monthly roll-up)', '', f'Attendees: CMO, Head of Growth, Performance marketing, RevOps', '',
                 '## Numbers', f'- Sign-ups: **{len(cur):,}** ({", ".join(f"{k_} {v}" for k_, v in sorted(by_ch.items(), key=lambda kv: -kv[1]))})',
                 f'- New paying customers: {M[(y, m)]["new"]}', f'- Spend: Google ${sp["google"]:,.0f} · Meta ${sp["meta"]:,.0f} · LinkedIn ${sp["linkedin"]:,.0f}', '',
                 '## Top campaigns by spend (platform-reported)', '| Campaign | Spend | Conv. | ROAS (platform) |', '|---|---|---|---|']
        notes += [f'| {n} | ${v[0]:,.0f} | {v[1]} | {v[2] / v[0]:.2f} |' for n, v in top]
        extra = {
            (2024, 11): ['Black Friday: 40% off first year. Ran FB_BlackFriday_2024 at ~$850/day. Signups look amazing — need to check paid conversion in Q1.'],
            (2025, 1): ['GS_Generic_APAC live. Early CPA looks cheap. Kenji wants more budget in Japan/Australia.'],
            (2025, 4): ['Insights launch campaign live. PMax keeps eating budget; leads look low quality per sales.'],
            (2025, 6): ['Outage on the 12th — paused all paid campaigns for the afternoon? (No — we forgot, spend continued.)', 'Expect churn uptick in July/August.'],
            (2026, 1): ['Advantage+ ramping. Meta says ROAS > 3 but our Stripe data does not show it yet.', 'Price increase is generating angry tickets — coordinate with CS.'],
            (2026, 3): ['Meta platform ROAS keeps looking OK, but CRM shows very few paying customers from IG_Reels and Advantage+. Need a proper attribution analysis.'],
            (2026, 6): ['Paused FB_Prospecting_LAL_NA on the 14th.', 'Proposal: move 30% of Meta budget to GS_Generic_APAC and LI_ABM_APAC.'],
        }.get((y, m), ['No major changes. Keep budgets flat.'] if m % 2 else ['Test new ad creatives on retargeting.'])
        notes += ['', '## Notes & decisions'] + [f'- {x}' for x in extra] + ['', '## Action items', '- [ ] RevOps: refresh attribution sheet', '- [ ] Perf marketing: weekly budget pacing check']
        with open(out('notes', 'growth', f'{y}-{m:02d}_growth_review.md'), 'w') as f: f.write('\n'.join(notes) + '\n')


def write_pipeline_docs():
    for y, m in MONTHS:
        t = month_end(y, m)
        doc = Document()
        doc.add_heading(f'Enterprise pipeline review — {MNAME[m]} {y}', 1)
        open_ = [d for d in deals if d['created'] <= t and (d['close'] > t or not d['stage'].startswith('Closed'))]
        won = [d for d in deals if d['stage'] == 'Closed won' and (d['close'].year, d['close'].month) == (y, m)]
        lost = [d for d in deals if d['stage'] == 'Closed lost' and (d['close'].year, d['close'].month) == (y, m)]
        doc.add_paragraph(f'Open pipeline at month end: {len(open_)} deals, ${sum(d["amount"] for d in open_) / 1e6:,.2f}M total ACV.')
        tab = doc.add_table(rows=1, cols=4); tab.style = 'Light Grid Accent 1'
        for i, h in enumerate(['Region', 'Open deals', 'Open ACV (USD)', 'Won this month']): tab.rows[0].cells[i].text = h
        for r in REGIONS:
            cells = tab.add_row().cells
            cells[0].text = r; cells[1].text = str(len([d for d in open_ if d['region'] == r]))
            cells[2].text = f'{sum(d["amount"] for d in open_ if d["region"] == r):,.0f}'; cells[3].text = str(len([d for d in won if d['region'] == r]))
        doc.add_heading('Closed won', 2)
        for d in won: doc.add_paragraph(f'{d["company"]} ({COUNTRIES[d["ci"]][0]}) — {d["seats"]} seats, ${d["amount"]:,.0f} ACV — {d["rep"]}', style='List Bullet')
        if not won: doc.add_paragraph('None this month.')
        doc.add_heading('Closed lost', 2)
        for d in lost: doc.add_paragraph(f'{d["company"]} — ${d["amount"]:,.0f} — {d["lost"]} ({d["rep"]})', style='List Bullet')
        doc.save(out('notes', 'sales', f'Pipeline_review_{y}-{m:02d}.docx'))


def eml(path, frm, to, subj, body, when):
    msg = EmailMessage()
    msg['From'], msg['To'], msg['Subject'] = frm, to, subj
    msg['Date'] = when.strftime('%a, %d %b %Y %H:%M:%S +0000')
    msg['Message-ID'] = make_msgid(domain=frm.split('@')[-1].rstrip('>'))
    msg.set_content(body)
    with open(path, 'wb') as f: f.write(bytes(msg))


def write_inbox():
    churned = [c for c in customers if c['kind'] == 'self' and c['churn_type'] == 'voluntary']
    random.shuffle(churned)
    reasons_2026 = ['Your price increase for the Team plan is too much for us. We are moving to a cheaper tool.',
                    'We got the renewal notice with the new $29 price. Not justifiable for what we use. Please cancel.']
    reasons = ['We are consolidating tools and moving everything into Notion.', 'Our project ended and we no longer need the seats.',
               'Budget cuts this quarter, we have to cancel all non-essential software.', 'The team never really adopted it, sorry.',
               'We were acquired and the parent company uses another tool.', 'Too slow for our big boards, we had to switch.']
    n = 0
    for c in churned[:220]:
        d = c['churn']
        if c['plan'] == 'team' and date(2026, 1, 20) <= d <= date(2026, 4, 30): reason = random.choice(reasons_2026)
        elif c['promo']: reason = 'The discount from Black Friday is ending and the full price is too high for a team our size.'
        elif OUTAGE <= d <= date(2025, 8, 15) and random.random() < .5: reason = 'After the outage in June we lost confidence. We need something more reliable.'
        else: reason = random.choice(reasons)
        when = datetime(d.year, d.month, d.day, 9) - timedelta(days=random.randint(1, 10), hours=random.randint(0, 8))
        f_ = c['contact'].split()[0]
        eml(out('inbox', 'support', f'{when:%Y-%m-%d}_cancel_{c["id"]}.eml'), f'{c["contact"]} <{c["email"]}>', 'support@lumora.io',
            random.choice(['Cancel our subscription', 'Cancellation request', 'Please cancel', f'{c["company"]} — cancelling Lumora']),
            f'Hi Lumora team,\n\n{reason}\n\nPlease cancel our {PLAN_LABEL[c["plan"]]} subscription ({c["seats"]} seats) at the end of the current period.\n\nThanks,\n{f_}\n{c["company"]}', when)
        n += 1
    ents = [c for c in customers if c['kind'] == 'ent' and active(c, OUTAGE)]
    for c in random.sample(ents, min(25, len(ents))):
        when = datetime(2025, 6, 12, random.randint(14, 20), random.randint(0, 59))
        eml(out('inbox', 'support', f'{when:%Y-%m-%d}_outage_{c["id"]}.eml'), f'{c["contact"]} <{c["email"]}>', 'support@lumora.io',
            random.choice(['URGENT: Lumora down', 'Outage — status?', 'We cannot access our boards', 'SLA breach today']),
            f'Hello,\n\nOur whole team ({c["seats"]} users) has been locked out for {random.randint(1, 4)} hours now. This is the second time this year. '
            f'We need an incident report and to discuss SLA credits under our contract.\n\nRegards,\n{c["contact"]}\n{c["company"]}', when)
    late = [r for r in invoice_register if r['paid'] is None or (r['paid'] - r['due']).days > 25]
    for r in random.sample(late, min(40, len(late))):
        when = datetime.combine(r['due'] + timedelta(days=random.randint(10, 30)), datetime.min.time()) + timedelta(hours=10)
        if when.date() > EXPORTED: continue
        eml(out('inbox', 'finance', f'{when:%Y-%m-%d}_reminder_{r["no"]}.eml'), 'Lumora Billing <billing@lumora.io>', f'{r["c"]["contact"]} <{r["c"]["email"]}>',
            f'Payment reminder — invoice {r["no"]} overdue',
            f'Dear {r["c"]["contact"]},\n\nOur records show invoice {r["no"]} dated {r["date"]:%d %B %Y} for {r["cur"]} {r["total"]:,.2f} was due on {r["due"]:%d %B %Y} and remains unpaid.\n'
            f'Please arrange payment or let us know if there is an issue with the invoice.\n\nKind regards,\nLumora Accounts Receivable', when)
    for dl in random.sample([d for d in deals if d['source'] == 'Partner'], min(30, len([d for d in deals if d['source'] == 'Partner']))):
        pn = random.choice(PARTNERS)[0]
        when = datetime.combine(dl['created'], datetime.min.time()) + timedelta(hours=random.randint(8, 17))
        eml(out('inbox', 'partners', f'{when:%Y-%m-%d}_dealreg_{dl["id"]}.eml'), f'{pn} <deals@{re.sub("[^a-z]", "", pn.lower())}.com>', 'partners@lumora.io',
            f'Deal registration: {dl["company"]}',
            f'Hi team,\n\nWe would like to register {dl["company"]} ({COUNTRIES[dl["ci"]][0]}, ~{dl["seats"]} users, {dl["industry"]}).\n'
            f'Main contact: {dl["contact"]}. They are evaluating Lumora against two other tools, decision expected within {random.randint(1, 4)} months.\n\nBest,\n{pn}', when)


# ───────────────────────── main ─────────────────────────
def main():
    if os.path.isdir(ROOT) and os.listdir(ROOT):
        raise SystemExit(f'{ROOT} exists and is not empty; delete it or run from another folder')
    os.makedirs(ROOT)
    print('simulating pre-2024 base…'); gen_legacy()
    print('simulating acquisition…'); gen_acquisition()
    print('simulating enterprise sales…'); gen_deals()
    print(f'  {len(signups):,} sign-ups · {len(customers):,} customers · {len(deals):,} deals · {len(ad_rows):,} ad rows')
    M = build_monthly()
    steps = [('ads', write_ads), ('ga4', write_ga4), ('crm', write_crm), ('deals', write_deals), ('stripe', write_stripe), ('invoices', write_invoices),
             ('order forms', write_order_forms), ('AR', write_ar), ('usage', lambda: write_usage(M)), ('zendesk', lambda: write_zendesk(M)), ('nps', write_nps)]
    for name, fn in steps: print(f'writing {name}…'); fn()
    partner_rows = write_partners()
    F = build_finance(M, partner_rows)
    B = build_budget(M, F)
    for name, fn in [('GL', lambda: write_gl(F)), ('budgets', lambda: write_budgets(B)), ('management accounts', lambda: write_mgmt_accounts(M, F, B)),
                     ('quotas', write_quotas), ('headcount', write_headcount), ('board', lambda: write_board(M, F, B)), ('growth notes', lambda: write_growth_notes(M, F)),
                     ('pipeline docs', write_pipeline_docs), ('inbox', write_inbox)]:
        print(f'writing {name}…'); fn()
    e = M[MONTHS[-1]]
    print(f'ARR end: ${(e["mrr_self"] + e["mrr_ent"]) * 12 / 1e6:.2f}M · paying customers {e["customers"]:,} (enterprise {e["ent_customers"]})')
    n = sum(len(fs) for _, _, fs in os.walk(ROOT))
    print(f'done: {n} files in {ROOT}')


if __name__ == '__main__':
    main()
