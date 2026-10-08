"use client"

import {
  ArrowRightIcon,
  ChatTextIcon,
  CoinsIcon,
  FileTextIcon,
  LinkSimpleIcon,
  StorefrontIcon,
  TrophyIcon,
  VideoCameraIcon,
} from "@phosphor-icons/react"
import Link from "next/link"
import { useEffect, useState } from "react"

import { LabelBars } from "@/components/app/charts"
import { AskBox } from "@/components/app/ask-box"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { api, explain } from "@/lib/api"
import { day, rupees, sentence } from "@/lib/format"
import type { Report, ReportCard } from "@/lib/types"

const CHECKS = [
  {
    icon: CoinsIcon,
    title: "Who's paid",
    body: "Brand deals, free units and commission links, for every recent review.",
  },
  {
    icon: ChatTextIcon,
    title: "In their own words",
    body: "The exact sentence behind every label, with a link to the second it was said.",
  },
  {
    icon: LinkSimpleIcon,
    title: "Links that pay them",
    body: "We open the shop links under each video to see which ones pay the reviewer.",
  },
  {
    icon: StorefrontIcon,
    title: "Today's price",
    body: "The lowest price for what reviewers agree on, from every shop that lists it.",
  },
]

export default function Home() {
  const [reports, setReports] = useState<ReportCard[] | null>(null)
  const [latest, setLatest] = useState<Report | null>(null)
  const [error, setError] = useState<{ title: string; body: string } | null>(
    null
  )
  useEffect(() => {
    api
      .reports()
      .then((rs) => {
        setReports(rs)
        if (rs[0]) api.report(rs[0].id).then((r) => setLatest(r.report))
      })
      .catch((e) => setError(explain(e)))
  }, [])

  return (
    <div className="flex flex-col gap-8 pt-4 md:gap-10 md:pt-6">
      <section className="grid grid-cols-1 items-start gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        <div className="min-w-0">
          <h1 className="text-[28px] leading-tight font-medium tracking-[-0.025em] text-ink md:text-[38px]">
            What are you buying next?
          </h1>
          <p className="mt-2 text-[15px] text-muted-foreground">
            We&apos;ll go through the reviews, show who&apos;s paid, and what
            the rest recommend.
          </p>
          <div className="mt-6">
            <AskBox />
          </div>
        </div>
        <LatestCard
          report={latest}
          card={reports?.[0] ?? null}
          loading={reports === null && !error}
        />
      </section>

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {CHECKS.map((c) => (
          <div
            key={c.title}
            className="flex gap-3 rounded-2xl bg-white/70 p-4 shadow-[0_0_0_1px_rgb(15_23_42/0.06)]"
          >
            <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-klein-mist text-klein">
              <c.icon weight="duotone" className="size-4.5" />
            </span>
            <div>
              <p className="text-[13.5px] font-medium text-ink">{c.title}</p>
              <p className="mt-0.5 text-[12.5px] leading-relaxed text-muted-foreground">
                {c.body}
              </p>
            </div>
          </div>
        ))}
      </section>

      <section>
        <div className="mb-4 flex items-end justify-between gap-3">
          <h2 className="text-[17px] font-medium tracking-tight text-ink">
            Your reports
          </h2>
          <Button
            variant="outline"
            size="sm"
            nativeButton={false}
            render={<Link href="/app/check" />}
          >
            New check
          </Button>
        </div>
        {error ? (
          <Empty className="rounded-2xl bg-white ring-1 ring-foreground/10">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <FileTextIcon weight="duotone" />
              </EmptyMedia>
              <EmptyTitle>{error.title}</EmptyTitle>
              <EmptyDescription>{error.body}</EmptyDescription>
            </EmptyHeader>
          </Empty>
        ) : reports === null ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 3 }, (_, i) => (
              <Skeleton key={i} className="h-56 rounded-2xl" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
            {reports.map((r) => (
              <ReportTile key={r.id} r={r} />
            ))}
            <Link href="/app/check" className="group">
              <div className="flex h-full min-h-56 flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-line bg-white/40 p-6 text-center transition-colors group-hover:bg-white">
                <span className="grid size-10 place-items-center rounded-full bg-klein-mist text-klein">
                  <ArrowRightIcon weight="bold" className="size-4" />
                </span>
                <p className="text-[14px] font-medium text-ink">
                  Check something new
                </p>
                <p className="max-w-56 text-[12.5px] text-muted-foreground">
                  Earbuds, laptops, a TV for the sale. Ask in your own words.
                </p>
              </div>
            </Link>
          </div>
        )}
      </section>
    </div>
  )
}

