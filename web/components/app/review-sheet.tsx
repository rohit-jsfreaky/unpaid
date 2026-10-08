"use client"

import {
  ArrowSquareOutIcon,
  LinkSimpleIcon,
  NoteIcon,
  PlayCircleIcon,
  QuotesIcon,
  TextAlignLeftIcon,
} from "@phosphor-icons/react"
import Image from "next/image"

import { LabelChip } from "@/components/label-chip"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { day, language, views } from "@/lib/format"
import { labelsOf } from "@/lib/labels"
import type { Evidence, Review, Video } from "@/lib/types"

/** Where a piece of proof was found, in a shopper's words. */
function where(e: Evidence): { icon: typeof PlayCircleIcon; text: string } {
  switch (e.source) {
    case "transcript":
      return {
        icon: PlayCircleIcon,
        text: `Said in the video at ${e.time_text}`,
      }
    case "description":
      return { icon: TextAlignLeftIcon, text: "Written in the description" }
    case "description_link":
      return { icon: LinkSimpleIcon, text: "Shop links in the description" }
    default:
      return { icon: NoteIcon, text: "YouTube's own label on the video" }
  }
}

export function Proof({ e, english }: { e: Evidence; english: boolean }) {
  const w = where(e)
  return (
    <div className="rounded-xl bg-soft p-4 shadow-[0_0_0_1px_rgb(15_23_42/0.05)]">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <LabelChip
          name={e.label}
          party={e.source === "description_link" ? null : e.party}
          size="sm"
        />
        <span className="inline-flex items-center gap-1.5 text-[12px] text-muted-foreground">
          <w.icon weight="duotone" className="size-3.5" /> {w.text}
        </span>
      </div>
      <figure className="mt-3">
        <QuotesIcon weight="fill" className="size-3.5 text-faint" />
        <blockquote className="mt-1.5 text-[14px] leading-relaxed break-words text-ink">
          {e.quote}
        </blockquote>
        {e.meaning_en && (!english || e.source === "description_link") ? (
          <figcaption className="mt-2 text-[12.5px] leading-relaxed text-muted-foreground">
            <span className="font-medium text-ink-2">
              {e.source === "description_link" ? "Checked: " : "In English: "}
            </span>
            {e.meaning_en}
          </figcaption>
        ) : null}
        {e.source === "description_link" && e.party ? (
          <figcaption className="mt-1 text-[12.5px] text-muted-foreground">
            {e.party}
          </figcaption>
        ) : null}
      </figure>
      {e.source === "transcript" ? (
        <a
          href={e.url}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-flex items-center gap-1.5 text-[12.5px] font-medium text-klein hover:underline"
        >
          <PlayCircleIcon weight="fill" className="size-4" /> Watch at{" "}
          {e.time_text}
        </a>
      ) : null}
    </div>
  )
}

