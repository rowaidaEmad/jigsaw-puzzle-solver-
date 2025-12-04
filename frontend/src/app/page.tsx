import { Button } from '@/components/ui/button';
import Image from 'next/image';

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-black">
      {/* Header */}
      <header className="border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-6 py-4 max-w-6xl flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Image src="/icon-96.svg" alt="Logo" width={40} height={40} className="dark:invert" />
            <span className="text-xl font-bold text-black dark:text-white">Puzzle Solver</span>
          </div>

          <nav className="flex items-center gap-6">
            <a href="#features" className="text-sm text-slate-600 dark:text-slate-400 hover:text-[#5185A1] transition">
              Features
            </a>
            <a href="#demo" className="text-sm text-slate-600 dark:text-slate-400 hover:text-[#5185A1] transition">
              Demo
            </a>
            <Button size="sm" className="bg-[#5185A1] hover:bg-[#4174-90] text-white">
              Try Now
            </Button>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6 py-16 max-w-6xl">
        {/* Hero */}
        <div className="flex flex-col md:flex-row items-center gap-12 mb-32">
          <div className="flex-1 space-y-6">
            <div className="inline-block">
              <span className="text-sm font-medium text-[#5185A1]">awesomeness</span>
            </div>

            <h1 className="text-6xl md:text-7xl font-bold tracking-tight text-black dark:text-white">
              Jigsaw Puzzle
              <br />
              Solver
            </h1>

            <p className="text-xl text-slate-600 dark:text-slate-400 max-w-xl leading-relaxed">
              Computer vision meets puzzle solving. Upload an image, customize parameters, and watch the algorithms work their magic.
            </p>

            <div className="flex gap-3 pt-4">
              <Button size="lg" className="bg-[#5185A1] hover:bg-[#417490] text-white">
                Get Started
              </Button>
              <Button size="lg" variant="outline" className="border-[#5185A1] text-[#5185A1] hover:bg-[#5185A1] hover:text-white">
                View Demo
              </Button>
            </div>
          </div>

          <div className="flex-1 flex justify-center">
            <Image src="/icon-480.svg" alt="Puzzle Solver" width={400} height={400} className="dark:invert opacity-90" />
          </div>
        </div>

        {/* Features */}
        <div id="features" className="mb-32">
          <h2 className="text-4xl font-bold text-black dark:text-white mb-12 text-center">How it works</h2>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="group p-8 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-[#5185A1] transition">
              <div className="w-12 h-12 rounded-lg bg-[#5185A1]/10 flex items-center justify-center text-2xl mb-4">🎨</div>
              <h3 className="text-xl font-semibold text-black dark:text-white mb-3">Preprocessing</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                Upscaling with Lanczos interpolation, adaptive thresholding, and edge detection to prepare puzzle pieces.
              </p>
            </div>

            <div className="group p-8 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-[#5185A1] transition">
              <div className="w-12 h-12 rounded-lg bg-[#5185A1]/10 flex items-center justify-center text-2xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold text-black dark:text-white mb-3">Computer Vision</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                Advanced contour extraction, Canny edge detection, and morphological operations for precise analysis.
              </p>
            </div>

            <div className="group p-8 rounded-lg border border-slate-200 dark:border-slate-800 hover:border-[#5185A1] transition">
              <div className="w-12 h-12 rounded-lg bg-[#5185A1]/10 flex items-center justify-center text-2xl mb-4">⚡</div>
              <h3 className="text-xl font-semibold text-black dark:text-white mb-3">Multiple Sizes</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                Support for 2×2, 4×4, and 8×8 puzzle grids with automatic tile extraction and segmentation.
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="rounded-lg border border-slate-200 dark:border-slate-800 p-12 bg-slate-50 dark:bg-slate-900/50">
          <div className="grid grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-black dark:text-white mb-2">2-8×8</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Grid Sizes</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-black dark:text-white mb-2">5 Steps</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Processing Pipeline</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-black dark:text-white mb-2">∞</div>
              <div className="text-sm text-slate-600 dark:text-slate-400">Awesomeness Level</div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 mt-20">
        <div className="container mx-auto px-6 py-8 max-w-6xl flex items-center justify-between">
          <div className="text-sm text-slate-600 dark:text-slate-400">Built with awesomeness</div>
          <div className="flex items-center gap-6 text-sm text-slate-600 dark:text-slate-400">
            <a href="#" className="hover:text-black dark:hover:text-white transition">
              GitHub
            </a>
            <a href="#" className="hover:text-black dark:hover:text-white transition">
              Docs
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
