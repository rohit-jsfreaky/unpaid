"use client"

import {
  CheckCircleIcon,
  CircleDashedIcon,
  ClockCountdownIcon,
  WarningCircleIcon,
} from "@phosphor-icons/react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { Suspense, useCallback, useEffect, useRef, useState } from "react"

import { NewCheck } from "@/components/app/new-check"
import { LabelChip } from "@/components/label-chip"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Spinner } from "@/components/ui/spinner"
import { api, ApiError, explain } from "@/lib/api"
import { rupees, sentence } from "@/lib/format"
import type { RunEvent } from "@/lib/types"

type Intent = {
  product: string
  budget_inr: number | null
  sale_event: string | null
  must_haves: string[]
}

type RunState = {
  intent: Intent | null
  searches: number
  searchesDone: number
  found: number | null
  keep: number | null
  opened: number
  linksDone: boolean
  labelled: { channel: string; labels: string[] }[]
  withPicks: number
  usesDone: number
  phones: number
  pricesDone: number
}

const EMPTY: RunState = {
  intent: null,
  searches: 0,
  searchesDone: 0,
  found: null,
  keep: null,
  opened: 0,
  linksDone: false,
  labelled: [],
  withPicks: 0,
  usesDone: 0,
  phones: 0,
  pricesDone: 0,
}

function reduce(p: RunState, e: RunEvent): RunState {
  if (e.type === "plan") return { ...p, searches: e.plan.queries.length }
  if (e.type === "selected")
    return { ...p, keep: e.keep, found: e.keep + e.dropped }
  if (e.type === "video")
    return {
      ...p,
      labelled: [{ channel: e.channel, labels: e.labels }, ...p.labelled],
      withPicks: p.withPicks + (e.picks > 0 ? 1 : 0),
    }
  if (e.type === "uses") return { ...p, usesDone: p.usesDone + 1 }
  if (e.type !== "tool") return p
  if (e.tool === "llm" && e.step === "read the question" && e.status === "done")
    return { ...p, intent: e.intent as Intent }
  if (e.tool === "youtube" && e.status === "done")
    return { ...p, searchesDone: p.searchesDone + 1 }
  if (e.tool === "youtube_video" && e.status === "done")
    return { ...p, opened: p.opened + 1 }
  if (e.tool === "links" && e.status === "done")
    return { ...p, linksDone: true }
  if (e.tool === "google_shopping" && e.status === "start")
    return { ...p, phones: p.phones + 1 }
  if (e.tool === "google_shopping" && e.status === "done")
    return { ...p, pricesDone: p.pricesDone + 1 }
  return p
}

type Phase = "running" | "not_checked" | "error"

