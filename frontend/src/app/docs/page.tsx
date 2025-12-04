'use client';

import { Grid } from '@/components/ui/grid-pattern';

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <main className="container mx-auto px-6 py-12 max-w-6xl">
        <div className="relative p-8 rounded-2xl border border-slate-200 dark:border-slate-800 bg-gradient-to-b from-white to-slate-50 dark:from-black dark:to-slate-900">
          <div className="flex items-center gap-4 mb-6">
            <Grid size={14} seed="docs-hero" />
            <h1 className="text-3xl font-bold text-black dark:text-white">Project README - Phase 1</h1>
          </div>

          <section className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Getting access to the repo</h2>
            <p className="text-slate-600 dark:text-slate-400">
              This repository is currently private. If you want access before Phase 2&lsquo;s public release, please contact us via email or
              phone.
            </p>
            <p className="mt-2">Clone it</p>
            <pre className="mt-3 p-3 bg-slate-100 dark:bg-slate-800 rounded text-sm overflow-auto">
              git clone git@github.com:sharqawycs/jigsaw-puzzle-solver.git
            </pre>
          </section>

          <section className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Installation & Environment</h2>
            <p className="text-slate-600 dark:text-slate-400">
              The project is tested on Python 3.11 and 3.12 on Arch Linux, Windows 11, and MacOS 26.
            </p>

            <ol className="list-decimal list-inside mt-3 text-slate-600 dark:text-slate-400">
              <li className="mb-2">
                Install dependencies:
                <pre className="mt-1 p-3 bg-slate-100 dark:bg-slate-800 rounded text-sm overflow-auto">pip install -r requirements.txt</pre>
              </li>
              <li className="mb-2">
                Put your puzzle images in <code>data/puzzle_NxN/</code> folders (it&lsquo;s already there for you)
              </li>
              <li className="mb-2">
                Open and run <code>phase1.ipynb</code> in Jupyter
              </li>
              <li className="mb-2">
                You will find the processed tiles in <code>output/puzzle_NxN/</code> folders
              </li>
            </ol>
          </section>

          <section className="mt-8 p-4 rounded bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <h3 className="text-lg font-semibold">Need access? Contact us</h3>
            <p className="text-slate-600 dark:text-slate-400 mt-2">
              Email:{' '}
              <a href="mailto:sharqawycs@gmail.com" className="underline">
                sharqawycs@gmail.com
              </a>{' '}
              • Call:{' '}
              <a href="tel:+201091215660" className="underline">
                +201091215660
              </a>
            </p>
          </section>

          <div className="mt-6 text-center">
            <strong className="text-primary">AWESOME ✨</strong>
          </div>
        </div>
      </main>
    </div>
  );
}