export function ReviewSheet({
  row,
  onOpenChange,
}: {
  row: { video: Video; review: Review } | null
  onOpenChange: (open: boolean) => void
}) {
  const v = row?.video
  const r = row?.review
  const english = r?.language === "latin" || !r?.language
  return (
    <Sheet open={row !== null} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full gap-0 overflow-y-auto p-0 data-[side=right]:sm:max-w-[560px]"
      >
        {v && r ? (
          <>
            <div className="relative aspect-video w-full shrink-0 overflow-hidden bg-mist">
              <Image
                src={r.thumbnail}
                alt=""
                fill
                sizes="560px"
                className="object-cover"
              />
            </div>
            <SheetHeader className="gap-2 px-6 pt-5">
              <div className="flex flex-wrap gap-1.5">
                {labelsOf(v).map((l) => (
                  <LabelChip key={l.key} name={l.name} size="sm" />
                ))}
              </div>
              <SheetTitle className="text-[18px] leading-snug">
                {v.title}
              </SheetTitle>
              <SheetDescription>
                {v.channel} · {views(v.views)} views · {day(r.published)} ·{" "}
                {language(r.language)}
              </SheetDescription>
              <a
                href={v.link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex w-fit items-center gap-1.5 text-[13px] font-medium text-klein hover:underline"
              >
                Open on YouTube{" "}
                <ArrowSquareOutIcon weight="bold" className="size-3.5" />
              </a>
            </SheetHeader>

            <div className="flex flex-col gap-6 px-6 py-6">
              <section>
                <h3 className="text-[13px] font-medium text-ink">Money ties</h3>
                {v.labels.length ? (
                  <div className="mt-3 flex flex-col gap-3">
                    {v.labels.map((e, i) => (
                      <Proof key={i} e={e} english={english} />
                    ))}
                  </div>
                ) : (
                  <p className="mt-2 text-[13px] leading-relaxed text-muted-foreground">
                    No sponsorship, free unit or paying shop link found in the
                    description
                    {r.has_transcript
                      ? " or in what was said"
                      : ". YouTube had no captions for this video, so what was said wasn't checked"}
                    . That doesn&apos;t prove the reviewer is independent.
                  </p>
                )}
              </section>

              {v.denials.length ? (
                <section>
                  <h3 className="text-[13px] font-medium text-ink">
                    What the reviewer says about it
                  </h3>
                  <div className="mt-3 flex flex-col gap-2">
                    {v.denials.map((d, i) => (
                      <div
                        key={i}
                        className="rounded-xl bg-white p-3.5 text-[13px] shadow-[0_0_0_1px_rgb(15_23_42/0.07)]"
                      >
                        <p className="leading-relaxed text-ink">
                          &ldquo;{d.quote}&rdquo;
                        </p>
                        {!english && d.meaning_en ? (
                          <p className="mt-1.5 text-muted-foreground">
                            {d.meaning_en}
                          </p>
                        ) : null}
                        <p className="mt-1.5 text-[12px] text-faint">
                          {d.source === "transcript"
                            ? `Said at ${d.time_text}`
                            : "In the description"}{" "}
                          · shown as a note, not a label
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              ) : null}

              <Separator />

              <section>
                <h3 className="text-[13px] font-medium text-ink">
                  What they recommend
                </h3>
                {v.picks.length ? (
                  <ol className="mt-3 flex flex-col divide-y divide-mist rounded-xl bg-white shadow-[0_0_0_1px_rgb(15_23_42/0.07)]">
                    {[...v.picks]
                      .sort((a, b) => (a.rank ?? 99) - (b.rank ?? 99))
                      .map((p, i) => (
                        <li key={i} className="flex gap-3 p-3.5">
                          <span className="mt-0.5 w-5 shrink-0 font-mono text-[12px] text-faint tnum">
                            {p.rank ? `#${p.rank}` : "·"}
                          </span>
                          <div className="min-w-0">
                            <p className="text-[13.5px] font-medium text-ink">
                              {p.phone}
                            </p>
                            <p className="mt-1 line-clamp-2 text-[12.5px] leading-relaxed text-muted-foreground">
                              &ldquo;{english ? p.quote : p.meaning_en}&rdquo;
                            </p>
                            {p.time_text ? (
                              <a
                                href={p.url}
                                target="_blank"
                                rel="noreferrer"
                                className="mt-1 inline-flex items-center gap-1 text-[12px] font-medium text-klein hover:underline"
                              >
                                <PlayCircleIcon
                                  weight="fill"
                                  className="size-3.5"
                                />{" "}
                                {p.time_text}
                              </a>
                            ) : null}
                          </div>
                        </li>
                      ))}
                  </ol>
                ) : (
                  <p className="mt-2 text-[13px] text-muted-foreground">
                    No list of picks we could read in this video.
                  </p>
                )}
              </section>
            </div>
          </>
        ) : null}
      </SheetContent>
    </Sheet>
  )
}
