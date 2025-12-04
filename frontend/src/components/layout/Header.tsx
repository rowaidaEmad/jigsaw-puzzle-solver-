import Image from 'next/image';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function Header() {
  return (
    <header className="border-b border-slate-200 dark:border-slate-800">
      <div className="container mx-auto px-6 py-4 max-w-6xl flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <Image src="/icon-96.svg" alt="Logo" width={40} height={40} className="dark:invert" />
          <span className="text-xl font-bold text-black dark:text-white">Puzzle Solver</span>
        </Link>

        <nav className="flex items-center gap-6">
          <Link href="/#features" className="text-sm text-slate-600 dark:text-slate-400 hover:text-primary transition">
            Features
          </Link>
          <Link href="/examples" className="">
            <Button size="sm" className="bg-primary hover:bg-primary/90 text-white">
              Try Now
            </Button>
          </Link>
        </nav>
      </div>
    </header>
  );
}
