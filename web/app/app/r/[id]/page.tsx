"use client"

import {
  ArrowRightIcon,
  CoinsIcon,
  SealCheckIcon,
  TagIcon,
  TrophyIcon,
  VideoCameraIcon,
} from "@phosphor-icons/react"
import Link from "next/link"
import { useState } from "react"

import { LabelBars, PicksChart, TimelineChart } from "@/components/app/charts"
import { FocusCards } from "@/components/app/focus-cards"
import { useReport } from "@/components/app/report-context"
import { Proof, ReviewSheet } from "@/components/app/review-sheet"
import { Dot } from "@/components/label-chip"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { language, pct, rupees } from "@/lib/format"
import { productWords } from "@/lib/product"
import type { Review, Video } from "@/lib/types"

function Kpi({
  icon: Icon,
  label,
  value,
  note,
}: {
  icon: typeof CoinsIcon
  label: string
  value: React.ReactNode
  note: React.ReactNode
}) {
  return (
    <Card className="gap-3">
      <CardHeader>
        <CardDescription className="flex items-center gap-1.5">
          <Icon weight="duotone" className="size-4 text-klein" /> {label}
        </CardDescription>
        <CardTitle className="text-[26px] leading-tight font-medium tracking-tight tnum">
          {value}
        </CardTitle>
      </CardHeader>
      <CardContent className="text-[12.5px] leading-relaxed text-muted-foreground">
        {note}
      </CardContent>
    </Card>
  )
}

