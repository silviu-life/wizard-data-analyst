# Lumora Software — ce e ascuns în `date/` (cheia demo-ului)

Generat de `genereaza_date_demo.py` (seed 42, ~30 s). Ține-l departe de folderul `date/` când rulezi analiza: Claude trebuie să găsească singur poveștile. La final compari ce a găsit cu lista de mai jos.

**Firma:** Lumora Software, B2B SaaS de project management, fondată în 2021, HQ San Francisco, hub de engineering în Cluj, entitate EU în Amsterdam (din 2025). Clienți în 48 de țări. Datele acoperă 2024-01-01 → 2026-09-30 (export pe 2026-10-01).
Self-serve (Starter $12 / Team $25→$29 / Business $45 per seat/lună, plătit prin Stripe) + Enterprise sales-led (facturi PDF, transfer bancar).

## Povești plantate (ce ar trebui să găsească analiza)

1. **Creștere:** ARR ~$7,4M (ian 2024) → ~$34M (sep 2026). EBITDA negativ în 2024, pozitiv din T3 2025.
2. **APAC explodează din 2025:** campaniile `GS_Generic_APAC` (ian 2025) și `FB_Prospecting_APAC` (mai 2025) duc ponderea APAC în clienții noi de la ~10% la ~25–28%. Bugetul a subestimat APAC.
3. **Scumpirea planului Team (1 ian 2026, $25→$29):** churn-ul Team se dublează în ian–apr 2026, apare un val de tichete „Billing / price_increase_2026”, NPS scade în T1–T2 2026 și apar emailuri de anulare care citează prețul. Câștigul de MRR din scumpire e mâncat parțial de churn.
4. **Pana din 12 iunie 2025** (~13:00–18:00 UTC): utilizarea orară scade aproape la zero, tichetele urcă de la ~35/zi la ~270, CSAT scade, churn-ul crește în iul–aug, NPS T3 2025 e cel mai prost (≈ −21), plus emailuri de la clienții enterprise despre SLA.
5. **Meta minte:** ROAS-ul raportat de platformă arată ok, dar în CRM/Stripe `Meta_AdvantagePlus_2026` (CAC ~$3.4k) și `IG_Reels_Awareness_Global` (~$2.3k) sunt cele mai proaste campanii. Din 2026 toată rețeaua Meta are conversie cu −38% (oboseala audienței). Cel mai bun e `GS_Brand_Global` (CAC ~$60).
6. **Black Friday (40% reducere în primul an):** volum mare de signup-uri, dar retenția cohortei e mult mai slabă (~35% supraviețuire la 15 luni, față de ~54% la cohorta normală), cu un vârf de churn când expiră reducerea.
7. **LinkedIn:** CAC mare, dar aduce clienți de calitate (mai mulți pe Business, churn mai mic). `LI_ABM_Enterprise_NA` alimentează pipeline-ul enterprise.
8. **Enterprise North America ratează T2 2026:** win rate ~9% (pierdute la un concurent mai ieftin, cu funcții AI). EMEA depășește planul în 2026 (win rate 35%). Churn-ul NA la reînnoire se dublează în 2026. Marcus Webb (AE NA) pleacă în oct 2025.
9. **Add-on-ul Insights** (lansat 1 apr 2025, $8/seat) generează venit din expansiune; `reports_generated` din usage apare doar după lansare.
10. **Parteneri:** canal mic, dar cu cea mai bună rată de activare/plată (64% / 44%).
11. **Sezonalitate:** scădere în august și decembrie. Utilizarea are vârf marți–miercuri, 10–11 ora locală.
12. **DSO:** clienții enterprise din APAC/LATAM plătesc facturile mai târziu (~+12 zile).

## Capcane de curățare (realiste, intenționate)

- **Stripe:** formatul se schimbă din 2025-07 (`payments_*` → `unified_payments_*`): sume în unități minore (cenți; JPY fără zecimale), status `Paid`→`succeeded`, date ISO cu `Z`. Exporturile `2025-03` și `2026-02` se suprapun cu ultimele zile din luna precedentă, deci apar **rânduri duplicate**. Plățile sunt în 6 valute, cu coloana `Converted Amount` în USD.
- **Enterprise apare doar în PDF-uri:** ~900 de facturi (`INV-…` pentru entitatea US, `LSE-…` pentru cea EU, în USD/EUR/GBP) și ~190 de order forms. Încasările sunt în `finance/AR_receipts_*.xlsx`.
- **Google Ads:** 2 rânduri de titlu deasupra headerului, `1,234.56` cu virgulă la mii, CTR ca `3.45%` și un rând `Total: Account` la final.
- **Meta:** cheltuiala e în **EUR**, CTR e un procent scris ca număr, iar Results e gol când nu există conversii.
- **LinkedIn:** 6 rânduri de metadate deasupra headerului, date `M/D/YYYY`, CTR ca fracție, Leads vs Conversions în funcție de obiectiv.
- **GA4:** header cu linii comentate `#`, date `YYYYMMDD`. Partenerii apar ca `Referral`. GA4 vede ~90% din signup-uri (consent).
- **CRM:** țări scrise în mai multe feluri (`USA`/`U.S.`/`United States`, `Deutschland`, `日本`, `Türkiye`…), ~3% fără țară. Datele de dinainte de iul 2024 sunt `MM/DD/YYYY`. ~1,2% duplicate (email cu altă capitalizare). Lipsesc industrii.
- **HubSpot deals:** coloana `Amount (USD)` din 2024 devine `Amount` din 2025.
- **GL:** separator `;`, zecimale cu virgulă (`1.234,56`), date `DD/MM/YYYY`, BOM UTF-8.
- **Management accounts:** cifrele sunt în **USD '000**, iar 2024 nu are buget comparativ în coloana Budget.
- **Bugete:** format lat (luni pe coloane), cu titlu și rânduri goale deasupra tabelului.
- **NPS:** comentarii în EN/DE/PT/ES/FR/JA. Țara lipsește; se face join pe email cu CRM.
- **Zendesk:** CSAT `Good/Bad/Offered/Unoffered`; chat-ul există doar din ian 2025.
