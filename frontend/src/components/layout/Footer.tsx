'use client';

import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 dark:border-slate-800">
      <div className="container mx-auto px-6 py-4 max-w-6xl flex items-center justify-between">
        <div className="text-sm text-slate-600 dark:text-slate-400">Built with awesomeness</div>
        <div className="flex items-center gap-6 text-sm text-slate-600 dark:text-slate-400">
          <a
            href="https://github.com/sharqawycs/jigsaw-puzzle-solver"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-black dark:hover:text-white transition">
            GitHub
          </a>
          <Link href="/docs" className="hover:text-black dark:hover:text-white transition">
            Docs
          </Link>
        </div>
      </div>
    </footer>
  );
}
