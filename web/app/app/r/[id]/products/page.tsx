"use client"

import { CaretRightIcon, PlayCircleIcon } from "@phosphor-icons/react"
import { useMemo, useState } from "react"

import { ShareChart } from "@/components/app/charts"
import { useReport } from "@/components/app/report-context"
import { LabelChip } from "@/components/label-chip"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { areaMeta } from "@/lib/areas"
import { productWords } from "@/lib/product"
import { rupees } from "@/lib/format"
import type { Area, AreaBoard, UseMention } from "@/lib/types"

type By = "all" | Area

/** One row of the table, whichever ranking is on. */
type Row = {
  key: string
  name: string
  noneN: number
  tieN: number
  extra: string
}

export default function Products() {
  const state = useReport()
  const [by, setBy] = useState<By | null>(null)
  const [open, setOpen] = useState<string | null>(null)

  const report = state.status === "ready" ? state.report : null
  const areas = useMemo(() => report?.areas ?? [], [report])
  // Start on what the shopper asked for, if anything.
  const current: By =
    by ?? (areas.find((a) => a.focus)?.area as By | undefined) ?? "all"
  if (state.status !== "ready" || !report) return null
  const { priceOf } = state
  const b = report.board
  const nd = b.no_disclosure_videos_with_picks
  const ds = b.disclosed_videos_with_picks
  const area: AreaBoard | undefined =
    current === "all" ? undefined : areas.find((a) => a.area === current)

  const rows: Row[] = area
    ? area.phones.map((p) => ({
        key: p.key,
        name: p.name,
        noneN: p.good_no_disclosure,
        tieN: p.good_disclosed,
        extra: p.weak ? `${p.weak} call it weak` : "—",
      }))
    : b.phones.map((p) => ({
        key: p.key,
        name: p.name,
        noneN: p.no_disclosure,
        tieN: p.disclosed,
        extra: p.best_rank ? `#${p.best_rank}` : "—",
      }))
  const what = area ? areaMeta(area.area, area.name).praise : "pick it"
  const words = productWords(report.product)

  const tally = open ? b.phones.find((p) => p.key === open) : undefined
  const openName =
    tally?.name ??
    areas.flatMap((a) => a.phones).find((p) => p.key === open)?.name ??
    ""
  const opinions: { area: Area; m: UseMention }[] = open
    ? areas.flatMap((a) =>
        (a.phones.find((p) => p.key === open)?.mentions ?? []).map((m) => ({
          area: a.area,
          m,
        }))
      )
    : []
  const english = new Set(
    report.reviews.filter((r) => r.language === "latin").map((r) => r.video_id)
  )
  const meaningOf = new Map(
    report.videos.flatMap((v) =>
      v.picks.map((p) => [`${v.video_id}|${p.quote}`, p.meaning_en])
    )
  )
  const low = openName ? priceOf(openName)?.offers : undefined

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-2">
        <span className="text-[12.5px] text-muted-foreground">Rank by</span>
        <ToggleGroup
          variant="outline"
          size="sm"
          value={[current]}
          onValueChange={(v) => v[0] && setBy(v[0] as By)}
          className="flex-wrap"
        >
          <ToggleGroupItem value="all">Overall</ToggleGroupItem>
          {areas.map((a) => {
            const Icon = areaMeta(a.area, a.name).icon
            return (
              <ToggleGroupItem key={a.area} value={a.area}>
                <Icon weight="duotone" /> {areaMeta(a.area, a.name).name}
                {a.focus ? (
                  <span
                    className="size-1.5 rounded-full bg-klein"
                    aria-label="you asked for this"
                  />
                ) : null}
              </ToggleGroupItem>
            )
          })}
        </ToggleGroup>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {area
              ? `Who praises the ${areaMeta(area.area, area.name).name.toLowerCase()}`
              : "Who recommends what"}
          </CardTitle>
          <CardDescription>
            {area
              ? `Reviewers who say it's good for ${areaMeta(area.area, area.name).name.toLowerCase()}, in their own words: the ${nd} with nothing to disclose vs the ${ds} with a money tie.`
              : `The ${words.many} picked most, split by reviewers with nothing to disclose (${nd}) and with a money tie (${ds}).`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {rows.length ? (
            <ShareChart
              rows={rows
                .slice(0, 12)
                .map((r) => ({ phone: r.name, noneN: r.noneN, tieN: r.tieN }))}
              nd={nd}
              ds={ds}
              what={what}
            />
          ) : (
            <p className="py-8 text-center text-[13px] text-muted-foreground">
              No reviewer talked about this.
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="py-0">
        <Table>
          <TableHeader>
            <TableRow className="bg-soft/80 hover:bg-soft/80">
              <TableHead className="pl-4 capitalize">{words.one}</TableHead>
              <TableHead className="text-right">
                {area ? "Praised · no disclosure" : "No disclosure"}
              </TableHead>
              <TableHead className="text-right">
                {area ? "Praised · money tie" : "Money tie"}
              </TableHead>
              <TableHead className="text-right">
                {area ? "Weak" : "Best rank"}
              </TableHead>
              <TableHead className="text-right">Lowest price</TableHead>
              <TableHead className="w-8" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((r) => {
              const price = priceOf(r.name)?.offers[0]
              return (
                <TableRow
                  key={r.key}
                  className="cursor-pointer"
                  onClick={() => setOpen(r.key)}
                >
                  <TableCell className="pl-4 font-medium whitespace-normal text-ink">
                    {r.name}
                  </TableCell>
                  <TableCell className="text-right font-mono text-[12px] tnum">
                    {r.noneN} <span className="text-faint">/ {nd}</span>
                  </TableCell>
                  <TableCell className="text-right font-mono text-[12px] tnum">
                    {r.tieN} <span className="text-faint">/ {ds}</span>
                  </TableCell>
                  <TableCell className="text-right font-mono text-[12px] text-muted-foreground tnum">
                    {r.extra}
                  </TableCell>
                  <TableCell className="text-right font-mono text-[12px] tnum">
                    {price ? rupees(price.price) : "—"}
                  </TableCell>
                  <TableCell>
                    <CaretRightIcon className="text-faint" />
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </Card>

      <Sheet open={open !== null} onOpenChange={(o) => !o && setOpen(null)}>
        <SheetContent
          side="right"
          className="w-full overflow-y-auto data-[side=right]:sm:max-w-[540px]"
        >
          {open ? (
            <>
              <SheetHeader className="px-6 pt-6">
                <SheetTitle className="text-[20px]">{openName}</SheetTitle>
                <SheetDescription>
                  {tally
                    ? `Picked in ${tally.all} of ${b.videos_with_picks} reviews · ${tally.no_disclosure} with nothing to disclose · ${tally.disclosed} with a money tie`
                    : "Praised by reviewers, not in their top lists"}
                </SheetDescription>
              </SheetHeader>
              <div className="flex flex-col gap-5 px-6 pb-8">
                {low?.length ? (
                  <div className="rounded-xl bg-klein-mist p-4 shadow-[0_0_0_1px_rgb(0_47_167/0.1)]">
                    <p className="text-[12px] text-klein">Lowest price today</p>
                    <p className="text-[24px] font-medium text-klein tnum">
                      {rupees(low[0].price)}
                    </p>
                    <p className="text-[12px] text-klein/80">
                      {low[0].seller} · {low.length}{" "}
                      {low.length === 1 ? "seller" : "sellers"}
                    </p>
                  </div>
                ) : null}

                {opinions.length ? (
                  <section className="flex flex-col gap-3">
                    <h3 className="text-[13px] font-medium text-ink">
                      What reviewers say it&apos;s good at
                    </h3>
                    {opinions.map(({ area: ar, m }, i) => {
                      const meta = areaMeta(
                        ar,
                        areas.find((x) => x.area === ar)?.name
                      )
                      const Icon = meta.icon
                      return (
                        <div
                          key={i}
                          className="rounded-xl bg-white p-3.5 shadow-[0_0_0_1px_rgb(15_23_42/0.07)]"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="inline-flex items-center gap-1.5 text-[12.5px] font-medium text-ink">
                              <Icon
                                weight="duotone"
                                className="size-4 text-klein"
                              />{" "}
                              {meta.name}
                              <Badge
                                variant={
                                  m.verdict === "good" ? "secondary" : "outline"
                                }
                              >
                                {m.verdict === "good" ? "Good" : "Weak"}
                              </Badge>
                            </span>
                            <span className="text-[12px] text-muted-foreground">
                              {m.channel}
                            </span>
                          </div>
                          <p className="mt-2 text-[13px] leading-relaxed text-ink">
                            &ldquo;{m.quote}&rdquo;
                          </p>
                          {!english.has(m.video_id) ? (
                            <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
                              {m.meaning_en}
                            </p>
                          ) : null}
                          <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                            <div className="flex flex-wrap gap-1">
                              {m.labels.map((l) => (
                                <LabelChip key={l} name={l} size="sm" />
                              ))}
                            </div>
                            {m.time_text ? (
                              <a
                                href={m.url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 text-[12px] font-medium text-klein hover:underline"
                              >
                                <PlayCircleIcon
                                  weight="fill"
                                  className="size-3.5"
                                />{" "}
                                Watch at {m.time_text}
                              </a>
                            ) : null}
                          </div>
                        </div>
                      )
                    })}
                  </section>
                ) : null}

                {tally ? (
                  <>
                    <Separator />
                    <section className="flex flex-col gap-3">
                      <h3 className="text-[13px] font-medium text-ink">
                        Who recommends it
                      </h3>
                      {tally.mentions.map((m) => (
                        <div
                          key={m.video_id}
                          className="rounded-xl bg-white p-3.5 shadow-[0_0_0_1px_rgb(15_23_42/0.07)]"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-[13.5px] font-medium text-ink">
                                {m.channel}
                              </p>
                              <div className="mt-1.5 flex flex-wrap gap-1">
                                {m.labels.map((l) => (
                                  <LabelChip key={l} name={l} size="sm" />
                                ))}
                              </div>
                            </div>
                            <span className="shrink-0 font-mono text-[12px] text-muted-foreground tnum">
                              {m.rank ? `#${m.rank}` : "in list"}
                            </span>
                          </div>
                          <p className="mt-2.5 line-clamp-3 text-[12.5px] leading-relaxed text-muted-foreground">
                            &ldquo;
                            {english.has(m.video_id)
                              ? m.quote
                              : (meaningOf.get(`${m.video_id}|${m.quote}`) ??
                                m.quote)}
                            &rdquo;
                          </p>
                          {m.time_text ? (
                            <a
                              href={m.url}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-1.5 inline-flex items-center gap-1 text-[12px] font-medium text-klein hover:underline"
                            >
                              <PlayCircleIcon
                                weight="fill"
                                className="size-3.5"
                              />{" "}
                              Watch at {m.time_text}
                            </a>
                          ) : null}
                        </div>
                      ))}
                    </section>
                  </>
                ) : null}
              </div>
            </>
          ) : null}
        </SheetContent>
      </Sheet>
    </div>
  )
}