function LatestCard({
  report,
  card,
  loading,
}: {
  report: Report | null
  card: ReportCard | null
  loading: boolean
}) {
  if (loading || (card && !report))
    return <Skeleton className="h-[340px] rounded-2xl" />
  if (!card || !report) return null
  return (
    <Card className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-28 bg-gradient-to-b from-klein-mist to-transparent" />
      <CardHeader className="relative">
        <div className="flex flex-wrap items-center gap-2">
          {card.sample ? (
            <Badge variant="secondary">Sample report</Badge>
          ) : (
            <Badge variant="secondary">Latest report</Badge>
          )}
          <CardDescription>{day(card.checked_at)}</CardDescription>
        </div>
        <CardTitle className="text-[17px] leading-snug">
          {sentence(card.question)}
        </CardTitle>
      </CardHeader>
      <CardContent className="relative flex flex-col gap-5">
        <LabelBars videos={report.videos} />
        <div className="flex items-center justify-between gap-3 rounded-xl bg-soft p-3.5">
          <div className="min-w-0">
            <p className="flex items-center gap-1.5 text-[12px] text-muted-foreground">
              <TrophyIcon weight="duotone" className="size-3.5 text-klein" />{" "}
              Most recommended
            </p>
            <p className="truncate text-[14px] font-medium text-ink">
              {card.top_pick ?? "—"}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[12px] text-muted-foreground">Lowest today</p>
            <p className="text-[16px] font-medium text-ink tnum">
              {rupees(card.top_pick_price)}
            </p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="relative justify-between">
        <span className="text-[12.5px] text-muted-foreground">
          {card.reviews} reviews · {card.with_money_ties} with a money tie
        </span>
        <Button
          size="sm"
          nativeButton={false}
          render={<Link href={`/app/r/${card.id}`} />}
        >
          Open report <ArrowRightIcon data-icon="inline-end" />
        </Button>
      </CardFooter>
    </Card>
  )
}

function ReportTile({ r }: { r: ReportCard }) {
  return (
    <Link href={`/app/r/${r.id}`} className="group">
      <Card className="h-full transition-shadow group-hover:shadow-[0_18px_40px_-20px_rgb(15_23_42/0.25)]">
        <CardHeader>
          <div className="flex items-center gap-2">
            {r.sample ? <Badge variant="secondary">Sample report</Badge> : null}
            <CardDescription>{day(r.checked_at)}</CardDescription>
          </div>
          <CardTitle className="text-[16px] leading-snug">
            {sentence(r.question)}
          </CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-2">
          <Mini
            icon={VideoCameraIcon}
            value={String(r.reviews)}
            label="reviews"
          />
          <Mini
            icon={CoinsIcon}
            value={String(r.with_money_ties)}
            label="money ties"
          />
          <Mini
            icon={TrophyIcon}
            value={rupees(r.top_pick_price)}
            label="top pick"
          />
        </CardContent>
        <CardFooter className="justify-between text-[12.5px]">
          <span className="truncate text-muted-foreground">
            Top pick: {r.top_pick ?? "—"}
          </span>
          <span className="inline-flex shrink-0 items-center gap-1 font-medium text-klein">
            Open{" "}
            <ArrowRightIcon
              weight="bold"
              className="size-3.5 transition-transform group-hover:translate-x-0.5"
            />
          </span>
        </CardFooter>
      </Card>
    </Link>
  )
}

function Mini({
  icon: Icon,
  value,
  label,
}: {
  icon: typeof CoinsIcon
  value: string
  label: string
}) {
  return (
    <div className="min-w-0 rounded-xl bg-soft p-3">
      <Icon weight="duotone" className="size-4 text-klein" />
      <p className="mt-2 truncate text-[15px] font-medium text-ink tnum">
        {value}
      </p>
      <p className="text-[11.5px] text-muted-foreground">{label}</p>
    </div>
  )
}
