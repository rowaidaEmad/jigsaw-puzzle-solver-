'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import type { MouseEvent } from 'react';

export default function Footer() {
  const [showMessage, setShowMessage] = useState(false);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    };
  }, []);

  function onGithubClick(e: MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    setShowMessage(true);
    if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
    // hide after 8 seconds
    timeoutRef.current = window.setTimeout(() => setShowMessage(false), 8000);
  }

  return (
    <footer className="border-t border-slate-200 dark:border-slate-800">
      <div className="container mx-auto px-6 py-4 max-w-6xl flex items-center justify-between relative">
        <div className="text-sm text-slate-600 dark:text-slate-400">Built with awesomeness</div>
        <div className="flex items-center gap-6 text-sm text-slate-600 dark:text-slate-400">
          <button
            onClick={onGithubClick}
            className="bg-transparent hover:text-black dark:hover:text-white transition text-sm leading-none"
            aria-label="Private GitHub repository (click for details)">
            GitHub
          </button>
          <Link href="/docs" className="hover:text-black dark:hover:text-white transition">
            Docs
          </Link>
        </div>

        {showMessage && (
          <div
            role="status"
            aria-live="polite"
            className="absolute left-1/2 -translate-x-1/2 bottom-full mb-3 w-full max-w-md rounded-md bg-slate-50 shadow-md p-3 text-sm text-slate-800 dark:bg-slate-900 dark:text-slate-100">
            <div className="flex items-start gap-3">
              <div className="flex-1">
                <strong className="block">Whoa there!</strong>
                <div className="mt-1">
                  This repository is currently classified as &ldquo;Too Awesome to share yet&quot; - it&apos;s slated for a Phase 2 public
                  debut. Want VIP access? Email{' '}
                  <a href="mailto:sharqawycs@gmail.com" className="underline hover:text-black dark:hover:text-white">
                    sharqawycs@gmail.com
                  </a>{' '}
                  or call{' '}
                  <a href="tel:+201091215660" className="underline hover:text-black dark:hover:text-white">
                    +201091215660
                  </a>{' '}
                  the password is &rdquo;I feel awesome&#34;.
                </div>
              </div>
              <button
                aria-label="Close"
                onClick={() => setShowMessage(false)}
                className="text-slate-500 hover:text-slate-900 dark:hover:text-slate-200">
                ✕
              </button>
            </div>
          </div>
        )}
      </div>
    </footer>
  );
}
