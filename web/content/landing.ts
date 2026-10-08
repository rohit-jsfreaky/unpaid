// Real examples for the landing page, exported from the recorded report by `uv run unpaid site`.
// `uv run verify` fails if this file differs from a fresh export, so no number here is typed by hand.
import data from "./landing.json"

export type Example = {
  channel: string
  title?: string
  top_pick?: string | null
  label?: string
  party?: string | null
  quote: string
  meaning_en: string | null
  time_text: string | null
  url: string
  language?: string
}

export type Row = {
  channel: string
  views: number | null
  published: string | null
  language: string | null
  labels: string[]
  top_pick: string | null
}

export type Landing = {
  question: string
  checked_at: string
  videos_found: number
  reviews: number
  with_ties: number
  per_label: Record<string, number>
  videos_with_paid_links: number
  paid_links: number
  languages: Record<string, number>
  brand_example: Example
  spoken_example: Example
  denial_example: Example
  groups: { no_disclosure: number; disclosed: number }
  phones: {
    name: string
    no_disclosure: number
    disclosed: number
    all: number
  }[]
  prices: {
    phone: string
    sellers: number
    offers: { seller: string; price: number; searched_at: string }[]
  }
  rows: Row[]
  accuracy: {
    label: string
    key: number
    found: number
    right: number
    precision: number | null
    recall: number | null
    missed: string[]
  }[]
  must_haves: string[]
  focus: Focus[]
  report_id: string
  reports: { id: string; question: string; product: string; reviews: number }[]
}

export type Focus = {
  area: string
  best: string | null
  no_disclosure: number
  of_no_disclosure: number
  disclosed: number
  of_disclosed: number
  weak: number
  price: number | null
  quote: string | null
  meaning_en: string | null
  channel: string | null
  time_text: string | null
  url: string | null
  language: string | null
}

export const landing = data as Landing

/** How many different #1 picks the reviews had. */
export const distinctTopPicks = new Set(
  landing.rows.map((r) => r.top_pick).filter(Boolean)
).size
