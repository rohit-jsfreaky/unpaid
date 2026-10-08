"use client"

import { ArrowSquareOutIcon, StorefrontIcon } from "@phosphor-icons/react"

import { SellersChart } from "@/components/app/charts"
import { useReport } from "@/components/app/report-context"
import { Dot } from "@/components/label-chip"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { rupees, stamp } from "@/lib/format"

const BUDGET = /under\s*₹?\s*([\d,]+)\s*(k)?/i

export default function Prices() {
  const state = useReport()
  if (state.status !== "ready") return null
  const { report } = state
  const m = report.searches[0]?.match(BUDGET)
  const budget = m ? Number(m[1].replace(/,/g, "")) * (m[2] ? 1000 : 1) : null
  const tally = new Map(report.board.phones.map((p) => [p.name, p]))

  return (
    <div className="flex flex-col gap-4">
      <p className="max-w-2xl text-[13.5px] leading-relaxed text-muted-foreground">
        Prices for the phones the reviewers agree on, from every shop that
        listed them when we checked. Prices change all day; each one shows when
        it was checked.
      </p>
      {report.prices.map((pp) => {
        const t = tally.get(pp.phone)
        const low = pp.offers[0]
        const over = budget !== null && low !== undefined && low.price > budget
        return (
          <Card key={pp.phone}>
            <CardHeader>
              <CardTitle className="text-[18px]">{pp.phone}</CardTitle>
              <CardDescription className="flex flex-wrap items-center gap-x-3 gap-y-1">
                {t ? (
                  <>
                    <span className="inline-flex items-center gap-1.5">
                      <Dot k="none" /> {t.no_disclosure} of{" "}
                      {report.board.no_disclosure_videos_with_picks} with
                      nothing to disclose
                    </span>
                    <span className="inline-flex items-center gap-1.5">
                      <Dot k="commission" /> {t.disclosed} of{" "}
                      {report.board.disclosed_videos_with_picks} with a money
                      tie
                    </span>
                  </>
                ) : null}
              </CardDescription>
              <CardAction className="text-right">
                <p className="text-[12px] text-muted-foreground">
                  Lowest today
                </p>
                <p className="text-[24px] leading-tight font-medium tracking-tight text-ink tnum">
                  {rupees(low?.price)}
                </p>
                {over ? (
                  <Badge variant="outline">
                    Over your ₹{budget?.toLocaleString("en-IN")} budget
                  </Badge>
                ) : null}
              </CardAction>
            </CardHeader>
            <CardContent>
              {pp.offers.length ? (
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  <SellersChart offers={pp.offers.slice(0, 10)} />
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Seller</TableHead>
                        <TableHead className="text-right">Price</TableHead>
                        <TableHead className="text-right">Checked</TableHead>
                        <TableHead className="w-8" />
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pp.offers.map((o, i) => (
                        <TableRow key={o.seller}>
                          <TableCell className="max-w-[220px] whitespace-normal">
                            <p className="font-medium text-ink">{o.seller}</p>
                            <p className="line-clamp-1 text-[12px] text-muted-foreground">
                              {o.title}
                            </p>
                          </TableCell>
                          <TableCell className="text-right font-mono text-[12px] tnum">
                            {rupees(o.price)}
                            {i === 0 ? (
                              <span className="ml-1.5 text-klein">lowest</span>
                            ) : null}
                          </TableCell>
                          <TableCell className="text-right text-[12px] text-muted-foreground">
                            {stamp(
                              o.searched_at
                                .replace(" UTC", "Z")
                                .replace(" ", "T")
                            )}
                          </TableCell>
                          <TableCell>
                            {o.link ? (
                              <a
                                href={o.link}
                                target="_blank"
                                rel="noreferrer"
                                aria-label={`Open ${o.seller}`}
                              >
                                <ArrowSquareOutIcon className="text-faint hover:text-ink" />
                              </a>
                            ) : null}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <Empty className="py-10">
                  <EmptyHeader>
                    <EmptyMedia variant="icon">
                      <StorefrontIcon weight="duotone" />
                    </EmptyMedia>
                    <EmptyTitle>No shop listed it when we checked</EmptyTitle>
                    <EmptyDescription>
                      New phones often reach shops after the reviews. Check
                      again later.
                    </EmptyDescription>
                  </EmptyHeader>
                </Empty>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
