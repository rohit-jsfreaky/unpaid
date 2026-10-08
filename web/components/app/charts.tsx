"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts"

import { Dot } from "@/components/label-chip"
import { useIsMobile } from "@/hooks/use-mobile"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  type ChartConfig,
} from "@/components/ui/chart"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { day, rupees, views as fmtViews } from "@/lib/format"
import { LABELS, labelsOf, type LabelKey } from "@/lib/labels"
import type { Board, Offer, Review, Video } from "@/lib/types"

/* ---------- Labels: how many reviews carry each one ---------- */

export function LabelBars({
  videos,
  onPick,
}: {
  videos: Video[]
  onPick?: (key: LabelKey) => void
}) {
  const total = videos.length
  const counts = LABELS.map((l) => ({
    ...l,
    n: videos.filter((v) => labelsOf(v).some((x) => x.key === l.key)).length,
  }))
  return (
    <div className="flex flex-col gap-3.5">
      {counts.map((c) => (
        <Tooltip key={c.key}>
          <TooltipTrigger
            render={
              <button
                type="button"
                onClick={() => onPick?.(c.key)}
                className="group grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-1.5 text-left sm:grid-cols-[minmax(0,170px)_1fr_auto]"
              />
            }
          >
            <span className="flex min-w-0 items-center gap-2 text-[13px] text-ink-2">
              <Dot k={c.key} />
              <span className="truncate">{c.name}</span>
            </span>
            {/* On phones the bar gets its own full-width row under the name. */}
            <span className="order-last col-span-2 h-2.5 overflow-hidden rounded-full bg-mist sm:order-none sm:col-span-1">
              <span
                className="block h-full rounded-full transition-[filter] group-hover:brightness-95"
                style={{
                  width: `${total ? (c.n / total) * 100 : 0}%`,
                  background: `var(--label-${c.key})`,
                }}
              />
            </span>
            <span className="w-14 text-right font-mono text-[12px] text-ink tnum">
              {c.n} <span className="text-faint">/ {total}</span>
            </span>
          </TooltipTrigger>
          <TooltipContent side="top">
            {c.n} of {total} reviews · {c.means}
          </TooltipContent>
        </Tooltip>
      ))}
    </div>
  )
}

/* ---------- Picks: reviewers with no disclosure vs with a money tie ---------- */

const PICKS: ChartConfig = {
  none: { label: "No disclosure found", color: "var(--label-none)" },
  tie: { label: "Has a money tie", color: "var(--label-commission)" },
}

type PickRow = {
  phone: string
  none: number
  tie: number
  noneN: number
  tieN: number
}

export function PicksChart({
  board,
  limit = 8,
}: {
  board: Board
  limit?: number
}) {
  return (
    <ShareChart
      rows={board.phones.slice(0, limit).map((p) => ({
        phone: p.name,
        noneN: p.no_disclosure,
        tieN: p.disclosed,
      }))}
      nd={board.no_disclosure_videos_with_picks}
      ds={board.disclosed_videos_with_picks}
      what="pick it"
    />
  )
}

/** Share of each reviewer group behind each phone: picks overall, or praise for one area ("praise its camera"). */
export function ShareChart({
  rows,
  nd,
  ds,
  what,
}: {
  rows: { phone: string; noneN: number; tieN: number }[]
  nd: number
  ds: number
  what: string
}) {
  const mobile = useIsMobile()
  const data: PickRow[] = rows.map((r) => ({
    ...r,
    none: nd ? Math.round((r.noneN / nd) * 100) : 0,
    tie: ds ? Math.round((r.tieN / ds) * 100) : 0,
  }))
  return (
    <ChartContainer
      config={PICKS}
      className="aspect-auto w-full"
      style={{ height: 64 + data.length * 52 }}
    >
      <BarChart
        data={data}
        layout="vertical"
        margin={{ left: 0, right: mobile ? 36 : 44, top: 4, bottom: 4 }}
        barGap={2}
        barCategoryGap={12}
      >
        <CartesianGrid horizontal={false} strokeDasharray="3 3" />
        <XAxis
          type="number"
          domain={[0, 100]}
          tickFormatter={(v) => `${v}%`}
          tickLine={false}
          axisLine={false}
          fontSize={11}
        />
        <YAxis
          type="category"
          dataKey="phone"
          width={mobile ? 104 : 170}
          tickLine={false}
          axisLine={false}
          fontSize={mobile ? 11 : 12}
          tick={{ fill: "var(--color-ink-2)" }}
        />
        <ChartTooltip
          cursor={{ fill: "var(--color-mist)", opacity: 0.6 }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const r = payload[0].payload as PickRow
            return (
              <div className="grid min-w-52 gap-1.5 rounded-lg bg-background px-3 py-2 text-xs shadow-xl ring-1 ring-foreground/10">
                <p className="font-medium text-ink">{r.phone}</p>
                <p className="flex items-center gap-2 text-ink-2">
                  <Dot k="none" /> {r.noneN} of {nd} with no disclosure {what}
                </p>
                <p className="flex items-center gap-2 text-ink-2">
                  <Dot k="commission" /> {r.tieN} of {ds} with a money tie{" "}
                  {what}
                </p>
              </div>
            )
          }}
        />
        <ChartLegend content={<ChartLegendContent />} verticalAlign="top" />
        <Bar dataKey="none" fill="var(--color-none)" radius={4} maxBarSize={14}>
          <LabelList
            dataKey="noneN"
            position="right"
            formatter={(v) => `${v}/${nd}`}
            className="fill-ink-2"
            fontSize={11}
          />
        </Bar>
        <Bar dataKey="tie" fill="var(--color-tie)" radius={4} maxBarSize={14}>
          <LabelList
            dataKey="tieN"
            position="right"
            formatter={(v) => `${v}/${ds}`}
            className="fill-ink-2"
            fontSize={11}
          />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}

