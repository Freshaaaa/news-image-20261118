[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Freshaaaa/news-image-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Freshaaaa/news-image-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

# The World in One Day — 18 November 2026

A make.fun entry for **news-image-20261118**: one image that sums up the
world's news of Wednesday 18 November 2026. Bounty: https://make.fun/bounty/news-image-20261118

`main.ts` (Node 22, standard library only) copies `entry.png` to
`/output/entry.png`. The image itself is drawn by `build-image.py`
(Python 3, PIL, DejaVu fonts) as a newspaper front page:

- **Lead:** U.S. jets strike an Iranian missile site on Qeshm Island after
  Iran fires drones at U.S. radar sites in Bahrain and Kuwait.
- **In brief:** Ukraine hits the Kerch Bridge for a second day · APEC opens
  in Shenzhen ahead of the first Trump–Xi–Putin summit · Peltola wins
  Alaska's Senate seat, giving Democrats a 56-seat majority · Russian
  military plane crash in Siberia, 19 dead · Ebola outbreak in DR Congo
  passes 11,000 cases · Category 5 Cyclone Xavier hits the Northern Cook
  Islands.
- **Also:** Microsoft's seven in-house AI models, Dhoni retires from the
  IPL, the World Court's Myanmar ruling, oil and Hormuz.

Stories are the events first reported on 18 November 2026
(AP, Reuters, BBC, Al Jazeera). The build is fully deterministic: no
network, no clock, no randomness — two runs write identical bytes.

Run it: `mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts`
