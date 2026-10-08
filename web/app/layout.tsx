import type { Metadata } from "next"
import {
  Geist_Mono,
  Instrument_Sans,
  Noto_Sans_Devanagari,
  Noto_Sans_Malayalam,
  Noto_Sans_Telugu,
} from "next/font/google"

import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/sonner"
import { TooltipProvider } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

const instrument = Instrument_Sans({
  subsets: ["latin"],
  variable: "--font-instrument",
})
const mono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" })
// Reviewers quoted in Hindi, Telugu and Malayalam: their own words, in their own script.
const deva = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  variable: "--font-deva",
  preload: false,
})
const telugu = Noto_Sans_Telugu({
  subsets: ["telugu"],
  variable: "--font-telugu",
  preload: false,
})
const malayalam = Noto_Sans_Malayalam({
  subsets: ["malayalam"],
  variable: "--font-malayalam",
  preload: false,
})

const TAGLINE =
  "Unpaid reads every recent YouTube review of what you want to buy, shows who was paid, sent a free unit or earns commission, and what the reviewers with nothing to disclose recommend."

export const metadata: Metadata = {
  title: {
    default: "Unpaid · See who got paid to recommend it",
    template: "%s · Unpaid",
  },
  description: TAGLINE,
  applicationName: "Unpaid",
  openGraph: {
    title: "Unpaid",
    description: TAGLINE,
    type: "website",
    siteName: "Unpaid",
  },
}

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={cn(
        "antialiased",
        instrument.variable,
        mono.variable,
        deva.variable,
        telugu.variable,
        malayalam.variable,
        "font-sans"
      )}
    >
      <body className="min-h-screen">
        {/* Light only: the charts' colours are checked against the light surface. */}
        <ThemeProvider forcedTheme="light" enableSystem={false}>
          <TooltipProvider>{children}</TooltipProvider>
          <Toaster position="bottom-right" />
        </ThemeProvider>
      </body>
    </html>
  )
}