function Run() {
  const params = useSearchParams()
  const router = useRouter()
  const q = params.get("q") ?? ""
  const [p, setP] = useState<RunState>(EMPTY)
  const [phase, setPhase] = useState<Phase>("running")
  const [problem, setProblem] = useState<{
    title: string
    body: string
  } | null>(null)
  const [canRunLive, setCanRunLive] = useState(false)
  const started = useRef<string | null>(null)

  const start = useCallback(
    (live: boolean) => {
      setP(EMPTY)
      setPhase("running")
      api
        .check(q, { live, paceMs: live ? 0 : 45 }, (e) =>
          setP((prev) => reduce(prev, e))
        )
        .then(({ id }) => router.replace(`/app/r/${id}`))
        .catch((e) => {
          setProblem(explain(e))
          setPhase(
            e instanceof ApiError && e.problem === "not_checked" && !live
              ? "not_checked"
              : "error"
          )
        })
    },
    [q, router]
  )

  useEffect(() => {
    if (!q || started.current === q) return
    started.current = q
    start(false)
    api
      .account()
      .then((a) => setCanRunLive(a.mode === "live"))
      .catch(() => setCanRunLive(false))
  }, [q, start])

  if (!q) return <NewCheck />

  const total = p.keep ?? 0
  const steps = [
    {
      title: "Understanding what you want",
      done: p.intent !== null,
      active: true,
      detail: p.intent ? (
        <div className="mt-2 flex flex-wrap gap-1.5">
          <Badge variant="secondary" className="capitalize">
            {p.intent.product}
          </Badge>
          {p.intent.budget_inr ? (
            <Badge variant="secondary">
              Under {rupees(p.intent.budget_inr)}
            </Badge>
          ) : null}
          {p.intent.sale_event ? (
            <Badge variant="secondary" className="capitalize">
              {p.intent.sale_event}
            </Badge>
          ) : null}
          {p.intent.must_haves.map((m) => (
            <Badge key={m} variant="outline" className="capitalize">
              {m}
            </Badge>
          ))}
        </div>
      ) : null,
    },
    {
      title: "Finding review videos",
      done: p.keep !== null,
      active: p.intent !== null,
      detail:
        p.keep !== null
          ? `${p.found} videos found, ${p.keep} recent reviews match`
          : p.searches
            ? `Searching in English and Hindi (${p.searchesDone} of ${p.searches})`
            : null,
    },
    {
      title: "Watching each review",
      done: total > 0 && p.opened >= total,
      active: p.keep !== null,
      progress: total ? p.opened / total : 0,
      detail: total ? `${p.opened} of ${total} reviews` : null,
    },
    {
      title: "Checking the shop links under each video",
      done: p.linksDone,
      active: total > 0 && p.opened >= total,
    },
    {
      title: "Looking for money ties",
      done: total > 0 && p.labelled.length >= total,
      active: p.linksDone,
      progress: total ? p.labelled.length / total : 0,
      detail:
        total && p.linksDone
          ? `${p.labelled.length} of ${total} reviews`
          : null,
    },
    {
      title: "Finding what each product is good at",
      done:
        total > 0 && p.labelled.length >= total && p.usesDone >= p.withPicks,
      active: total > 0 && p.labelled.length >= total,
      progress: p.withPicks ? p.usesDone / p.withPicks : 0,
      detail:
        total && p.labelled.length >= total
          ? `${p.usesDone} of ${p.withPicks} reviews` +
            (p.intent?.must_haves.length
              ? ` · ${p.intent.must_haves.join(" and ")} first`
              : "")
          : null,
    },
    {
      title: "Checking today's prices",
      done: p.phones > 0 && p.pricesDone >= p.phones,
      active:
        total > 0 && p.labelled.length >= total && p.usesDone >= p.withPicks,
      detail: p.phones ? `${p.pricesDone} of ${p.phones} phones` : null,
    },
  ]

  return (
    <div className="flex flex-col gap-6 pt-4">
      <div>
        <Badge variant="outline">New check</Badge>
        <h1 className="mt-3 text-[26px] leading-tight font-medium tracking-[-0.02em] text-ink md:text-[32px]">
          {sentence(q)}
        </h1>
      </div>

      {phase === "not_checked" ? (
        <Alert>
          <ClockCountdownIcon weight="duotone" />
          <AlertTitle>{problem?.title}</AlertTitle>
          <AlertDescription>
            {canRunLive
              ? "Unpaid can check it now. It goes through every recent review, so it takes about a minute."
              : problem?.body}
          </AlertDescription>
          <div className="col-start-2 mt-3 flex flex-wrap gap-2">
            {canRunLive ? (
              <Button onClick={() => start(true)}>Check it now</Button>
            ) : null}
            <Button
              variant="outline"
              nativeButton={false}
              render={<Link href="/app" />}
            >
              Open a saved report
            </Button>
          </div>
        </Alert>
      ) : phase === "error" ? (
        <Alert variant="destructive">
          <WarningCircleIcon weight="duotone" />
          <AlertTitle>{problem?.title}</AlertTitle>
          <AlertDescription>{problem?.body}</AlertDescription>
          <div className="col-start-2 mt-3">
            <Button
              variant="outline"
              nativeButton={false}
              render={<Link href="/app" />}
            >
              Back to your reports
            </Button>
          </div>
        </Alert>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
          <Card className="lg:col-span-3">
            <CardHeader>
              <CardTitle>Checking the reviews for you</CardTitle>
              <CardDescription>
                You&apos;ll see the report as soon as it&apos;s ready.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ol className="flex flex-col">
                {steps.map((s, i) => (
                  <li key={s.title} className="flex gap-3.5 pb-6 last:pb-0">
                    <div className="flex flex-col items-center">
                      {s.done ? (
                        <CheckCircleIcon
                          weight="fill"
                          className="size-6 text-klein"
                        />
                      ) : s.active ? (
                        <Spinner className="size-6 text-klein" />
                      ) : (
                        <CircleDashedIcon className="size-6 text-faint" />
                      )}
                      {i < steps.length - 1 ? (
                        <span className="mt-1 w-px flex-1 bg-line" />
                      ) : null}
                    </div>
                    <div className="min-w-0 flex-1 pt-0.5">
                      <p
                        className={
                          s.done || s.active
                            ? "text-[14px] font-medium text-ink"
                            : "text-[14px] text-faint"
                        }
                      >
                        {s.title}
                      </p>
                      {typeof s.detail === "string" ? (
                        <p className="mt-1 text-[12.5px] text-muted-foreground">
                          {s.detail}
                        </p>
                      ) : (
                        s.detail
                      )}
                      {"progress" in s && s.active && !s.done ? (
                        <Progress
                          value={(s.progress ?? 0) * 100}
                          className="mt-2"
                        />
                      ) : null}
                    </div>
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Reviews so far</CardTitle>
              <CardDescription>
                What each reviewer disclosed, as we find it.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex max-h-[460px] flex-col gap-2 overflow-y-auto">
              {p.labelled.length ? (
                p.labelled.map((v, i) => (
                  <div
                    key={`${v.channel}-${p.labelled.length - i}`}
                    className="flex animate-in items-center justify-between gap-3 rounded-lg bg-soft px-3 py-2.5 fade-in slide-in-from-top-1"
                  >
                    <span className="truncate text-[13px] font-medium text-ink">
                      {v.channel}
                    </span>
                    <div className="flex shrink-0 gap-1">
                      {v.labels.map((l) => (
                        <LabelChip key={l} name={l} size="sm" />
                      ))}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-[13px] text-muted-foreground">
                  Reviews will appear here.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default function CheckPage() {
  return (
    <Suspense>
      <Run />
    </Suspense>
  )
}
