import { Button } from '@/components/ui/button';
import Image from 'next/image';
import Link from 'next/link';
import { Grid } from '@/components/ui/grid-pattern';

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

const team = [
  { name: 'Sherqo', role: 'Upscaling Specialist', image: '/ph2.jpg', github: 'https://github.com/sharqawycs' },
  { name: 'Rowaida', role: 'Filter Wizard', image: '/ph.jpg', github: 'https://github.com/rowaidaEmad' },
  { name: 'Habiba', role: 'Morphology Expert', image: '/ph.jpg', github: 'https://github.com/habibadawod' },
  { name: 'Somaya', role: 'Edge Detection Pro', image: '/ph.jpg', github: 'https://github.com/somayagalal' },
  { name: 'M. Osama', role: 'Segmentation Guru', image: '/ph2.jpg', github: 'https://github.com/mohammedosama27' },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <main className="container mx-auto px-6 py-16 max-w-6xl">
        {/* Hero */}
        <div className="flex flex-col md:flex-row items-center gap-12 mb-32">
          <div className="flex-1 space-y-6">
            <h1 className="text-6xl md:text-7xl font-bold tracking-tight text-black dark:text-white">Awesome Jigsaw Puzzle Solver</h1>

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
            {team.map(member => {
              const githubHref = member.github?.trim().length
                ? member.github
                : `https://github.com/search?q=${encodeURIComponent(member.name)}&type=users`;

              return (
                <div key={member.name} className="group text-center">
                  <a href={githubHref} target="_blank" rel="noopener noreferrer" className="block">
                    <div className="w-20 h-20 rounded-full bg-slate-100 dark:bg-slate-900 flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition overflow-hidden">
                      <Image
                        src={member.image}
                        alt={member.name}
                        width={80}
                        height={80}
                        className="w-full h-full object-cover dark:invert"
                      />
                    </div>
                  </a>

                  <a href={githubHref} target="_blank" rel="noopener noreferrer" className="hover:underline">
                    <h3 className="font-semibold text-black dark:text-white mb-1">{member.name}</h3>
                  </a>

                  <p className="text-xs text-primary font-medium">{member.role}</p>
                </div>
              );
            })}
          </div>
        </div>
      </main>

      {/* Footer */}
    </div>
  );
}
