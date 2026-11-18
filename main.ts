// news-image-20261118 entry (Node 22, standard library only).
//
// The image is entry.png beside this file: a newspaper front page drawn in
// this session by build-image.py (PIL, DejaVu fonts) from the world news
// reported on Wednesday 18 November 2026. This program copies that file to
// the grader's output directory. Copying one fixed file is deterministic:
// every run writes the same bytes, with no network and no clock involved.
//
// Local run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });
writeFileSync(
  join(outDir, 'entry.png'),
  readFileSync(join(here, 'entry.png')),
);
