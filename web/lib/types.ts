// Mirrors the engine's report (engine/src/unpaid/board.py, proof.py, aggregate.py, prices.py).

export type Source =
  "description" | "transcript" | "description_link" | "youtube_label"

export type Evidence = {
  label: string
  party: string | null
  source: Source
  quote: string
  meaning_en: string | null
  segment: number | null
  time_text: string | null
  url: string
}

export type Pick = {
  phone: string
  rank: number | null
  quote: string
  meaning_en: string
  source: string
  time_text: string | null
  url: string
}

export type Video = {
  video_id: string
  channel: string
  title: string
  link: string
  views: number | null
  has_transcript: boolean
  labels: Evidence[]
  denials: Evidence[]
  picks: Pick[]
}

export type Review = {
  video_id: string
  published: string | null
  published_text: string | null
  views: number | null
  length: string | null
  products_tagged: number | null
  language: string | null
  has_transcript: boolean
  thumbnail: string
}

export type Mention = {
  video_id: string
  channel: string
  disclosed: boolean
  labels: string[]
  rank: number | null
  quote: string
  time_text: string | null
  url: string
}

export type PhoneTally = {
  key: string
  name: string
  all: number
  no_disclosure: number
  disclosed: number
  share_all: number
  share_no_disclosure: number
  share_disclosed: number
  best_rank: number | null
  mentions: Mention[]
}

export type Board = {
  videos_with_picks: number
  no_disclosure_videos_with_picks: number
  disclosed_videos_with_picks: number
  phones: PhoneTally[]
  top_all: string[]
  top_no_disclosure: string[]
}

export type Offer = {
  seller: string
  title: string
  price: number
  price_text: string
  link: string | null
  search_id: string
  searched_at: string
}

export type PhonePrices = { phone: string; offers: Offer[]; skipped: number }

export type Area = string

export type UseMention = {
  video_id: string
  channel: string
  disclosed: boolean
  labels: string[]
  verdict: "good" | "weak"
  quote: string
  meaning_en: string
  time_text: string | null
  url: string
}

export type AreaPhone = {
  name: string
  key: string
  good: number
  good_no_disclosure: number
  good_disclosed: number
  weak: number
  mentions: UseMention[]
}

export type AreaBoard = {
  area: Area
  name: string
  focus: boolean
  reviews: number
  phones: AreaPhone[]
  best_no_disclosure: string | null
  best_all: string | null
}

export type Report = {
  id: string
  question: string
  checked_at: string
  searches: string[]
  videos_found: number
  must_haves: string[]
  product: string
  category: {
    product: string
    areas: { key: string; name: string; words: string[] }[]
  }
  focus: Area[]
  not_tracked: string[]
  reviews: Review[]
  videos: Video[]
  board: Board
  areas: AreaBoard[]
  prices: PhonePrices[]
}

export type ReportCard = {
  id: string
  question: string
  checked_at: string
  sample: boolean
  reviews: number
  with_money_ties: number
  top_pick: string | null
  top_pick_price: number | null
}

export type LabelScore = {
  label: string
  key: number
  found: number
  right: number
  precision: number | null
  recall: number | null
  missed: string[]
  wrong: string[]
}

export type Accuracy = {
  videos: number
  scores: LabelScore[]
  per_label: Record<string, number>
}

export type Account = { mode: "live" | "replay"; searches_left: number | null }

/** One line of the live run, as the engine streams it. */
export type RunEvent =
  | { type: "start"; mode: "live" | "replay" }
  | {
      type: "tool"
      tool: string
      status: "start" | "done" | "error"
      step?: string
      [k: string]: unknown
    }
  | {
      type: "plan"
      plan: { queries: { text: string; hl: string }[] }
      must_haves: string[]
    }
  | { type: "selected"; keep: number; dropped: number }
  | {
      type: "video"
      v: string
      channel: string
      labels: string[]
      picks: number
    }
  | { type: "uses"; v: string; found: number }
  | { type: "cost"; searches_used: number; llm_calls: number }
  | { type: "result"; id: string; showcase: Report }
  | { type: "error"; status: number; detail: string }
