import { BY_NAME, color, LABELS, type LabelKey } from "@/lib/labels"
import { cn } from "@/lib/utils"

/** A label as a chip: the label's colour as a dot, its name in ink (text never wears the series colour). */
export function LabelChip({
  name,
  party,
  size = "md",
  className,
}: {
  name: string
  party?: string | null
  size?: "sm" | "md"
  className?: string
}) {
  const meta = BY_NAME[name] ?? LABELS[0]
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center gap-1.5 rounded-full bg-white font-medium whitespace-nowrap text-ink-2 shadow-[0_0_0_1px_rgb(15_23_42/0.1)]",
        size === "sm"
          ? "px-2 py-0.5 text-[11.5px]"
          : "px-2.5 py-1 text-[12.5px]",
        className
      )}
    >
      <Dot k={meta.key} />
      <span className="truncate">
        {meta.name}
        {party ? (
          <span className="text-muted-foreground"> · {party}</span>
        ) : null}
      </span>
    </span>
  )
}

export function Dot({ k, className }: { k: LabelKey; className?: string }) {
  return (
    <span
      aria-hidden
      className={cn("size-2 shrink-0 rounded-full", className)}
      style={{ background: color(k) }}
    />
  )
}
