import type { Metadata } from 'next';
import { Geist_Mono, Bricolage_Grotesque } from 'next/font/google';
import './globals.css';

const bricolageGrotesque = Bricolage_Grotesque({
  variable: '--font-bricolage-grotesque',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Jigsaw Puzzle Solver',
  description: 'An awesome image processing application to solve jigsaw puzzles.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${bricolageGrotesque.variable}  ${geistMono.variable} font-sans antialiased`}>{children}</body>
    </html>
  );
}
