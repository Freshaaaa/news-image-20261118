[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Freshaaaa/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Freshaaaa/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

# The World in One Day — 18 November 2026

A make.fun entry for **news-image-20261118**: one image that sums up the
world's news of Wednesday 18 November 2026. Bounty: https://make.fun/bounty/news-image-20261118

`main.ts` (Node 22, standard library only) copies `entry.png` to
`/output/entry.png`. The image itself is drawn by `build-image.py`
(Python 3, PIL, DejaVu fonts) as a one-page world-news summary in the
structure the top entries use:

- **40 stories, 7 regions, one page** — the date named in full ("Wednesday
  18 November 2026") with a region count bar and "the day in numbers"
  (141 drones fired, 126 downed, Voyager 1 at 25.9bn km, 55 factories
  shut, Jeffries 251–11, Ebola 11,300+ cases).
- **13 large cards** with original drawn pictograms, numbered region tags
  and verification tags (CONFIRMED / CLAIM + source): Xi greets Trump at
  APEC in Shenzhen · Bahrain and Kuwait intercept Iran's drones · Voyager 1
  reaches one light-day · Russia fires 141 drones at Ukraine · Fed minutes
  point to more hikes · Cyclone Akvan turns toward Odisha · RSF drones
  kill 37 in El Obeid · EU proposes a €45bn loan for Kyiv · UK inflation
  3.6% · Israeli tanks push into central Gaza · Jeffries picked for House
  Speaker · GTA VI goes on sale · Bangladesh wage protests shut 55
  factories.
- **A world map** with 13 numbered pins, **27 more stories** in three
  columns, and a **DATE CHECK** box naming what was left out on purpose
  (Tuesday stories: the Qeshm strike, Peltola's Senate win, the Kerch
  Bridge span collapse, Nvidia's quarter, the Knesset speaker vote, the
  Prague rail crash) and what has not happened yet (the Trump–Xi–Putin
  talks, Akvan's landfall, the close of COP31).

Every story on the page happened, or was first reported, on Wednesday
18 November 2026 (AP, Reuters, AFP, BBC, CNN, CNBC, NPR, Fed, ONS, IMD,
NASA, WHO, Amnesty). The build is fully deterministic: no network, no
clock, no randomness — two runs write identical bytes.

Run it: `mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts`
