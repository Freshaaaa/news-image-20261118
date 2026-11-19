// news-image-20261118 — entrypoint (Node 22, standard library only).
//
// entry.png beside this file is the entry: a one-page summary of the
// world's news of Wednesday 18 November 2026, drawn by build-image.py
// (Python, PIL, DejaVu fonts) — 52 stories across 7 regions and 9 fields,
// a day-in-numbers strip, a UTC timeline, a world map with 13 numbered
// pins, and a date check naming what was left out on purpose.
// This program copies that one fixed file to the grader's output
// directory. A plain copy is deterministic: every run writes the same
// bytes, with no network, no clock and no randomness involved.
//
// Local run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });
writeFileSync(join(outDir, 'entry.png'), readFileSync(join(here, 'entry.png')));
