"use client"

import {
  CaretRightIcon,
  MagnifyingGlassIcon,
  VideoCameraSlashIcon,
} from "@phosphor-icons/react"
import Image from "next/image"
import { useMemo, useState } from "react"

import { useReport } from "@/components/app/report-context"
import { ReviewSheet } from "@/components/app/review-sheet"
import { Dot, LabelChip } from "@/components/label-chip"
import { Card } from "@/components/ui/card"
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import {
  InputGroup,
  InputGroupAddon,
  InputGroupInput,
} from "@/components/ui/input-group"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { day, language, views } from "@/lib/format"
import { LABELS, labelsOf, type LabelKey } from "@/lib/labels"
import type { Review, Video } from "@/lib/types"

type Filter = "all" | LabelKey

export default function Reviews() {
  const state = useReport()
  const [q, setQ] = useState("")
  const [filter, setFilter] = useState<Filter>("all")
  const [open, setOpen] = useState<{ video: Video; review: Review } | null>(
    null
  )

  const rows = useMemo(
    () => (state.status === "ready" ? state.rows : []),
    [state]
  )
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return rows
      .filter(
        (r) =>
          filter === "all" || labelsOf(r.video).some((l) => l.key === filter)
      )
      .filter(
        (r) =>
          !needle ||
          `${r.video.channel} ${r.video.title}`.toLowerCase().includes(needle)
      )
      .sort((a, b) => (b.video.views ?? 0) - (a.video.views ?? 0))
  }, [rows, q, filter])
  if (state.status !== "ready") return null

  const count = (k: LabelKey) =>
    rows.filter((r) => labelsOf(r.video).some((l) => l.key === k)).length

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <ToggleGroup
          variant="outline"
          size="sm"
          value={[filter]}
          onValueChange={(v) => setFilter((v[0] as Filter) ?? "all")}
          className="flex-wrap"
        >
          <ToggleGroupItem value="all">All {rows.length}</ToggleGroupItem>
          {LABELS.filter((l) => count(l.key) > 0).map((l) => (
            <ToggleGroupItem key={l.key} value={l.key}>
              <Dot k={l.key} /> {l.short} {count(l.key)}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
        <InputGroup className="lg:w-72">
          <InputGroupAddon>
            <MagnifyingGlassIcon />
          </InputGroupAddon>
          <InputGroupInput
            placeholder="Search reviewers or titles"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </InputGroup>
      </div>

      {/* Phones: one card per review. */}
      <div className="flex flex-col gap-3 md:hidden">
        {shown.length ? null : (
          <p className="rounded-2xl bg-white p-6 text-center text-[13px] text-muted-foreground ring-1 ring-foreground/10">
            No reviews match. Try another search.
          </p>
        )}
        {shown.map((r) => {
          const top = [...r.video.picks].sort(
            (a, b) => (a.rank ?? 99) - (b.rank ?? 99)
          )[0]
          return (
            <button
              key={r.video.video_id}
              type="button"
              onClick={() => setOpen(r)}
              className="flex flex-col gap-3 rounded-2xl bg-white p-3.5 text-left ring-1 ring-foreground/10"
            >
              <div className="flex gap-3">
                <div className="relative aspect-video w-28 shrink-0 overflow-hidden rounded-lg bg-mist">
                  <Image
                    src={r.review.thumbnail}
                    alt=""
                    fill
                    sizes="112px"
                    className="object-cover"
                  />
                </div>
                <div className="min-w-0">
                  <p className="line-clamp-2 text-[13px] leading-snug font-medium text-ink">
                    {r.video.title}
                  </p>
                  <p className="mt-1 text-[12px] text-muted-foreground">
                    {r.video.channel} · {views(r.video.views)} views
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-1.5">
                {labelsOf(r.video).map((l) => (
                  <LabelChip key={l.key} name={l.name} size="sm" />
                ))}
                <span className="text-[12px] text-muted-foreground">
                  {language(r.review.has_transcript ? r.review.language : null)}{" "}
                  · {day(r.review.published)}
                </span>
              </div>
              {top ? (
                <p className="text-[12.5px] text-ink-2">
                  <span className="text-muted-foreground">#1 pick: </span>
                  {top.phone}
                </p>
              ) : null}
            </button>
          )
        })}
      </div>

      <Card className="hidden py-0 md:flex">
        {shown.length ? (
          <Table>
            <TableHeader>
              <TableRow className="bg-soft/80 hover:bg-soft/80">
                <TableHead className="w-[42%] pl-4">Review</TableHead>
                <TableHead>Posted</TableHead>
                <TableHead className="text-right">Views</TableHead>
                <TableHead>Spoken in</TableHead>
                <TableHead>What we found</TableHead>
                <TableHead>Their #1 pick</TableHead>
                <TableHead className="w-8" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {shown.map((r) => {
                const top = [...r.video.picks].sort(
                  (a, b) => (a.rank ?? 99) - (b.rank ?? 99)
                )[0]
                return (
                  <TableRow
                    key={r.video.video_id}
                    className="cursor-pointer"
                    onClick={() => setOpen(r)}
                  >
                    <TableCell className="pl-4">
                      <div className="flex items-center gap-3">
                        <div className="relative aspect-video w-24 shrink-0 overflow-hidden rounded-md bg-mist">
                          <Image
                            src={r.review.thumbnail}
                            alt=""
                            fill
                            sizes="96px"
                            className="object-cover"
                          />
                        </div>
                        <div className="min-w-0 whitespace-normal">
                          <p className="line-clamp-2 text-[13px] leading-snug font-medium text-ink">
                            {r.video.title}
                          </p>
                          <p className="mt-0.5 text-[12px] text-muted-foreground">
                            {r.video.channel}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {day(r.review.published)}
                    </TableCell>
                    <TableCell className="text-right font-mono text-[12px] tnum">
                      {views(r.video.views)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {language(
                        r.review.has_transcript ? r.review.language : null
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col items-start gap-1">
                        {labelsOf(r.video).map((l) => (
                          <LabelChip key={l.key} name={l.name} size="sm" />
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="whitespace-normal text-ink-2">
                      {top?.phone ?? <span className="text-faint">—</span>}
                    </TableCell>
                    <TableCell>
                      <CaretRightIcon className="text-faint" />
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        ) : (
          <Empty className="py-16">
            <EmptyHeader>
              <EmptyMedia variant="icon">
                <VideoCameraSlashIcon weight="duotone" />
              </EmptyMedia>
              <EmptyTitle>No reviews match</EmptyTitle>
              <EmptyDescription>
                Try another search or show all reviews.
              </EmptyDescription>
            </EmptyHeader>
          </Empty>
        )}
      </Card>

      <ReviewSheet row={open} onOpenChange={(o) => !o && setOpen(null)} />
    </div>
  )
}
