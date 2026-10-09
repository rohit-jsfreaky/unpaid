"use client"

import {
  CalendarBlankIcon,
  ChatCircleDotsIcon,
  CoinsIcon,
  CurrencyInrIcon,
  FileTextIcon,
  LinkSimpleIcon,
  ListChecksIcon,
  MagnifyingGlassIcon,
  StorefrontIcon,
  TagIcon,
  VideoCameraIcon,
} from "@phosphor-icons/react"
import Link from "next/link"
import { useEffect, useState } from "react"

import { AskBox } from "@/components/app/ask-box"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { day, sentence } from "@/lib/format"
import type { ReportCard } from "@/lib/types"

const STEPS = [
  {
    icon: ChatCircleDotsIcon,
    title: "We read your question",
    body: "What you're buying, your budget, the sale, what matters to you.",
  },
  {
    icon: MagnifyingGlassIcon,
    title: "We find the reviews",
    body: "Every review posted in the last three weeks, in English and Hindi search.",
  },
  {
    icon: VideoCameraIcon,
    title: "We go through each one",
    body: "The description and what was said in the video, in its own language.",
  },
  {
    icon: LinkSimpleIcon,
    title: "We open the shop links",
    body: "To see which links pay the reviewer when you buy.",
  },
  {
    icon: CoinsIcon,
    title: "We label the money ties",
    body: "Only with the reviewer's own words as proof.",
  },
  {
    icon: StorefrontIcon,
    title: "We check today's prices",
    body: "For the products the reviewers agree on.",
  },
]

const TIPS = [
  {
    icon: TagIcon,
    text: "Name what you're buying: a phone, earbuds, a laptop, a mixer grinder.",
  },
  {
    icon: CurrencyInrIcon,
    text: "Add your budget, like under ₹30,000 or under 30k.",
  },
  {
    icon: ListChecksIcon,
    text: "Say what matters: camera, battery, bass, noise.",
  },
  {
    icon: CalendarBlankIcon,
    text: "Mention the sale if there is one: Big Billion Days.",
  },
]

export function NewCheck() {
  const [reports, setReports] = useState<ReportCard[] | null>(null)
  useEffect(() => {
    api
      .reports()
      .then(setReports)
      .catch(() => setReports([]))
  }, [])

  return (
    <div className="grid grid-cols-1 items-start gap-6 pt-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
      <div className="flex min-w-0 flex-col gap-6">
        <div>
          <h1 className="text-[28px] leading-tight font-medium tracking-[-0.025em] text-ink md:text-[34px]">
            Start a new check
          </h1>
          <p className="mt-2 text-[15px] text-muted-foreground">
            Ask the way you would ask a friend. We&apos;ll do the watching.
          </p>
        </div>
        <AskBox examples={reports?.map((r) => sentence(r.question))} />
        <Card>
          <CardHeader>
            <CardTitle>What happens next</CardTitle>
            <CardDescription>
              It takes about a minute. You can watch each step as it happens.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {STEPS.map((s, i) => (
                <li
                  key={s.title}
                  className="flex gap-3 rounded-xl bg-soft p-3.5"
                >
                  <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-white text-klein shadow-[0_0_0_1px_rgb(15_23_42/0.06)]">
                    <s.icon weight="duotone" className="size-4" />
                  </span>
                  <div className="min-w-0">
                    <p className="text-[13px] font-medium text-ink">
                      <span className="mr-1.5 font-mono text-[11px] text-faint tnum">
                        0{i + 1}
                      </span>
                      {s.title}
                    </p>
                    <p className="mt-0.5 text-[12.5px] leading-relaxed text-muted-foreground">
                      {s.body}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Ask a good question</CardTitle>
            <CardDescription>
              The more you say, the closer the reviews match.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {TIPS.map((t) => (
              <div
                key={t.text}
                className="flex items-start gap-2.5 text-[13px] leading-relaxed text-ink-2"
              >
                <t.icon
                  weight="duotone"
                  className="mt-0.5 size-4 shrink-0 text-klein"
                />
                {t.text}
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Recent reports</CardTitle>
            <CardDescription>Open one to see a finished check.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {reports === null ? (
              <Skeleton className="h-14" />
            ) : reports.length ? (
              reports.slice(0, 4).map((r) => (
                <Link
                  key={r.id}
                  href={`/app/r/${r.id}`}
                  className="flex items-start gap-3 rounded-xl bg-soft p-3 transition-colors hover:bg-mist"
                >
                  <FileTextIcon
                    weight="duotone"
                    className="mt-0.5 size-4 shrink-0 text-klein"
                  />
                  <div className="min-w-0">
                    <p className="line-clamp-2 text-[13px] font-medium text-ink">
                      {sentence(r.question)}
                    </p>
                    <p className="mt-0.5 text-[12px] text-muted-foreground">
                      {day(r.checked_at)} · {r.reviews} reviews ·{" "}
                      {r.with_money_ties} money ties
                    </p>
                  </div>
                </Link>
              ))
            ) : (
              <p className="text-[13px] text-muted-foreground">
                Your reports will show up here.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