export default function Overview() {
  const state = useReport()
  const [open, setOpen] = useState<{ video: Video; review: Review } | null>(
    null
  )
  if (state.status !== "ready") return null
  const { report, rows, withTies, priceOf } = state
  const b = report.board
  const top = b.phones[0]
  const topPrice = top ? priceOf(top.name)?.offers[0] : undefined
  const sellers = top ? (priceOf(top.name)?.offers.length ?? 0) : 0
  const langs = Object.entries(
    rows.reduce<Record<string, number>>((acc, r) => {
      const k = language(r.review.has_transcript ? r.review.language : null)
      acc[k] = (acc[k] ?? 0) + 1
      return acc
    }, {})
  ).sort((a, b) => b[1] - a[1])
  const holds = top ? top.share_no_disclosure >= 0.5 : false
  const spoken = withTies.flatMap((v) =>
    v.labels.filter((e) => e.source === "transcript").map((e) => ({ v, e }))
  )
  const written = withTies.flatMap((v) =>
    v.labels.filter((e) => e.source !== "transcript").map((e) => ({ v, e }))
  )
  const proofs = [...spoken, ...written].slice(0, 4)
  const rowOf = (v: Video) =>
    rows.find((r) => r.video.video_id === v.video_id) ?? null

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi
          icon={VideoCameraIcon}
          label="Reviews checked"
          value={report.videos.length}
          note={`Posted in the last 3 weeks, out of ${report.videos_found} videos found.`}
        />
        <Kpi
          icon={CoinsIcon}
          label="With a money tie"
          value={
            <>
              {withTies.length}{" "}
              <span className="text-[15px] text-muted-foreground">
                ({pct(withTies.length / report.videos.length)})
              </span>
            </>
          }
          note="Sponsored, sent a free unit, or earning commission when you buy."
        />
        <Kpi
          icon={TrophyIcon}
          label="Most recommended"
          value={<span className="text-[20px]">{top?.name ?? "—"}</span>}
          note={
            top
              ? `Picked in ${top.all} of ${b.videos_with_picks} reviews with a list.`
              : "No lists of picks found."
          }
        />
        <Kpi
          icon={TagIcon}
          label="Lowest price today"
          value={rupees(topPrice?.price)}
          note={
            topPrice
              ? `${top?.name} at ${topPrice.seller}, ${sellers} ${sellers === 1 ? "seller" : "sellers"} checked.`
              : "No listing found today."
          }
        />
      </div>

      <FocusCards report={report} priceOf={priceOf} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>What the reviewers disclosed</CardTitle>
            <CardDescription>
              Reviews carrying each label. One review can carry more than one.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <LabelBars videos={report.videos} />
          </CardContent>
          <CardFooter className="justify-between text-[12.5px] text-muted-foreground">
            <span>Every label comes with the reviewer&apos;s own words.</span>
            <Link
              href={`/app/r/${report.id}/reviews`}
              className="font-medium text-klein hover:underline"
            >
              See the proof
            </Link>
          </CardFooter>
        </Card>

        <Card className="relative overflow-hidden lg:col-span-2">
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-klein-mist to-transparent" />
          <CardHeader className="relative">
            <CardDescription className="flex items-center gap-1.5">
              <SealCheckIcon weight="duotone" className="size-4 text-klein" />{" "}
              The favourite, checked
            </CardDescription>
            <CardTitle className="text-[20px] leading-snug">
              {top
                ? holds
                  ? `${top.name} holds up`
                  : `${top.name} leans on paid reviewers`
                : "No favourite yet"}
            </CardTitle>
          </CardHeader>
          {top ? (
            <CardContent className="relative flex flex-col gap-4">
              <p className="text-[13.5px] leading-relaxed text-ink-2">
                {top.no_disclosure} of {b.no_disclosure_videos_with_picks}{" "}
                reviewers with nothing to disclose pick it, and {top.disclosed}{" "}
                of {b.disclosed_videos_with_picks} with a money tie.
              </p>
              <div className="flex flex-col gap-2">
                <Share
                  k="none"
                  label="No disclosure found"
                  n={top.no_disclosure}
                  of={b.no_disclosure_videos_with_picks}
                />
                <Share
                  k="commission"
                  label="Has a money tie"
                  n={top.disclosed}
                  of={b.disclosed_videos_with_picks}
                />
              </div>
              <div className="flex items-end justify-between rounded-xl bg-white p-4 shadow-[0_0_0_1px_rgb(15_23_42/0.07)]">
                <div>
                  <p className="text-[12px] text-muted-foreground">
                    Lowest price today
                  </p>
                  <p className="text-[24px] font-medium tracking-tight text-ink tnum">
                    {rupees(topPrice?.price)}
                  </p>
                  <p className="text-[12px] text-muted-foreground">
                    {topPrice?.seller}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  nativeButton={false}
                  render={<Link href={`/app/r/${report.id}/prices`} />}
                >
                  All prices <ArrowRightIcon data-icon="inline-end" />
                </Button>
              </div>
            </CardContent>
          ) : null}
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Who recommends what</CardTitle>
          <CardDescription>
            Share of reviewers who pick each one: the{" "}
            {b.no_disclosure_videos_with_picks} with nothing to disclose vs the{" "}
            {b.disclosed_videos_with_picks} with a money tie.
          </CardDescription>
          <CardAction>
            <Button
              variant="ghost"
              size="sm"
              nativeButton={false}
              render={<Link href={`/app/r/${report.id}/products`} />}
            >
              All {productWords(report.product).many}{" "}
              <ArrowRightIcon data-icon="inline-end" />
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent>
          <PicksChart board={b} limit={8} />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>When the reviews came out</CardTitle>
            <CardDescription>
              Each dot is a review: the day it was posted and how many watched
              it.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TimelineChart rows={rows} />
          </CardContent>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Spoken in</CardTitle>
            <CardDescription>
              We go through what was said, in the reviewer&apos;s own language.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {langs.map(([k, n]) => (
              <div
                key={k}
                className="flex items-center justify-between rounded-lg bg-soft px-3 py-2.5 text-[13px]"
              >
                <span className="text-ink-2">{k}</span>
                <span className="font-mono text-[12px] text-ink tnum">
                  {n} review{n === 1 ? "" : "s"}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {proofs.length ? (
        <Card>
          <CardHeader>
            <CardTitle>The proof, in their words</CardTitle>
            <CardDescription>
              A few of the money ties we found. Open a review to see all of
              them.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {proofs.map(({ v, e }, i) => {
              const row = rowOf(v)
              return (
                <button
                  key={i}
                  type="button"
                  className="text-left"
                  onClick={() => row && setOpen(row)}
                >
                  <p className="mb-1.5 text-[12.5px] font-medium text-ink-2">
                    {v.channel}
                  </p>
                  <Proof e={e} english={row?.review.language === "latin"} />
                </button>
              )
            })}
          </CardContent>
        </Card>
      ) : null}

      <ReviewSheet row={open} onOpenChange={(o) => !o && setOpen(null)} />
    </div>
  )
}

function Share({
  k,
  label,
  n,
  of,
}: {
  k: "none" | "commission"
  label: string
  n: number
  of: number
}) {
  return (
    <div className="flex items-center gap-3 text-[12.5px]">
      <span className="flex w-40 shrink-0 items-center gap-2 text-ink-2">
        <Dot k={k} /> {label}
      </span>
      <span className="h-2 flex-1 overflow-hidden rounded-full bg-white shadow-[0_0_0_1px_rgb(15_23_42/0.06)]">
        <span
          className="block h-full rounded-full"
          style={{
            width: `${of ? (n / of) * 100 : 0}%`,
            background: `var(--label-${k})`,
          }}
        />
      </span>
      <span className="w-10 text-right font-mono text-[11.5px] text-ink tnum">
        {n}/{of}
      </span>
    </div>
  )
}
