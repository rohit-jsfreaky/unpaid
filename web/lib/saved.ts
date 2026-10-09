import type { Report, ReportCard } from "./types"

/**
 * The reports this browser checked, kept on the device. The engine also saves them, but on Vercel the next request can
 * reach another instance that doesn't have the report, so the page falls back to this copy. Storage can be missing or
 * blocked (private windows): every call fails quietly and the page still works from the engine alone.
 */
const KEY = "unpaid:reports:v1"
const KEEP = 8

type Saved = Record<string, { card: ReportCard; report: Report }>

function read(): Saved {
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "{}") as Saved
  } catch {
    return {}
  }
}

export function saveReport(card: ReportCard, report: Report): void {
  try {
    const all = { ...read(), [card.id]: { card, report } }
    const newest = Object.values(all)
      .sort((a, b) => b.card.checked_at.localeCompare(a.card.checked_at))
      .slice(0, KEEP)
    localStorage.setItem(
      KEY,
      JSON.stringify(Object.fromEntries(newest.map((s) => [s.card.id, s])))
    )
  } catch {
    // full or blocked storage: the engine's copy still works
  }
}

export function savedReport(id: string): Report | null {
  return read()[id]?.report ?? null
}

export function savedCards(): ReportCard[] {
  return Object.values(read()).map((s) => s.card)
}
