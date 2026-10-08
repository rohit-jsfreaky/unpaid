"use client"

import { PlayCircleIcon, QuotesIcon } from "@phosphor-icons/react"

import { Dot } from "@/components/label-chip"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { areaMeta } from "@/lib/areas"
import { rupees } from "@/lib/format"
import type { AreaBoard, PhonePrices, Report } from "@/lib/types"

/** One card per thing the shopper said matters: the phone reviewers with nothing to disclose praise most for it. */
export function FocusCards({
  report,
  priceOf,
}: {
  report: Report
  priceOf: (phone: string) => PhonePrices | undefined
}) {
  const focus = report.areas.filter((a) => a.focus)
  if (!focus.length) return null
  const english = new Set(
    report.reviews.filter((r) => r.language === "latin").map((r) => r.video_id)
  )
  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-[17px] font-medium tracking-tight text-ink">
          What you asked for
        </h2>
        <p className="text-[12.5px] text-muted-foreground">
          What reviewers praise for{" "}
          {focus
            .map((a) => areaMeta(a.area, a.name).name.toLowerCase())
            .join(" and ")}
          , in their own words
        </p>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {focus.map((a) => (
          <FocusCard
            key={a.area}
            a={a}
            report={report}
            priceOf={priceOf}
            english={english}
          />
        ))}
      </div>
    </section>
  )
}

function FocusCard({
  a,
  report,
  priceOf,
  english,
}: {
  a: AreaBoard
  report: Report
  priceOf: (phone: string) => PhonePrices | undefined
  english: Set<string>
}) {
  const meta = areaMeta(a.area, a.name)
  const nd = report.board.no_disclosure_videos_with_picks
  const ds = report.board.disclosed_videos_with_picks
  const best = a.phones.find((p) => p.name === a.best_no_disclosure)
  const quote =
    best?.mentions.find((m) => !m.disclosed && m.verdict === "good") ??
    best?.mentions[0]
  const low = best ? priceOf(best.name)?.offers[0] : undefined
  return (
    <Card className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-klein-mist to-transparent" />
      <CardHeader className="relative">
        <CardDescription className="flex items-center gap-1.5">
          <meta.icon weight="duotone" className="size-4 text-klein" /> Best for{" "}
          {meta.name.toLowerCase()}
          <Badge variant="secondary" className="ml-1">
            You asked for it
          </Badge>
        </CardDescription>
        <CardTitle className="text-[20px] leading-snug">
          {best?.name ?? "No clear pick"}
        </CardTitle>
      </CardHeader>
      <CardContent className="relative flex flex-col gap-4">
        {best ? (
          <p className="text-[13.5px] leading-relaxed text-ink-2">
            {best.good_no_disclosure} of {nd} reviewers with nothing to disclose{" "}
            {meta.praise}, and {best.good_disclosed} of {ds} with a money tie.
            {best.weak ? ` ${best.weak} call it weak.` : " None call it weak."}
          </p>
        ) : (
          <p className="text-[13.5px] text-muted-foreground">
            No reviewer with nothing to disclose gave an opinion on{" "}
            {meta.name.toLowerCase()}.
          </p>
        )}
        <div className="flex flex-col gap-2.5">
          {a.phones.slice(0, 3).map((p) => (
            <div key={p.key} className="flex flex-col gap-1">
              <div className="flex items-center justify-between gap-3 text-[12.5px]">
                <span className="truncate font-medium text-ink">{p.name}</span>
                <span className="shrink-0 font-mono text-[11.5px] text-muted-foreground tnum">
                  {p.good_no_disclosure}/{nd} · {p.good_disclosed}/{ds}
                </span>
              </div>
              <div className="flex gap-1">
                <Bar n={p.good_no_disclosure} of={nd} k="none" />
                <Bar n={p.good_disclosed} of={ds} k="commission" />
              </div>
            </div>
          ))}
          <div className="flex items-center gap-4 pt-1 text-[11.5px] text-muted-foreground">
            <span className="flex items-center gap-1.5">
              <Dot k="none" /> No disclosure found
            </span>
            <span className="flex items-center gap-1.5">
              <Dot k="commission" /> Has a money tie
            </span>
          </div>
        </div>
        {quote ? (
          <figure className="rounded-xl bg-soft p-3.5 shadow-[0_0_0_1px_rgb(15_23_42/0.05)]">
            <QuotesIcon weight="fill" className="size-3.5 text-faint" />
            <blockquote className="mt-1.5 text-[13.5px] leading-relaxed text-ink">
              {quote.quote}
            </blockquote>
            {!english.has(quote.video_id) ? (
              <p className="mt-1.5 text-[12px] leading-relaxed text-muted-foreground">
                <span className="font-medium text-ink-2">In English: </span>
                {quote.meaning_en}
              </p>
            ) : null}
            <figcaption className="mt-2 flex flex-wrap items-center justify-between gap-2 text-[12px] text-muted-foreground">
              <span>{quote.channel}</span>
              {quote.time_text ? (
                <a
                  href={quote.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 font-medium text-klein hover:underline"
                >
                  <PlayCircleIcon weight="fill" className="size-3.5" /> Watch at{" "}
                  {quote.time_text}
                </a>
              ) : null}
            </figcaption>
          </figure>
        ) : null}
      </CardContent>
      <CardFooter className="relative justify-between text-[12.5px]">
        <span className="text-muted-foreground">Lowest price today</span>
        <span className="text-[15px] font-medium text-ink tnum">
          {low ? `${rupees(low.price)} · ${low.seller}` : "Not checked"}
        </span>
      </CardFooter>
    </Card>
  )
}

function Bar({
  n,
  of,
  k,
}: {
  n: number
  of: number
  k: "none" | "commission"
}) {
  return (
    <span className="h-2 flex-1 overflow-hidden rounded-full bg-mist">
      <span
        className="block h-full rounded-full"
        style={{
          width: `${of ? (n / of) * 100 : 0}%`,
          background: `var(--label-${k})`,
        }}
      />
    </span>
  )
}
