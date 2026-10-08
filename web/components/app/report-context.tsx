"use client"

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import { api, explain } from "@/lib/api"
import { hasMoneyTie } from "@/lib/labels"
import type { PhonePrices, Report, Review, Video } from "@/lib/types"

type Loaded = {
  report: Report
  sample: boolean
  /** Reviews joined with their labels, in the report's order. */
  rows: { video: Video; review: Review }[]
  priceOf: (phone: string) => PhonePrices | undefined
  withTies: Video[]
}

type State =
  | { status: "loading" }
  | { status: "error"; title: string; body: string }
  | ({ status: "ready" } & Loaded)

const Ctx = createContext<State>({ status: "loading" })

export function ReportProvider({
  id,
  children,
}: {
  id: string
  children: ReactNode
}) {
  const [state, setState] = useState<State>({ status: "loading" })
  useEffect(() => {
    let live = true
    api
      .report(id)
      .then(({ report, sample }) => {
        if (!live) return
        const byId = new Map(report.reviews.map((r) => [r.video_id, r]))
        const rows = report.videos.flatMap((v) => {
          const review = byId.get(v.video_id)
          return review ? [{ video: v, review }] : []
        })
        const prices = new Map(report.prices.map((p) => [p.phone, p]))
        setState({
          status: "ready",
          report,
          sample,
          rows,
          priceOf: (phone) => prices.get(phone),
          withTies: report.videos.filter(hasMoneyTie),
        })
      })
      .catch((e) => live && setState({ status: "error", ...explain(e) }))
    return () => {
      live = false
    }
  }, [id])
  const value = useMemo(() => state, [state])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useReport(): State {
  return useContext(Ctx)
}
