"use client"

import { useGSAP } from "@gsap/react"
import { ArrowUpIcon, TranslateIcon } from "@phosphor-icons/react"
import gsap from "gsap"
import { useRouter } from "next/navigation"
import { useRef, useState } from "react"

import { landing } from "@/content/landing"
import { sentence } from "@/lib/format"

export function Hero() {
  const router = useRouter()
  const [q, setQ] = useState("")
  const root = useRef<HTMLElement>(null)

  useGSAP(
    () => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        gsap.set("[data-hero]", { opacity: 1 })
        return
      }
      gsap.fromTo(
        "[data-hero]",
        { opacity: 0, y: 18, filter: "blur(6px)" },
        {
          opacity: 1,
          y: 0,
          filter: "blur(0px)",
          duration: 0.9,
          ease: "power3.out",
          stagger: 0.09,
          delay: 0.05,
        }
      )
    },
    { scope: root }
  )

  const go = (text: string) => {
    const t = text.trim()
    if (t) router.push(`/app/check?q=${encodeURIComponent(t)}`)
  }

  return (
    <section
      ref={root}
      id="product"
      className="relative overflow-hidden px-6 pt-36 pb-24 text-center md:pt-44 md:pb-32"
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[760px] glow-top" />
      <div className="relative mx-auto flex max-w-[860px] flex-col items-center">
        <div
          data-hero
          className="mb-8 inline-flex items-center gap-2 rounded-full py-1 pr-3.5 pl-1 text-[12.5px] font-medium text-ink-2 opacity-0 glass"
        >
          <span className="rounded-full bg-klein-soft px-2 py-0.5 text-[10px] font-bold tracking-wide text-klein uppercase">
            New
          </span>
          Big Billion Days phone reviews, checked
        </div>

        <h1
          data-hero
          className="text-[40px] leading-[1.06] font-normal tracking-[-0.035em] text-ink opacity-0 md:text-[64px]"
        >
          Every review says &ldquo;buy this&rdquo;.
          <br />
          <span className="font-semibold text-[#020617]">
            See who got paid to say it.
          </span>
        </h1>

        <p
          data-hero
          className="mt-6 max-w-[600px] text-[15.5px] leading-relaxed text-muted-foreground opacity-0 md:text-[17px]"
        >
          Unpaid goes through every recent YouTube review of what you want to
          buy, from phones to earbuds to laptops. It shows who was sponsored by
          the brand, sent it for free, or earns a cut when you buy, with the
          exact words they used. Then it tells you what the reviewers with
          nothing to disclose recommend.
        </p>

        <form
          data-hero
          onSubmit={(e) => {
            e.preventDefault()
            go(q)
          }}
          className="mt-10 w-full max-w-[640px] rounded-[26px] bg-white p-2 text-left opacity-0 shadow-[0_0_0_1px_rgb(15_23_42/0.08),0_18px_45px_-12px_rgb(15_23_42/0.1)] transition-shadow focus-within:shadow-[0_0_0_1px_rgb(0_47_167/0.25),0_22px_55px_-10px_rgb(0_47_167/0.16)]"
        >
          <label htmlFor="ask" className="sr-only">
            What do you want to buy?
          </label>
          <textarea
            id="ask"
            rows={2}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                go(q)
              }
            }}
            placeholder="What do you want to buy? e.g. best phone under ₹30k for camera and battery"
            className="h-[92px] w-full resize-none border-0 bg-transparent px-4 pt-3 pb-2 text-[15px] text-ink placeholder:text-faint focus:outline-none sm:h-auto"
          />
          <div className="flex items-center justify-between rounded-[20px] bg-soft px-3 py-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-[12px] font-medium text-ink-2 shadow-[0_0_0_1px_rgb(15_23_42/0.07)]">
              <TranslateIcon weight="duotone" className="size-4 text-klein" />
              Reviews in Hindi, English, Telugu and Malayalam
            </span>
            <button
              type="submit"
              aria-label="Check reviews"
              disabled={!q.trim()}
              className="grid size-8 place-items-center rounded-full text-white gloss-dark transition-opacity disabled:opacity-40"
            >
              <ArrowUpIcon weight="bold" className="size-4" />
            </button>
          </div>
        </form>

        <div
          data-hero
          className="mt-5 flex flex-wrap items-center justify-center gap-2 text-[12.5px] opacity-0"
        >
          <span className="text-faint">Or open a real report:</span>
          {landing.reports.map((r) => (
            <button
              key={r.id}
              type="button"
              onClick={() => router.push(`/app/r/${r.id}`)}
              className="rounded-full bg-white/70 px-3 py-1 font-medium text-ink-2 shadow-[0_0_0_1px_rgb(15_23_42/0.08)] transition-colors hover:bg-white"
            >
              {sentence(r.question)}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
