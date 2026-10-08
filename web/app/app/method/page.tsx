"use client"

import { CheckCircleIcon, InfoIcon, XCircleIcon } from "@phosphor-icons/react"
import { useEffect, useState } from "react"

import { Dot } from "@/components/label-chip"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { api } from "@/lib/api"
import { pct } from "@/lib/format"
import { BY_NAME, LABELS, NO_DISCLOSURE } from "@/lib/labels"
import type { Accuracy } from "@/lib/types"

const RULES = [
  {
    ok: true,
    text: "A label needs the reviewer's own words, found exactly as they wrote or said them, or YouTube's own label.",
  },
  {
    ok: true,
    text: "A shop link counts only if it really carries the reviewer's affiliate ID when you open it.",
  },
  {
    ok: true,
    text: "A sponsor has to be named in the same sentence. We don't guess who paid.",
  },
  {
    ok: false,
    text: "“This video is not sponsored” is shown as a note. It never becomes a label.",
  },
  {
    ok: false,
    text: "“For sponsorship enquiries, email me” is an invitation, not a sponsor. No label.",
  },
  {
    ok: false,
    text: "“All content on this channel is for education” is a disclaimer, not a free unit. No label.",
  },
]

export default function Method() {
  const [acc, setAcc] = useState<Accuracy | null>(null)
  useEffect(() => {
    api
      .accuracy()
      .then(setAcc)
      .catch(() => setAcc(null))
  }, [])
  const rows = acc?.scores.filter((s) => s.key || s.found) ?? []

  return (
    <div className="flex flex-col gap-6 pt-4">
      <div className="max-w-2xl">
        <h1 className="text-[28px] leading-tight font-medium tracking-[-0.02em] text-ink md:text-[34px]">
          How we label a review
        </h1>
        <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
          Unpaid shows what reviewers disclosed about money, with their own
          words. It doesn&apos;t judge whether a review is honest, and it never
          calls anyone independent.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        {LABELS.map((l) => (
          <Card key={l.key}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Dot k={l.key} className="size-2.5" /> {l.name}
              </CardTitle>
              <CardDescription>{l.means}</CardDescription>
            </CardHeader>
            <CardFooter className="mt-auto text-[12.5px] leading-relaxed text-ink-2">
              <span>
                <span className="font-medium">We need: </span>
                {l.needs}
              </span>
            </CardFooter>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>The rules</CardTitle>
            <CardDescription>
              What counts, and what doesn&apos;t.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {RULES.map((r) => (
              <div
                key={r.text}
                className="flex gap-3 text-[13.5px] leading-relaxed text-ink-2"
              >
                {r.ok ? (
                  <CheckCircleIcon
                    weight="fill"
                    className="mt-0.5 size-4.5 shrink-0 text-klein"
                  />
                ) : (
                  <XCircleIcon
                    weight="fill"
                    className="mt-0.5 size-4.5 shrink-0 text-faint"
                  />
                )}
                {r.text}
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>How accurate it is</CardTitle>
            <CardDescription>
              Unpaid&apos;s labels compared with a line-by-line read of every
              review in the Big Billion Days report
              {acc ? ` (${acc.videos} reviews)` : ""}.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {acc ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Label</TableHead>
                    <TableHead className="text-right">Labels right</TableHead>
                    <TableHead className="text-right">Ties caught</TableHead>
                    <TableHead>Missed</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((s) => (
                    <TableRow key={s.label}>
                      <TableCell>
                        <span className="flex items-center gap-2 font-medium text-ink">
                          <Dot k={BY_NAME[s.label]?.key ?? "none"} /> {s.label}
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-mono text-[12px] tnum">
                        {pct(s.precision)}{" "}
                        <span className="text-faint">
                          ({s.right}/{s.found})
                        </span>
                      </TableCell>
                      <TableCell className="text-right font-mono text-[12px] tnum">
                        {pct(s.recall)}{" "}
                        <span className="text-faint">
                          ({s.right}/{s.key})
                        </span>
                      </TableCell>
                      <TableCell className="text-[12.5px] whitespace-normal text-muted-foreground">
                        {s.missed.length ? s.missed.join(", ") : "—"}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <Skeleton className="h-40" />
            )}
          </CardContent>
          <CardFooter className="text-[12.5px] leading-relaxed text-muted-foreground">
            A miss in &ldquo;Earns commission&rdquo; shows up as a wrong &ldquo;
            {NO_DISCLOSURE}&rdquo;. That&apos;s why we never treat no disclosure
            as proof of independence.
          </CardFooter>
        </Card>
      </div>

      <Alert>
        <InfoIcon weight="duotone" />
        <AlertTitle>Good to know</AlertTitle>
        <AlertDescription>
          What was said comes from YouTube&apos;s captions, which can be
          auto-made and imperfect. Reviews without captions are checked from
          their description only. Reports cover reviews from the last three
          weeks, and prices change all day.
        </AlertDescription>
      </Alert>
    </div>
  )
}