/* ---------- When the reviews came out, and how many watched ---------- */

const TIMELINE: ChartConfig = {
  none: { label: "No disclosure found", color: "var(--label-none)" },
  tie: { label: "Has a money tie", color: "var(--label-commission)" },
}

type Point = {
  x: number
  y: number
  channel: string
  title: string
  labels: string
  when: string
}

export function TimelineChart({
  rows,
}: {
  rows: { video: Video; review: Review }[]
}) {
  const toPoint = (r: { video: Video; review: Review }): Point | null =>
    r.review.published && r.video.views
      ? {
          x: new Date(r.review.published).getTime(),
          y: r.video.views,
          channel: r.video.channel,
          title: r.video.title,
          labels: labelsOf(r.video)
            .map((l) => l.name)
            .join(", "),
          when: day(r.review.published),
        }
      : null
  const none = rows
    .filter((r) => !r.video.labels.length)
    .map(toPoint)
    .filter((p): p is Point => p !== null)
  const tie = rows
    .filter((r) => r.video.labels.length)
    .map(toPoint)
    .filter((p): p is Point => p !== null)
  return (
    <ChartContainer config={TIMELINE} className="aspect-auto h-[300px] w-full">
      <ScatterChart margin={{ left: 4, right: 16, top: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          type="number"
          dataKey="x"
          domain={["dataMin - 86400000", "dataMax + 86400000"]}
          tickFormatter={(v) =>
            new Date(v).toLocaleDateString("en-IN", {
              day: "numeric",
              month: "short",
            })
          }
          tickLine={false}
          axisLine={false}
          fontSize={11}
        />
        <YAxis
          type="number"
          dataKey="y"
          scale="log"
          domain={["auto", "auto"]}
          tickFormatter={(v) => fmtViews(v)}
          tickLine={false}
          axisLine={false}
          width={44}
          fontSize={11}
        />
        <ZAxis range={[90, 90]} />
        <ChartTooltip
          cursor={{ strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const p = payload[0].payload as Point
            return (
              <div className="grid max-w-72 gap-1 rounded-lg bg-background px-3 py-2 text-xs shadow-xl ring-1 ring-foreground/10">
                <p className="font-medium text-ink">{p.channel}</p>
                <p className="line-clamp-2 text-muted-foreground">{p.title}</p>
                <p className="text-ink-2">
                  {p.when} · {fmtViews(p.y)} views
                </p>
                <p className="text-ink-2">{p.labels}</p>
              </div>
            )
          }}
        />
        <ChartLegend content={<ChartLegendContent />} verticalAlign="top" />
        <Scatter
          name="none"
          data={none}
          fill="var(--color-none)"
          stroke="var(--background)"
          strokeWidth={2}
        />
        <Scatter
          name="tie"
          data={tie}
          fill="var(--color-tie)"
          stroke="var(--background)"
          strokeWidth={2}
        />
      </ScatterChart>
    </ChartContainer>
  )
}

/* ---------- One phone's price at every seller ---------- */

const SELLERS: ChartConfig = {
  price: { label: "Price", color: "var(--color-klein)" },
}

export function SellersChart({ offers }: { offers: Offer[] }) {
  const mobile = useIsMobile()
  const data = offers.map((o, i) => ({
    seller: o.seller,
    price: o.price,
    lowest: i === 0,
  }))
  return (
    <ChartContainer
      config={SELLERS}
      className="aspect-auto w-full"
      style={{ height: 24 + data.length * 34 }}
    >
      <BarChart
        data={data}
        layout="vertical"
        margin={{ left: 0, right: 64, top: 0, bottom: 0 }}
        barCategoryGap={8}
      >
        <XAxis type="number" hide domain={[0, "dataMax"]} />
        <YAxis
          type="category"
          dataKey="seller"
          width={mobile ? 104 : 150}
          tickLine={false}
          axisLine={false}
          fontSize={12}
          tick={{ fill: "var(--color-ink-2)" }}
        />
        <ChartTooltip
          cursor={{ fill: "var(--color-mist)", opacity: 0.6 }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null
            const r = payload[0].payload as {
              seller: string
              price: number
              lowest: boolean
            }
            return (
              <div className="rounded-lg bg-background px-3 py-2 text-xs shadow-xl ring-1 ring-foreground/10">
                <p className="font-medium text-ink">{r.seller}</p>
                <p className="text-ink-2">
                  {rupees(r.price)}
                  {r.lowest ? " · lowest" : ""}
                </p>
              </div>
            )
          }}
        />
        <Bar
          dataKey="price"
          radius={4}
          maxBarSize={18}
          shape={(props: {
            x?: number
            y?: number
            width?: number
            height?: number
            payload?: { lowest: boolean }
          }) => (
            <rect
              x={props.x}
              y={props.y}
              width={props.width}
              height={props.height}
              rx={4}
              fill={props.payload?.lowest ? "var(--color-klein)" : "#cbd5e1"}
            />
          )}
        >
          <LabelList
            dataKey="price"
            position="right"
            formatter={(v) => rupees(Number(v))}
            className="fill-ink-2"
            fontSize={11}
          />
        </Bar>
      </BarChart>
    </ChartContainer>
  )
}
