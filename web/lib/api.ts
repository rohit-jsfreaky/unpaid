import type { Account, Accuracy, Report, ReportCard, RunEvent } from "./types"

/** Why a call failed, in product terms. */
export type Problem =
  | "offline"
  | "not_checked"
  | "busy"
  | "budget"
  | "not_shopping"
  | "upstream"
  | "missing"

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public problem: Problem
  ) {
    super(message)
  }
}

const BY_STATUS: Record<number, Problem> = {
  404: "not_checked",
  409: "budget",
  422: "not_shopping",
  429: "busy",
  502: "upstream",
}

async function get<T>(path: string): Promise<T> {
  let res: Response
  try {
    res = await fetch(`/api${path}`, { cache: "no-store" })
  } catch {
    throw new ApiError(0, "offline", "offline")
  }
  if (res.status >= 500 && res.status !== 502)
    throw new ApiError(res.status, "offline", "offline")
  const body = await res.json().catch(() => ({}))
  if (!res.ok)
    throw new ApiError(
      res.status,
      body?.detail ?? "failed",
      res.status === 404 ? "missing" : "upstream"
    )
  return body as T
}

/**
 * Checks a question and reports each step as it happens. Resolves with the finished report.
 * `live: false` answers only questions that were checked before (no keys needed).
 */
async function check(
  question: string,
  opts: { live: boolean; paceMs?: number },
  onEvent: (e: RunEvent) => void
): Promise<{ id: string; report: Report }> {
  let res: Response
  try {
    res = await fetch("/api/ask", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        question,
        replay: !opts.live,
        pace_ms: opts.paceMs ?? 0,
      }),
    })
  } catch {
    throw new ApiError(0, "offline", "offline")
  }
  if (!res.ok || !res.body)
    throw new ApiError(
      res.status,
      "failed",
      res.status >= 500 ? "offline" : "upstream"
    )

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  for (;;) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const lines = buffer.split("\n")
    buffer = lines.pop() ?? ""
    for (const line of lines) {
      if (!line.trim()) continue
      const event = JSON.parse(line) as RunEvent
      if (event.type === "result")
        return { id: event.id, report: event.showcase }
      if (event.type === "error")
        throw new ApiError(
          event.status,
          event.detail,
          BY_STATUS[event.status] ?? "upstream"
        )
      onEvent(event)
    }
    if (done)
      throw new ApiError(500, "the check ended without a report", "upstream")
  }
}

export const api = {
  account: () => get<Account>("/account"),
  reports: () => get<ReportCard[]>("/reports"),
  report: (id: string) =>
    get<{ sample: boolean; report: Report }>(
      `/reports/${encodeURIComponent(id)}`
    ),
  accuracy: () => get<Accuracy>("/accuracy"),
  check,
}

/** Plain-words message for anything that went wrong. */
export function explain(e: unknown): { title: string; body: string } {
  const p: Problem = e instanceof ApiError ? e.problem : "upstream"
  switch (p) {
    case "offline":
      return {
        title: "Unpaid can't connect right now",
        body: "Our data service isn't answering. Try again in a minute.",
      }
    case "not_checked":
      return {
        title: "We haven't checked this one yet",
        body: "This demo answers questions we've already checked. Open one of the sample reports to see how it works.",
      }
    case "busy":
      return {
        title: "Another check is running",
        body: "Give it a minute, then try again.",
      }
    case "budget":
      return {
        title: "We've hit this month's limit",
        body: "New checks are paused until next month. Saved reports still open.",
      }
    case "not_shopping":
      return {
        title: "Ask about something to buy",
        body: "For example: best phone under ₹30,000 for camera and battery.",
      }
    case "missing":
      return {
        title: "We couldn't find that report",
        body: "It may have been removed. Pick one from your reports.",
      }
    default:
      return {
        title: "Something went wrong",
        body: "Please try again. If it keeps happening, open a saved report instead.",
      }
  }
}
