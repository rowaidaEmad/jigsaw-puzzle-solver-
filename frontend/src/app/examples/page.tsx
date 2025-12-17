'use client';

import { Button } from '@/components/ui/button';
import Image from 'next/image';
import { useState } from 'react';

const examples = [
  {
    title: '2×2 Puzzle',
    description: '4 pieces - Perfect for testing basic algorithms',
    variants: ['48'],
    imageId: 48,
    gridSize: '2x2',
  },
  {
    title: '8×8 Puzzle',
    description: '64 pieces - High complexity, maximum challenge',
    variants: ['67'],
    imageId: 67,
    gridSize: '8x8',
  },
];

const steps = [
  { id: 'prep', name: 'Preprocessed', desc: 'Enhanced image quality' },
  { id: 'upscaled', name: 'Upscaled', desc: 'Lanczos interpolation + sharpening' },
  { id: 'binary', name: 'Binary', desc: 'Adaptive threshold + morphology' },
  { id: 'edges', name: 'Edges', desc: 'Canny edge detection' },
  { id: 'contours', name: 'Contours', desc: 'Shape extraction' },
];

export default function ExamplesPage() {
  const [selectedVariant, setSelectedVariant] = useState<{ [key: string]: number }>({
    '2×2 Puzzle': 0,
    '8×8 Puzzle': 0,
  });

  const [selectedPiece, setSelectedPiece] = useState<{ [key: string]: number }>({
    '2×2 Puzzle': 0,
    '8×8 Puzzle': 0,
  });

  return (
    <div className="min-h-screen bg-white dark:bg-black">
      <main className="container mx-auto px-6 py-16 max-w-6xl">
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
            {steps.map((step, idx) => (
              <div key={step.id} className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                  {idx + 1}
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
            const currentPiece = selectedPiece[example.title] || 0;
            const imageId = example.imageId;
            const gridSize = example.gridSize === '2x2' ? 2 : 8;
            const totalPieces = gridSize * gridSize;
            const pieceRow = Math.floor(currentPiece / gridSize);
            const pieceCol = currentPiece % gridSize;

            return (
              <div key={example.title} className="space-y-6">
                {/* Title and Description */}
                <div className="flex flex-col gap-3">
                  <div>
                    <h2 className="text-3xl font-bold text-black dark:text-white">{example.title}</h2>
                    <p className="text-slate-600 dark:text-slate-400">{example.description}</p>
                    <p className="text-sm text-slate-500 dark:text-slate-500 mt-1">Image {imageId}</p>
                  </div>

                  {/* Piece Selector */}
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-black dark:text-white">Select Piece:</span>
                    <select
                      value={currentPiece}
                      onChange={e =>
                        setSelectedPiece({
                          ...selectedPiece,
                          [example.title]: parseInt(e.target.value),
                        })
                      }
                      className="px-3 py-1.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-black dark:text-white text-sm">
                      {Array.from({ length: totalPieces }, (_, i) => {
                        const row = Math.floor(i / gridSize);
                        const col = i % gridSize;
                        return (
                          <option key={i} value={i}>
                            Piece {i} (Row {row}, Col {col})
                          </option>
                        );
                      })}
                    </select>
                  </div>
                </div>

                {/* Input Image Section */}
                <div className="p-6 rounded-lg bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-800">
                  <h3 className="text-lg font-semibold text-black dark:text-white mb-4">Input</h3>
                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Full Puzzle */}
                    <div>
                      <div className="aspect-square rounded-lg overflow-hidden border-2 border-slate-200 dark:border-slate-800">
                        <Image
                          src={`/examples/${imageId}/input.png`}
                          alt={`${example.title} - Input`}
                          width={400}
                          height={400}
                          className="w-full h-full object-cover"
                          unoptimized
                        />
                      </div>
                      <p className="text-center text-sm text-slate-600 dark:text-slate-400 mt-2">
                        Full puzzle ({gridSize}×{gridSize} = {totalPieces} pieces)
                      </p>
                    </div>
                    {/* Selected Piece */}
                    <div>
                      <div className="aspect-square rounded-lg overflow-hidden border-2 border-primary">
                        <Image
                          src={`/examples/${imageId}/original/puzzle_${String(imageId).padStart(3, '0')}_r${pieceRow}_c${pieceCol}.png`}
                          alt={`Piece ${currentPiece}`}
                          width={400}
                          height={400}
                          className="w-full h-full object-cover"
                          unoptimized
                        />
                      </div>
                      <p className="text-center text-sm text-slate-600 dark:text-slate-400 mt-2">
                        Selected Piece {currentPiece} (Row {pieceRow}, Col {pieceCol})
                      </p>
                    </div>
                  </div>
                </div>

                {/* Processing Pipeline */}
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-black dark:text-white">Preprocessing Pipeline - Piece {currentPiece}</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                    {steps.map((step, stepIdx) => (
                      <div key={step.id} className="group">
                        <div className="aspect-square rounded-lg overflow-hidden border-2 border-slate-200 dark:border-slate-800 hover:border-primary transition mb-3">
                          <Image
                            src={`/examples/${imageId}/${step.id}/puzzle_${String(imageId).padStart(3, '0')}_r${pieceRow}_c${pieceCol}.png`}
                            alt={`${example.title} - ${step.name}`}
                            width={300}
                            height={300}
                            className="w-full h-full object-cover group-hover:scale-105 transition"
                            unoptimized
                          />
                        </div>
                        <div className="text-center">
                          <p className="text-sm font-semibold text-black dark:text-white">
                            {stepIdx + 1}. {step.name}
                          </p>
                          <p className="text-xs text-slate-500 dark:text-slate-500">{step.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Solved Result */}
                <div className="p-4 rounded-lg bg-primary/5 dark:bg-primary/10 border border-primary/20 dark:border-primary/30">
                  <h3 className="text-lg font-semibold text-black dark:text-white mb-4">Solved Result</h3>
                  <div className="flex justify-center">
                    <div className="max-w-md w-full">
                      <div className="aspect-square rounded-lg overflow-hidden border border-primary/30 dark:border-primary/40">
                        <Image
                          src={`/examples/${imageId}/solved/solution.png`}
                          alt={`${example.title} - Solved`}
                          width={400}
                          height={400}
                          className="w-full h-full object-cover"
                          unoptimized
                        />
                      </div>
                      <p className="text-center text-sm text-slate-600 dark:text-slate-400 mt-2 font-medium">
                        ✓ Successfully solved using genetic algorithm
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
