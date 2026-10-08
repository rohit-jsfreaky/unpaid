import type { Video } from "./types"

export const NO_DISCLOSURE = "No disclosure found"

export type LabelKey = "none" | "commission" | "brand" | "free" | "third"

export type LabelMeta = {
  key: LabelKey
  name: string
  short: string
  /** What the label means, for a shopper. */
  means: string
  /** What we need to see before we show it. */
  needs: string
}

/** Fixed order: it is the colour order the charts were checked with, and the order labels are listed in. */
export const LABELS: LabelMeta[] = [
  {
    key: "none",
    name: NO_DISCLOSURE,
    short: "No disclosure",
    means:
      "We found no sponsorship, free unit or commission in the video or its description.",
    needs:
      "Nothing found. It doesn't prove the reviewer is independent, only that nothing was disclosed.",
  },
  {
    key: "commission",
    name: "Earns commission",
    short: "Commission",
    means: "The reviewer gets paid when you buy through their link.",
    needs:
      "A shop link that carries the reviewer's affiliate ID, YouTube's own label, or the reviewer saying so.",
  },
  {
    key: "brand",
    name: "Brand-sponsored",
    short: "Brand deal",
    means: "The brand of a product in the video paid for or partnered on it.",
    needs:
      "The reviewer's own words: sponsored by, in partnership with, #Collab, naming the brand.",
  },
  {
    key: "free",
    name: "Free unit from the brand",
    short: "Free unit",
    means: "The brand sent the reviewer the product.",
    needs: "The reviewer saying the device was sent or provided by the brand.",
  },
  {
    key: "third",
    name: "Third-party sponsor",
    short: "Other sponsor",
    means:
      "Someone other than the product's brand sponsored the video, like an app or a website.",
    needs: "The reviewer naming the sponsor.",
  },
]

export const BY_NAME: Record<string, LabelMeta> = Object.fromEntries(
  LABELS.map((l) => [l.name, l])
)

/** The video's labels in the fixed order, or "No disclosure found". */
export function labelsOf(v: Video): LabelMeta[] {
  const names = new Set(v.labels.map((e) => e.label))
  const found = LABELS.filter((l) => l.key !== "none" && names.has(l.name))
  return found.length ? found : [LABELS[0]]
}

export function hasMoneyTie(v: Video): boolean {
  return v.labels.length > 0
}

/** CSS colour for a label, from globals.css. */
export const color = (key: LabelKey) => `var(--label-${key})`
