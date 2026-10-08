const inr = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
})
const compact = new Intl.NumberFormat("en-IN", {
  notation: "compact",
  maximumFractionDigits: 1,
})

/** ₹25,799, or "—" when there's no price. */
export const rupees = (n: number | null | undefined) =>
  n == null ? "—" : inr.format(n)

/** 1.3M views, 702K. */
export const views = (n: number | null | undefined) =>
  n == null ? "—" : compact.format(n)

export const pct = (x: number | null | undefined) =>
  x == null ? "—" : `${Math.round(x * 100)}%`

/** 8 Oct 2026 */
export const day = (iso: string | null | undefined) =>
  iso
    ? new Date(iso).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : "—"

/** 8 Oct, 10:49 pm */
export const stamp = (iso: string | null | undefined) =>
  iso
    ? new Date(iso).toLocaleString("en-IN", {
        day: "numeric",
        month: "short",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
      })
    : "—"

/** "3 days ago" from an ISO date, relative to `now`. */
export function ago(iso: string | null | undefined, now: Date): string {
  if (!iso) return "—"
  const days = Math.max(
    0,
    Math.round((now.getTime() - new Date(iso).getTime()) / 86_400_000)
  )
  if (days === 0) return "today"
  if (days === 1) return "yesterday"
  if (days < 7) return `${days} days ago`
  const w = Math.round(days / 7)
  return w === 1 ? "1 week ago" : `${w} weeks ago`
}

const LANG: Record<string, string> = {
  latin: "English",
  devanagari: "Hindi",
  telugu: "Telugu",
  malayalam: "Malayalam",
  tamil: "Tamil",
  bengali: "Bengali",
  gujarati: "Gujarati",
  kannada: "Kannada",
  mixed: "Mixed",
}

/** The language a viewer would call it, from the captions' script. */
export const language = (script: string | null | undefined) =>
  script ? (LANG[script] ?? "Other") : "No captions"

/** "Best phone under 30k for camera and battery, big billion days" → sentence case, no trailing dot. */
export const sentence = (q: string) => (q ? q[0].toUpperCase() + q.slice(1) : q)
