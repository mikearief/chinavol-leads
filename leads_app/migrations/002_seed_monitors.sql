INSERT OR IGNORE INTO leads_monitors (slug, pm_question, ticker, description, signal_thresh_pp, cooldown_hrs)
VALUES
  ('will-china-invade-taiwan-before-2027',
   'Will China invade Taiwan by end of 2026?',
   'FXI',
    'iShares China Large-Cap ETF. Taiwan tension drives China risk-off. PM leads FXI at 45min: r=-0.151, p=0.0003, n=564 obs.',
    1.5, 4.0),
  ('will-china-invade-taiwan-before-2027',
   'Will China invade Taiwan by end of 2026?',
   'KWEB',
   'KraneShares CSI China Internet ETF. Tech-heavy China. PM leads KWEB at 45min: r=-0.160, p=0.0001, n=564 obs.',
    1.5, 4.0),
  ('us-x-iran-permanent-peace-deal-by-may-31-2026-333-871-241-192-799-449-125',
   'US x Iran permanent peace deal by May 31, 2026?',
   'OIH',
   'VanEck Oil Service ETF. Iran peace reduces supply risk. PM leads OIH at 45min: r=-0.247, p=0.029, n=367 obs.',
   2.0, 6.0);
