'use client';

import { useId, useMemo } from 'react';

export function Grid({ pattern, size, seed }: { pattern?: number[][]; size?: number; seed?: string | number }) {
  // seeded RNG to make patterns deterministic across SSR and CSR
  const p = useMemo(() => {
    if (pattern) return pattern;
    const seedNum = typeof seed === 'number' ? seed : stringToSeed(String(seed ?? 'default'));
    const rng = makeRng(seedNum);
    const res: number[][] = [];
    for (let i = 0; i < 5; i++) {
      const a = Math.floor(rng() * 4) + 7;
      const b = Math.floor(rng() * 6) + 1;
      res.push([a, b]);
    }
    return res;
  }, [pattern, seed]);
  return (
    <div className="pointer-events-none absolute left-1/2 top-0 -ml-20 -mt-2 h-full w-full [mask-image:linear-gradient(white,transparent)]">
      <div className="absolute inset-0 bg-gradient-to-r [mask-image:radial-gradient(farthest-side_at_top,white,transparent)] dark:from-slate-900/30 from-slate-100/30 to-slate-300/30 dark:to-slate-900/30 opacity-100">
        <GridPattern
          width={size ?? 20}
          height={size ?? 20}
          x={-12}
          y={4}
          squares={p}
          className="absolute inset-0 h-full w-full mix-blend-overlay dark:fill-white/10 dark:stroke-white/10 stroke-black/10 fill-black/10"
        />
      </div>
    </div>
  );
}

function stringToSeed(s: string) {
  // simple hash to produce a 32-bit integer from a string
  let hash = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    hash ^= s.charCodeAt(i);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return hash;
}

function makeRng(seedNum: number) {
  // LCG implementation
  let state = seedNum >>> 0;
  return function () {
    // constants from Numerical Recipes
    state = (state * 1664525 + 1013904223) >>> 0;
    return (state & 0xffffffff) / 4294967296;
  };
}

export function GridPattern({ width, height, x: offsetX, y: offsetY, squares, ...props }: any) {
  const patternId = useId();

  return (
    <svg aria-hidden="true" {...props}>
      <defs>
        <pattern id={patternId} width={width} height={height} patternUnits="userSpaceOnUse" x={offsetX} y={offsetY}>
          <path d={`M.5 ${height}V.5H${width}`} fill="none" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" strokeWidth={0} fill={`url(#${patternId})`} />
      {squares && (
        <svg x={offsetX} y={offsetY} className="overflow-visible">
          {squares.map(([sx, sy]: any, idx: number) => (
            <rect strokeWidth="0" key={`${sx}-${sy}-${idx}`} width={width + 1} height={height + 1} x={sx * width} y={sy * height} />
          ))}
        </svg>
      )}
    </svg>
  );
}
