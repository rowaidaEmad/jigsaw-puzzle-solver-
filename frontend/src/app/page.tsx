import { Button } from '@/components/ui/button';
import Image from 'next/image';
import Link from 'next/link';
import { Grid } from '@/components/ui/grid-pattern';
import Footer from '@/components/layout/Footer';

const features = [
  {
    title: 'Preprocessing',
    description: 'Upscaling with Lanczos interpolation, adaptive thresholding, and edge detection to prepare puzzle pieces.',
  },
  {
    title: 'CV',
    description: 'Advanced contour extraction, Canny edge detection, and morphological operations for precise analysis.',
  },
  {
    title: '2-8×8',
    description: 'Support for 2×2, 4×4, and 8×8 puzzle grids with automatic tile extraction and segmentation.',
  },
  {
    title: '5 Steps',
    description: 'Complete processing pipeline from upscaling to contour extraction.',
  },
  {
    title: 'Edge Detection',
    description: 'Canny edge detection algorithm to identify puzzle piece boundaries with precision.',
  },
  {
    title: '∞',
    description: 'Awesomeness Level',
  },
];

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
            <a href="#features" className="text-sm text-slate-600 dark:text-slate-400 hover:text-primary transition">
              Features
            </a>
            <Link href="/examples" className="">
              <Button size="sm" className="bg-primary hover:bg-primary/90 text-white">
                Try Now
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-6 py-16 max-w-6xl">
        {/* Hero */}
        <div className="flex flex-col md:flex-row items-center gap-12 mb-32">
          <div className="flex-1 space-y-6">
            <div className="inline-block">
              <span className="text-sm font-medium text-primary">awesomeness</span>
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
              <Link href="/examples">
                <Button size="lg" className="bg-primary hover:bg-primary/90 text-white">
                  View Examples
                </Button>
              </Link>
            </div>
          </div>

          <div className="flex-1 flex justify-center">
            <Image
              src="/icon-480.svg"
              alt="Puzzle Solver"
              width={400}
              height={400}
              className="dark:invert opacity-90"
              style={{ filter: 'drop-shadow(-5px 7px 35px var(--primary))' }}
            />
          </div>
        </div>

        {/* Features */}
        <div id="features" className="py-20 lg:py-32 mb-32">
          <h2 className="text-4xl font-bold text-black dark:text-white mb-12 text-center">How it works</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {features.map((feature, idx) => (
              <div
                key={feature.title}
                className="relative bg-gradient-to-b dark:from-slate-900 from-slate-50 dark:to-black to-white p-8 rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 text-center">
                <Grid size={20} seed={`${feature.title}-${idx}`} />
                <p className="text-4xl font-bold text-black dark:text-white relative z-20 mb-3">{feature.title}</p>
                <p className="text-slate-600 dark:text-slate-400 text-sm relative z-20">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Team Section */}
        <div className="mb-32">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-black dark:text-white mb-3">The Awesome Squad</h2>
            <p className="text-slate-600 dark:text-slate-400">The humans behind this thing</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            {/* Sherqo */}
            <div className="group text-center">
              <div className="w-20 h-20 rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition overflow-hidden">
                <Image src="/ph2.jpg" alt="Sherqo" width={80} height={80} className="w-full h-full object-cover dark:invert" />
              </div>
              <h3 className="font-semibold text-black dark:text-white mb-1">Sherqo</h3>
              <p className="text-xs text-primary font-medium">Upscaling Specialist</p>
            </div>

            {/* Rowaida */}
            <div className="group text-center">
              <div className="w-20 h-20 rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition overflow-hidden">
                <Image src="/ph.jpg" alt="Rowaida" width={80} height={80} className="w-full h-full object-cover dark:invert" />
              </div>
              <h3 className="font-semibold text-black dark:text-white mb-1">Rowaida</h3>
              <p className="text-xs text-primary font-medium">Filter Wizard</p>
            </div>

            {/* Habiba */}
            <div className="group text-center">
              <div className="w-20 h-20 rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition overflow-hidden">
                <Image src="/ph.jpg" alt="Habiba" width={80} height={80} className="w-full h-full object-cover dark:invert" />
              </div>
              <h3 className="font-semibold text-black dark:text-white mb-1">Habiba</h3>
              <p className="text-xs text-primary font-medium">Morphology Expert</p>
            </div>

            {/* Somaya */}
            <div className="group text-center">
              <div className="w-20 h-20 rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition overflow-hidden">
                <Image src="/ph.jpg" alt="Somaya" width={80} height={80} className="w-full h-full object-cover dark:invert" />
              </div>
              <h3 className="font-semibold text-black dark:text-white mb-1">Somaya</h3>
              <p className="text-xs text-primary font-medium">Edge Detection Pro</p>
            </div>

            {/* Mohamed */}
            <div className="group text-center">
              <div className="w-20 h-20 rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition overflow-hidden">
                <Image src="/ph2.jpg" alt="Mohamed" width={80} height={80} className="w-full h-full object-cover dark:invert" />
              </div>
              <h3 className="font-semibold text-black dark:text-white mb-1">M. Osama</h3>
              <p className="text-xs text-primary font-medium">Segmentation Guru</p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  );
}
