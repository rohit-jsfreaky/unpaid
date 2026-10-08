"use client"

import Link from "next/link"
import { useEffect, useState } from "react"

import { Logo } from "@/components/logo"
import { cn } from "@/lib/utils"

const LINKS = [
  { href: "#product", label: "Product" },
  { href: "#how", label: "How it works" },
  { href: "#study", label: "What we found" },
  { href: "#faq", label: "FAQ" },
]

/** A floating glass bar that tightens once the page scrolls. */
export function Nav() {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12)
    onScroll()
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  return (
    <header className="fixed inset-x-0 top-0 z-50 flex justify-center px-4 pt-3">
      <div
        className={cn(
          "flex h-14 w-full items-center justify-between rounded-full border border-white/70 pr-2 pl-5 backdrop-blur-xl backdrop-saturate-150 transition-all duration-500",
          scrolled
            ? "max-w-[920px] bg-white/70 shadow-[inset_0_1px_0_rgb(255_255_255/0.95),0_0_0_1px_rgb(15_23_42/0.06),0_12px_32px_-12px_rgb(15_23_42/0.16)]"
            : "max-w-[1100px] bg-white/45 shadow-[inset_0_1px_0_rgb(255_255_255/0.9),0_0_0_1px_rgb(15_23_42/0.04)]"
        )}
      >
        <Logo />
        <nav className="hidden items-center gap-1 text-[13.5px] font-medium text-muted-foreground md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="rounded-full px-3.5 py-1.5 transition-colors hover:bg-white/80 hover:text-ink"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <Link
          href="/app"
          className="inline-flex h-9 items-center rounded-full px-4 text-[13px] font-medium tracking-tight text-white gloss-dark transition-transform hover:-translate-y-px"
        >
          Open Unpaid
        </Link>
      </div>
    </header>
  )
}
