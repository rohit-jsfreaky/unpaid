"use client"

import { useGSAP } from "@gsap/react"
import gsap from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import Lenis from "lenis"
import { useEffect, useRef, type ReactNode } from "react"

gsap.registerPlugin(ScrollTrigger, useGSAP)

/** Lenis smooth scrolling, driven by GSAP's ticker so ScrollTrigger stays in step. */
export function SmoothScroll({ children }: { children: ReactNode }) {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return
    const lenis = new Lenis({ duration: 1.1, smoothWheel: true })
    lenis.on("scroll", ScrollTrigger.update)
    const tick = (time: number) => lenis.raf(time * 1000)
    gsap.ticker.add(tick)
    gsap.ticker.lagSmoothing(0)

    // In-page anchors scroll with Lenis too, offset for the floating navbar.
    const onClick = (e: MouseEvent) => {
      const a = (e.target as HTMLElement).closest<HTMLAnchorElement>(
        'a[href^="#"]'
      )
      if (!a) return
      const target = document.querySelector(a.getAttribute("href") || "")
      if (!target) return
      e.preventDefault()
      lenis.scrollTo(target as HTMLElement, { offset: -88 })
    }
    document.addEventListener("click", onClick)
    return () => {
      document.removeEventListener("click", onClick)
      gsap.ticker.remove(tick)
      lenis.destroy()
    }
  }, [])
  return <>{children}</>
}

/** Fades every [data-reveal] child up into place as it scrolls into view. */
export function Reveal({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) {
  const root = useRef<HTMLDivElement>(null)
  useGSAP(
    () => {
      const items = gsap.utils.toArray<HTMLElement>("[data-reveal]")
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        gsap.set(items, { opacity: 1 })
        return
      }
      ScrollTrigger.batch(items, {
        start: "top 88%",
        once: true,
        onEnter: (batch) =>
          gsap.fromTo(
            batch,
            { opacity: 0, y: 22 },
            {
              opacity: 1,
              y: 0,
              duration: 0.8,
              ease: "power3.out",
              stagger: 0.08,
              overwrite: true,
            }
          ),
      })
    },
    { scope: root }
  )
  return (
    <div ref={root} className={className}>
      {children}
    </div>
  )
}
