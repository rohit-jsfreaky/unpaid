import { Hero } from "@/components/landing/hero"
import { Nav } from "@/components/landing/nav"
import {
  Cards,
  Closing,
  Faq,
  Features,
  Footer,
  Labels,
  Study,
} from "@/components/landing/sections"
import { Reveal, SmoothScroll } from "@/components/motion"

export default function Home() {
  return (
    <SmoothScroll>
      <Nav />
      <main className="relative overflow-x-hidden">
        <Hero />
        <Reveal>
          <Features />
          <Cards />
          <Study />
          <Labels />
          <Faq />
          <Closing />
        </Reveal>
      </main>
      <Footer />
    </SmoothScroll>
  )
}
