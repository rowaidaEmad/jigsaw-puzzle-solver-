'use client';

import { Button } from '@/components/ui/button';
import Image from 'next/image';
import Link from 'next/link';
import { useState } from 'react';

const examples = [
  {
    title: '2×2 Puzzle',
    description: '4 pieces - Perfect for testing basic algorithms',
    variants: ['2x2_a', '2x2_b'],
  },
  {
    title: '4×4 Puzzle',
    description: '16 pieces - Medium complexity with clear features',
    variants: ['4x4_a', '4x4_b', '4x4_c'],
  },
  {
    title: '8×8 Puzzle',
    description: '64 pieces - High complexity, maximum challenge',
    variants: ['8x8_a', '8x8_b', '8x8_c'],
  },
];

const steps = [
  { id: 1, name: 'Original', desc: 'Raw puzzle tile' },
  { id: 2, name: 'Upscaled', desc: 'Lanczos interpolation + sharpening' },
  { id: 3, name: 'Binary', desc: 'Adaptive threshold + morphology' },
  { id: 4, name: 'Edges', desc: 'Canny edge detection' },
  { id: 5, name: 'Contours', desc: 'Shape extraction' },
];

export default function ExamplesPage() {
  const [selectedVariant, setSelectedVariant] = useState<{ [key: string]: number }>({
    '2×2 Puzzle': 0,
    '4×4 Puzzle': 0,
    '8×8 Puzzle': 0,
  });

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      {/* Header */}
      <header className="border-b border-slate-200 dark:border-slate-800">
        <div className="container mx-auto px-6 py-4 max-w-7xl flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3">
            <Image src="/icon-96.svg" alt="Logo" width={40} height={40} className="dark:invert" />
            <span className="text-xl font-bold text-black dark:text-white">Puzzle Solver</span>
          </Link>

          <Link href="/">
            <Button variant="ghost" size="sm">
              ← Back to Home
            </Button>
          </Link>
        </div>
      </header>

      <main className="container mx-auto px-6 py-16 max-w-7xl">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold text-black dark:text-white mb-4">Processing Examples</h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
            Real preprocessing results across different puzzle sizes and complexities
          </p>
        </div>

        {/* Processing Steps Legend */}
        <div className="mb-16 p-6 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800">
          <h2 className="text-lg font-semibold text-black dark:text-white mb-4">Pipeline Steps</h2>
          <div className="grid md:grid-cols-5 gap-4">
            {steps.map((step) => (
              <div key={step.id} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-[#5185A1] text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                  {step.id}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-black dark:text-white">{step.name}</h3>
                  <p className="text-xs text-slate-600 dark:text-slate-400">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Examples */}
        <div className="space-y-16">
          {examples.map((example, idx) => {
            const currentVariant = selectedVariant[example.title] || 0;
            const variantName = example.variants[currentVariant];

            return (
              <div key={example.title} className="space-y-6">
                {/* Title and Variant Selector */}
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-3xl font-bold text-black dark:text-white">{example.title}</h2>
                    <p className="text-slate-600 dark:text-slate-400">{example.description}</p>
                  </div>

                  {example.variants.length > 1 && (
                    <div className="flex gap-2">
                      {example.variants.map((_, variantIdx) => (
                        <Button
                          key={variantIdx}
                          size="sm"
                          variant={currentVariant === variantIdx ? 'default' : 'outline'}
                          onClick={() =>
                            setSelectedVariant({
                              ...selectedVariant,
                              [example.title]: variantIdx,
                            })
                          }
                          className={
                            currentVariant === variantIdx
                              ? 'bg-[#5185A1] hover:bg-[#417490] text-white'
                              : 'border-slate-300 dark:border-slate-700'
                          }
                        >
                          Example {variantIdx + 1}
                        </Button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Images Grid */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {steps.map((step) => (
                    <div key={step.id} className="group">
                      <div className="aspect-square rounded-lg overflow-hidden border-2 border-slate-200 dark:border-slate-800 hover:border-[#5185A1] transition mb-3">
                        <Image
                          src={`/examples/${variantName}_${step.id}_${step.name.toLowerCase()}.jpg`}
                          alt={`${example.title} - ${step.name}`}
                          width={300}
                          height={300}
                          className="w-full h-full object-cover group-hover:scale-105 transition"
                        />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-semibold text-black dark:text-white">{step.name}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-500">{step.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* CTA */}
        <div className="mt-20 text-center p-12 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
          <h2 className="text-3xl font-bold text-black dark:text-white mb-4">Ready to try it yourself?</h2>
          <p className="text-slate-600 dark:text-slate-400 mb-6">
            Upload your own puzzle image and see the preprocessing in action
          </p>
          <Button size="lg" className="bg-[#5185A1] hover:bg-[#417490] text-white">
            Try It Now (Coming Soon)
          </Button>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-800 mt-20">
        <div className="container mx-auto px-6 py-8 max-w-7xl text-center">
          <div className="text-sm text-slate-600 dark:text-slate-400">Built with awesomeness</div>
        </div>
      </footer>
    </div>
  );
}
