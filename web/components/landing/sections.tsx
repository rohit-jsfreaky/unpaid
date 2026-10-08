import {
  ArrowRightIcon,
  ArrowUpRightIcon,
  ChatTextIcon,
  LinkSimpleIcon,
  PlayCircleIcon,
  PlusIcon,
  QuotesIcon,
  StorefrontIcon,
  TranslateIcon,
  VideoCameraIcon,
} from "@phosphor-icons/react/dist/ssr"
import Link from "next/link"
import type { ReactNode } from "react"

import { Dot, LabelChip } from "@/components/label-chip"
import { Logo } from "@/components/logo"
import { distinctTopPicks, landing as L } from "@/content/landing"
import { day, pct, rupees, views } from "@/lib/format"
import { LABELS, NO_DISCLOSURE } from "@/lib/labels"
import { cn } from "@/lib/utils"

const REPORT = `/app/r/${L.report_id}`
const WORDS = [
  "no",
  "one",
  "two",
  "three",
  "four",
  "five",
  "six",
  "seven",
  "eight",
  "nine",
  "ten",
  "eleven",
  "twelve",
]
const word = (n: number) => WORDS[n] ?? String(n)

function Kicker({ children }: { children: ReactNode }) {
  return (
    <span className="font-mono text-[11px] font-medium tracking-[0.18em] text-faint uppercase">
      {children}
    </span>
  )
}

function Backdrop({
  tone,
  children,
}: {
  tone: "blue" | "sky" | "mint" | "slate"
  children: ReactNode
}) {
  const tones = {
    blue: "from-[#e3ebff] via-[#f1f5ff] to-[#eaf6ff]",
    sky: "from-[#e4f3fd] via-[#f2f9ff] to-[#eef2ff]",
    mint: "from-[#e3f6f1] via-[#f2fbf8] to-[#eaf3ff]",
    slate: "from-[#eef1f6] via-[#f7f8fb] to-[#e8eeff]",
  }
  return (
    <div
      className={cn(
        "relative rounded-[28px] bg-gradient-to-br p-6 shadow-[0_0_0_1px_rgb(15_23_42/0.05)] md:p-9",
        tones[tone]
      )}
    >
      <div className="rounded-2xl bg-white/90 p-5 shadow-[0_0_0_1px_rgb(255_255_255/0.9),0_14px_36px_-16px_rgb(15_23_42/0.18)] backdrop-blur-md md:p-6">
        {children}
      </div>
    </div>
  )
}

function MockHeader({ title, right }: { title: string; right: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-mist pb-3 font-mono text-[11px] text-faint">
      <span className="flex min-w-0 items-center gap-1.5 font-sans text-[12.5px] font-medium text-ink-2">
        <span className="size-1.5 shrink-0 rounded-full bg-klein" />
        <span className="truncate">{title}</span>
      </span>
      <span className="shrink-0">{right}</span>
    </div>
  )
}

function SeeIt({ href = REPORT, label }: { href?: string; label: string }) {
  return (
    <Link
      href={href}
      className="mt-7 inline-flex h-8 items-center gap-1.5 rounded-full bg-white px-3.5 text-[12.5px] font-medium text-ink-2 shadow-[0_0_0_1px_rgb(15_23_42/0.1)] transition-colors hover:bg-soft"
    >
      {label} <ArrowRightIcon weight="bold" className="size-3.5" />
    </Link>
  )
}

function Split({
  n,
  title,
  body,
  mock,
  flip = false,
  cta,
}: {
  n: number
  title: string
  body: ReactNode
  mock: ReactNode
  flip?: boolean
  cta: ReactNode
}) {
  return (
    <div className="grid grid-cols-1 items-center gap-12 md:grid-cols-2 md:gap-16">
      <div
        data-reveal
        className={cn(
          "flex flex-col items-start",
          flip ? "md:order-2 md:pl-4" : "md:pr-4"
        )}
      >
        <Kicker>0{n} / 04</Kicker>
        <h3 className="mt-3 text-[26px] leading-snug font-medium tracking-[-0.02em] md:text-[32px]">
          {title}
        </h3>
        <div className="mt-4 text-[15.5px] leading-relaxed text-muted-foreground">
          {body}
        </div>
        {cta}
      </div>
      <div data-reveal className={flip ? "md:order-1" : ""}>
        {mock}
      </div>
    </div>
  )
}

function Quote({
  text,
  meaning,
  lang,
}: {
  text: string
  meaning?: string | null
  lang?: string
}) {
  return (
    <figure className="rounded-xl bg-soft p-4 shadow-[0_0_0_1px_rgb(15_23_42/0.05)]">
      <QuotesIcon weight="fill" className="size-4 text-faint" />
      <blockquote className="mt-2 text-[14.5px] leading-relaxed text-ink">
        {text}
      </blockquote>
      {meaning ? (
        <figcaption className="mt-2.5 border-t border-mist pt-2.5 text-[12.5px] leading-relaxed text-muted-foreground">
          <span className="font-medium text-ink-2">
            {lang ? `${lang} → English: ` : "In English: "}
          </span>
          {meaning}
        </figcaption>
      ) : null}
    </figure>
  )
}

/* ---------- Statement + four split features ---------- */

export function Features() {
  const b = L.brand_example
  const s = L.spoken_example
  const top = L.phones.slice(0, 4)
  const g = L.groups
  return (
    <>
      <section className="border-t border-mist bg-white/40 px-6 py-24 text-center md:py-32">
        <p
          data-reveal
          className="mx-auto mb-5 font-mono text-[12px] text-faint"
        >
          Big Billion Days, {day(L.checked_at)}
        </p>
        <h2
          data-reveal
          className="mx-auto max-w-3xl text-[32px] leading-snug font-light tracking-[-0.03em] md:text-[46px]"
        >
          {L.reviews} new &ldquo;best phone under ₹30,000&rdquo; reviews.{" "}
          {distinctTopPicks} different #1 picks.{" "}
          <span className="font-normal text-[#020617]">Who do you trust?</span>
        </h2>
      </section>

      <section id="how" className="scroll-mt-24 px-6 py-16 md:py-24">
        <div className="mx-auto flex max-w-[1080px] flex-col gap-24 md:gap-36">
          <Split
            n={1}
            title="Who was paid, in their own words"
            body={
              <p>
                Every review gets a label: brand-sponsored, free unit from the
                brand, earns commission, another sponsor, or no disclosure
                found. Each label comes with the exact sentence it&apos;s based
                on and where it is. No sentence, no label.
              </p>
            }
            cta={<SeeIt label="See every label" />}
            mock={
              <Backdrop tone="blue">
                <MockHeader title={b.channel} right="From the description" />
                <p className="mt-4 line-clamp-2 text-[13.5px] font-medium text-ink">
                  {b.title}
                </p>
                <div className="mt-3">
                  <LabelChip name={b.label ?? ""} party={b.party} />
                </div>
                <div className="mt-4">
                  <Quote text={b.quote} />
                </div>
                {b.top_pick ? (
                  <p className="mt-4 text-[12px] leading-relaxed text-muted-foreground">
                    Their #1 pick in this video:{" "}
                    <span className="font-medium text-ink-2">{b.top_pick}</span>
                  </p>
                ) : null}
              </Backdrop>
            }
          />

          <Split
            n={2}
            flip
            title="We listen, not just read"
            body={
              <p>
                Most reviewers never put it in writing. They say it out loud,
                often in Hindi, Telugu or Malayalam. Unpaid goes through what
                they said in the video, shows their own words with an English
                meaning, and links to the second they said it.
              </p>
            }
            cta={<SeeIt label="Hear it at the timestamp" />}
            mock={
              <Backdrop tone="sky">
                <MockHeader
                  title={s.channel}
                  right={`Said at ${s.time_text}`}
                />
                <div className="mt-4 flex items-center gap-2">
                  <LabelChip name={s.label ?? ""} />
                  <span className="rounded-full bg-mist px-2.5 py-1 text-[12px] font-medium text-ink-2">
                    {s.language}
                  </span>
                </div>
                <div className="mt-4">
                  <Quote
                    text={s.quote}
                    meaning={s.meaning_en}
                    lang={s.language}
                  />
                </div>
                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-3 flex h-9 items-center justify-center gap-1.5 rounded-lg bg-klein-mist text-[12.5px] font-medium text-klein transition-colors hover:bg-klein-soft"
                >
                  <PlayCircleIcon weight="fill" className="size-4" /> Watch at{" "}
                  {s.time_text}
                </a>
              </Backdrop>
            }
          />

          <Split
            n={3}
            title="What the reviewers with nothing to disclose pick"
            body={
              <p>
                Unpaid puts the picks of reviewers with no money tie next to
                everyone else&apos;s. If the favourite only wins among paid
                reviewers, you&apos;ll see it. If it holds up, you can buy with
                more confidence.
              </p>
            }
            cta={<SeeIt label="Compare the picks" />}
            mock={
              <Backdrop tone="slate">
                <MockHeader
                  title="Picked by"
                  right={`${g.no_disclosure} vs ${g.disclosed} reviewers`}
                />
                <div className="mt-4 flex items-center gap-4 text-[11.5px] text-muted-foreground">
                  <span className="flex items-center gap-1.5">
                    <Dot k="none" /> No disclosure found
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Dot k="commission" /> Has a money tie
                  </span>
                </div>
                <div className="mt-4 flex flex-col gap-4">
                  {top.map((p) => (
                    <div key={p.name}>
                      <p className="text-[13px] font-medium text-ink">
                        {p.name}
                      </p>
                      <div className="mt-1.5 flex flex-col gap-1">
                        <Bar
                          value={p.no_disclosure}
                          of={g.no_disclosure}
                          k="none"
                        />
                        <Bar
                          value={p.disclosed}
                          of={g.disclosed}
                          k="commission"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Backdrop>
            }
          />

          <Split
            n={4}
            flip
            title="Today's price, from every seller"
            body={
              <p>
                For the phones the reviewers agree on, Unpaid checks what shops
                are asking right now and puts the lowest price first, with the
                time it was checked.
              </p>
            }
            cta={<SeeIt label="See today's prices" />}
            mock={
              <Backdrop tone="mint">
                <MockHeader
                  title={L.prices.phone}
                  right={`${L.prices.sellers} sellers`}
                />
                <ol className="mt-4 flex flex-col gap-1.5 font-mono text-[12.5px]">
                  {L.prices.offers.map((o, i) => (
                    <li
                      key={o.seller}
                      className={cn(
                        "flex items-center gap-3 rounded-lg px-3 py-2.5",
                        i === 0
                          ? "bg-klein-mist text-klein shadow-[0_0_0_1px_rgb(0_47_167/0.12)]"
                          : "bg-soft shadow-[0_0_0_1px_rgb(15_23_42/0.04)]"
                      )}
                    >
                      <span className="w-3 text-faint">{i + 1}</span>
                      <span
                        className={cn(
                          "flex-1 font-sans font-medium",
                          i === 0 ? "text-klein" : "text-ink"
                        )}
                      >
                        {o.seller}
                      </span>
                      <span className="font-semibold">{rupees(o.price)}</span>
                    </li>
                  ))}
                </ol>
                <p className="mt-4 border-t border-mist pt-3 font-mono text-[11px] text-faint">
                  Checked{" "}
                  {day(
                    L.prices.offers[0]?.searched_at
                      .replace(" UTC", "Z")
                      .replace(" ", "T")
                  )}
                </p>
              </Backdrop>
            }
          />
        </div>
      </section>
    </>
  )
}

function Bar({
  value,
  of,
  k,
}: {
  value: number
  of: number
  k: "none" | "commission"
}) {
  const share = of ? value / of : 0
  return (
    <div className="flex items-center gap-2.5">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-mist">
        <div
          className="h-full rounded-full"
          style={{ width: `${share * 100}%`, background: `var(--label-${k})` }}
        />
      </div>
      <span className="w-12 text-right font-mono text-[11px] text-ink-2 tnum">
        {value} of {of}
      </span>
    </div>
  )
}

/* ---------- Four cards ---------- */

const CARDS = [
  {
    icon: VideoCameraIcon,
    kicker: "01 · Reviews",
    title: "Every recent review",
    body: "The review videos posted in the last three weeks, in English and Hindi search, not just the top three.",
    tag: "Last 21 days",
    tone: "from-[#eaf0ff]",
  },
  {
    icon: ChatTextIcon,
    kicker: "02 · Proof",
    title: "The exact sentence",
    body: "Every label shows the words it's based on: from the description, or from what was said, with a timestamp.",
    tag: "No sentence, no label",
    tone: "from-[#e6f4fd]",
  },
  {
    icon: LinkSimpleIcon,
    kicker: "03 · Shop links",
    title: "Links that pay the reviewer",
    body: "Unpaid opens the shop links under each video and tells you which ones pay the reviewer when you buy.",
    tag: "Checked, not guessed",
    tone: "from-[#e5f6f1]",
  },
  {
    icon: StorefrontIcon,
    kicker: "04 · Prices",
    title: "What it costs today",
    body: "The lowest price for what reviewers agree on, from every shop that lists it, with the time checked.",
    tag: "Dated prices",
    tone: "from-[#eef1f6]",
  },
]

export function Cards() {
  return (
    <section className="border-y border-mist bg-soft/70 px-6 py-20 md:py-28">
      <div className="mx-auto max-w-[1140px] text-center">
        <h2
          data-reveal
          className="text-[28px] font-light tracking-[-0.03em] md:text-[40px]"
        >
          Everything the reviews didn&apos;t tell you,{" "}
          <span className="font-normal text-[#020617]">in one report</span>
        </h2>
        <p
          data-reveal
          className="mx-auto mt-3 max-w-lg text-[15px] text-muted-foreground"
        >
          For anyone about to spend real money on something because a video said
          so.
        </p>
        <div className="mt-14 grid grid-cols-1 gap-5 text-left sm:grid-cols-2 lg:grid-cols-4">
          {CARDS.map((c) => (
            <div
              key={c.title}
              data-reveal
              className={cn(
                "flex h-[290px] flex-col justify-between rounded-3xl bg-gradient-to-b to-white p-6 shadow-[0_0_0_1px_rgb(15_23_42/0.07)]",
                c.tone
              )}
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] tracking-wider text-faint uppercase">
                    {c.kicker}
                  </span>
                  <c.icon weight="duotone" className="size-5 text-klein" />
                </div>
                <h3 className="mt-3 text-[17px] font-medium tracking-tight">
                  {c.title}
                </h3>
                <p className="mt-2 text-[13.5px] leading-relaxed text-muted-foreground">
                  {c.body}
                </p>
              </div>
              <div className="flex items-center gap-1.5 border-t border-line/70 pt-4 font-mono text-[11px] font-medium text-klein">
                <span className="size-1.5 rounded-full bg-klein" />
                {c.tag}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ---------- What we found ---------- */

export function Study() {
  const fav = L.phones[0]
  const langs = Object.entries(L.languages).filter(([k]) => k !== "No captions")
  return (
    <section id="study" className="scroll-mt-24 px-6 py-20 md:py-28">
      <div className="mx-auto max-w-[1080px]">
        <div className="mb-12 flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div data-reveal>
            <Kicker>Big Billion Days 2026</Kicker>
            <h2 className="mt-2 text-[28px] font-medium tracking-[-0.03em] md:text-[40px]">
              What we found
            </h2>
          </div>
          <p
            data-reveal
            className="self-start rounded-full bg-white px-3.5 py-1.5 font-mono text-[12px] text-muted-foreground shadow-[0_0_0_1px_rgb(15_23_42/0.08)] md:self-auto"
          >
            {L.reviews} reviews · best phone under ₹30,000 · {day(L.checked_at)}
          </p>
        </div>

        <div className="mb-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          <div
            data-reveal
            className="flex flex-col justify-between rounded-3xl p-7 surface"
          >
            <div>
              <span className="block font-mono text-[38px] font-light text-[#020617] tnum">
                {L.with_ties} of {L.reviews}
              </span>
              <p className="mt-3 text-[14px] leading-relaxed text-muted-foreground">
                reviews had a money tie:{" "}
                {word(L.per_label["Earns commission"] ?? 0)} earn commission
                when you buy, and {word(L.per_label["Brand-sponsored"] ?? 0)}{" "}
                was made with a phone brand.
              </p>
            </div>
            <p className="mt-6 border-t border-mist pt-4 font-mono text-[11px] text-faint">
              Disclosed money ties
            </p>
          </div>
          <div
            data-reveal
            className="flex flex-col justify-between rounded-3xl bg-gradient-to-b from-[#f4f6fa] to-white p-7 surface"
          >
            <div>
              <span className="block font-mono text-[38px] font-light text-ink tnum">
                {L.paid_links} links
              </span>
              <p className="mt-3 text-[14px] leading-relaxed text-ink-2">
                under {word(L.videos_with_paid_links)} videos pay the reviewer
                when you buy through them. Most never say so in the video.
              </p>
            </div>
            <p className="mt-6 border-t border-mist pt-4 font-mono text-[11px] text-faint">
              Shop links checked
            </p>
          </div>
          <div
            data-reveal
            className="flex flex-col justify-between rounded-3xl bg-gradient-to-b from-klein-mist to-white p-7 surface"
          >
            <div>
              <div className="flex items-center justify-between">
                <span className="block font-mono text-[38px] font-light text-klein tnum">
                  {fav.no_disclosure} of {L.groups.no_disclosure}
                </span>
                <span className="rounded-full bg-klein-soft px-2 py-0.5 font-mono text-[10px] font-bold text-klein uppercase">
                  Holds up
                </span>
              </div>
              <p className="mt-3 text-[14px] leading-relaxed text-ink-2">
                reviewers with nothing to disclose still pick the {fav.name},
                the overall favourite. It&apos;s{" "}
                {rupees(L.prices.offers[0]?.price)} today.
              </p>
            </div>
            <p className="mt-6 border-t border-klein-soft pt-4 font-mono text-[11px] text-klein">
              The favourite, checked
            </p>
          </div>
        </div>

        {L.focus.length ? (
          <div data-reveal className="mb-12">
            <p className="mb-4 text-[14px] text-muted-foreground">
              The question asked for{" "}
              <span className="font-medium text-ink">
                {L.must_haves.join(" and ")}
              </span>
              . Here&apos;s what reviewers with nothing to disclose praise, in
              their own words:
            </p>
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              {L.focus.map((f) => (
                <div
                  key={f.area}
                  className="flex flex-col gap-4 rounded-3xl p-6 surface"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <Kicker>Best for {f.area}</Kicker>
                      <p className="mt-2 text-[20px] font-medium tracking-tight text-ink">
                        {f.best ?? "No clear pick"}
                      </p>
                    </div>
                    {f.price ? (
                      <span className="shrink-0 rounded-full bg-klein-mist px-3 py-1 font-mono text-[12px] font-medium text-klein tnum">
                        {rupees(f.price)} today
                      </span>
                    ) : null}
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Bar
                      value={f.no_disclosure}
                      of={f.of_no_disclosure}
                      k="none"
                    />
                    <Bar
                      value={f.disclosed}
                      of={f.of_disclosed}
                      k="commission"
                    />
                    <p className="text-[12px] text-muted-foreground">
                      Praised by {f.no_disclosure} of {f.of_no_disclosure}{" "}
                      reviewers with nothing to disclose and {f.disclosed} of{" "}
                      {f.of_disclosed} with a money tie.
                      {f.weak ? "" : " None call it weak."}
                    </p>
                  </div>
                  {f.quote ? (
                    <div className="mt-auto">
                      <Quote
                        text={f.quote}
                        meaning={f.language !== "English" ? f.meaning_en : null}
                        lang={f.language ?? undefined}
                      />
                      <p className="mt-2 flex items-center justify-between text-[12px] text-muted-foreground">
                        <span>{f.channel}</span>
                        {f.url ? (
                          <a
                            href={f.url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 font-medium text-klein hover:underline"
                          >
                            <PlayCircleIcon
                              weight="fill"
                              className="size-3.5"
                            />{" "}
                            Watch at {f.time_text}
                          </a>
                        ) : null}
                      </p>
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ) : null}

        <div data-reveal className="overflow-hidden rounded-2xl surface">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-left text-[13px]">
              <thead>
                <tr className="border-b border-line bg-soft/80 font-mono text-[11px] tracking-wider text-faint uppercase">
                  <th className="px-5 py-3 font-medium">Reviewer</th>
                  <th className="px-5 py-3 font-medium">Spoken in</th>
                  <th className="px-5 py-3 text-right font-medium">Views</th>
                  <th className="px-5 py-3 font-medium">What we found</th>
                  <th className="px-5 py-3 font-medium">Their #1 pick</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-mist">
                {L.rows.slice(0, 10).map((r, i) => (
                  <tr
                    key={`${r.channel}-${i}`}
                    className="transition-colors hover:bg-soft/70"
                  >
                    <td className="px-5 py-3 text-[13.5px] font-medium text-ink">
                      {r.channel}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {r.language ?? "—"}
                    </td>
                    <td className="px-5 py-3 text-right font-mono text-[12px] text-ink-2 tnum">
                      {views(r.views)}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex flex-wrap gap-1.5">
                        {r.labels.map((l) => (
                          <LabelChip key={l} name={l} size="sm" />
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-ink-2">
                      {r.top_pick ?? (
                        <span className="text-faint">No list</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-mist bg-soft/60 px-5 py-3 text-[12.5px]">
            <span className="text-muted-foreground">
              Top 10 by views of {L.reviews}. Reviews in{" "}
              {langs.map(([k, n]) => `${k} (${n})`).join(", ")}.
            </span>
            <Link
              href={`${REPORT}/reviews`}
              className="inline-flex items-center gap-1 font-medium text-klein hover:underline"
            >
              See all {L.reviews}{" "}
              <ArrowUpRightIcon weight="bold" className="size-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ---------- What each label means ---------- */

export function Labels() {
  const d = L.denial_example
  const commission = L.accuracy.find((a) => a.label === "Earns commission")
  // Money-tie labels Unpaid gave that the line-by-line read didn't agree with.
  const wrong = L.accuracy
    .filter((a) => a.label !== NO_DISCLOSURE)
    .reduce((n, a) => n + (a.found - a.right), 0)
  const missed = (commission?.missed ?? []).map((channel) => ({
    channel,
    language: L.rows.find((r) => r.channel === channel)?.language,
  }))
  return (
    <section className="border-t border-mist bg-white px-6 py-20 md:py-28">
      <div className="mx-auto max-w-[1080px]">
        <div data-reveal className="max-w-xl">
          <Kicker>How we label</Kicker>
          <h2 className="mt-2 text-[28px] font-medium tracking-[-0.03em] md:text-[40px]">
            We show what was disclosed. Not who&apos;s honest.
          </h2>
        </div>
        <div className="mt-12 grid gap-4 md:grid-cols-5">
          {LABELS.map((l) => (
            <div
              key={l.key}
              data-reveal
              className="flex flex-col rounded-3xl p-6 surface"
            >
              <span className="flex items-center gap-2">
                <Dot k={l.key} className="size-2.5" />
                <span className="text-[14.5px] font-medium tracking-tight text-ink">
                  {l.name}
                </span>
              </span>
              <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
                {l.means}
              </p>
              <p className="mt-auto border-t border-mist pt-3 text-[12px] leading-relaxed text-ink-2">
                <span className="font-medium">We need: </span>
                {l.needs}
              </p>
            </div>
          ))}
        </div>

        <div data-reveal className="mt-5 grid gap-5 md:grid-cols-2">
          <div className="rounded-3xl bg-soft p-7 shadow-[0_0_0_1px_rgb(15_23_42/0.05)]">
            <p className="font-mono text-[11px] tracking-[0.18em] text-faint uppercase">
              What a denial looks like
            </p>
            <div className="mt-4">
              <Quote text={d.quote} />
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-muted-foreground">
              {d.channel} says so in the video. We show it as a note, never as a
              label, and the review stays &ldquo;
              {NO_DISCLOSURE}&rdquo;.
            </p>
          </div>
          <div className="rounded-3xl bg-soft p-7 shadow-[0_0_0_1px_rgb(15_23_42/0.05)]">
            <p className="font-mono text-[11px] tracking-[0.18em] text-faint uppercase">
              How accurate it is
            </p>
            <p className="mt-4 text-[15px] leading-relaxed text-ink">
              We compared Unpaid&apos;s labels with a line-by-line read of all{" "}
              {L.reviews} reviews.{" "}
              {wrong === 0
                ? "Every money-tie label it gave was right."
                : `${wrong} of its money-tie labels were wrong.`}{" "}
              It caught {commission?.right} of the {commission?.key} reviewers
              who earn commission
              {missed.length
                ? `. It missed ${missed.map((m) => `${m.channel}${m.language ? `, who said it in ${m.language}` : ""}`).join("; ")}.`
                : "."}
            </p>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <Stat
                value={pct(commission?.precision)}
                label="of commission labels were right"
              />
              <Stat
                value={pct(commission?.recall)}
                label="of commission ties were caught"
              />
            </div>
          </div>
        </div>

        <div
          data-reveal
          className="mt-5 grid gap-6 rounded-3xl bg-soft p-7 shadow-[0_0_0_1px_rgb(15_23_42/0.05)] md:grid-cols-[auto_1fr_1fr_1fr]"
        >
          <p className="font-mono text-[11px] tracking-[0.18em] text-faint uppercase">
            Good to know
          </p>
          <p className="text-[14px] leading-relaxed text-muted-foreground">
            &ldquo;{NO_DISCLOSURE}&rdquo; doesn&apos;t mean independent. It
            means nothing was disclosed.
          </p>
          <p className="text-[14px] leading-relaxed text-muted-foreground">
            What was said comes from YouTube&apos;s captions, which can be
            auto-made and imperfect.
          </p>
          <p className="text-[14px] leading-relaxed text-muted-foreground">
            Prices change all day. Every price shows when it was checked.
          </p>
        </div>
      </div>
    </section>
  )
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="rounded-2xl bg-white p-4 shadow-[0_0_0_1px_rgb(15_23_42/0.06)]">
      <span className="block font-mono text-[26px] font-light text-ink tnum">
        {value}
      </span>
      <span className="mt-1 block text-[12px] leading-snug text-muted-foreground">
        {label}
      </span>
    </div>
  )
}

/* ---------- FAQ ---------- */

const FAQ = [
  {
    q: "Isn't earning commission normal?",
    a: "It is, and it doesn't make a review dishonest. It is a money tie you deserve to know about before you buy through that link. Unpaid shows it, then lets you compare with reviewers who have none.",
  },
  {
    q: "Does “No disclosure found” mean the reviewer is independent?",
    a: "No. It means we found nothing disclosed: no sponsor, no free unit, no paying links. Someone can still have a tie they never mention, so we never call anyone independent.",
  },
  {
    q: "Do you cover Hindi and regional reviews?",
    a: "Yes. Unpaid goes through what was said in Hindi, Telugu, Malayalam and English. It shows the reviewer's own words and an English meaning next to them.",
  },
  {
    q: "Are you accusing creators of anything?",
    a: "No. We only show what creators published themselves, in their descriptions and their own videos, with a link to the exact place. Creators who disclose clearly are doing the right thing.",
  },
  {
    q: "How fresh is a report?",
    a: "Each report looks at reviews from the last three weeks and shows the date it was made. Prices show the time they were checked.",
  },
]

export function Faq() {
  return (
    <section
      id="faq"
      className="scroll-mt-24 border-t border-mist bg-white px-6 py-20 md:py-28"
    >
      <div className="mx-auto grid max-w-[1080px] grid-cols-1 gap-8 md:grid-cols-12 md:gap-12">
        <h2
          data-reveal
          className="text-[32px] leading-tight font-light tracking-[-0.03em] md:col-span-4 md:text-[40px]"
        >
          Frequently
          <br />
          <span className="font-normal text-[#020617]">asked questions</span>
        </h2>
        <div className="divide-y divide-mist md:col-span-8">
          {FAQ.map((f) => (
            <details key={f.q} data-reveal className="group py-5 first:pt-0">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-6 text-[15.5px] font-medium text-ink [&::-webkit-details-marker]:hidden">
                {f.q}
                <PlusIcon
                  weight="bold"
                  className="size-4 shrink-0 text-faint transition-transform duration-300 group-open:rotate-45"
                />
              </summary>
              <p className="mt-3 pr-6 text-[14.5px] leading-relaxed text-muted-foreground">
                {f.a}
              </p>
            </details>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ---------- Closing + footer ---------- */

export function Closing() {
  return (
    <section className="relative overflow-hidden px-6 pt-32 pb-36 text-center">
      <div className="pointer-events-none absolute inset-0 glow-bottom" />
      <div className="relative mx-auto flex max-w-[720px] flex-col items-center">
        <h2
          data-reveal
          className="text-[36px] leading-tight font-light tracking-[-0.035em] md:text-[54px]"
        >
          Before you buy,
          <br />
          <span className="font-normal text-[#020617]">
            see who&apos;s getting paid.
          </span>
        </h2>
        <p
          data-reveal
          className="mt-4 max-w-md text-[15.5px] leading-relaxed text-muted-foreground"
        >
          Ask for what you want to buy. Unpaid goes through the reviews, the
          money ties and today&apos;s prices for you.
        </p>
        <div
          data-reveal
          className="mt-9 flex flex-wrap items-center justify-center gap-3"
        >
          <Link
            href="/app"
            className="inline-flex h-10 items-center gap-2 rounded-full px-5 text-[13.5px] font-medium text-white gloss-dark transition-transform hover:-translate-y-px"
          >
            Open Unpaid <ArrowRightIcon weight="bold" className="size-4" />
          </Link>
          <Link
            href={REPORT}
            className="inline-flex h-10 items-center gap-2 rounded-full bg-white px-5 text-[13.5px] font-medium text-ink-2 shadow-[0_0_0_1px_rgb(15_23_42/0.1)] transition-colors hover:bg-soft"
          >
            <TranslateIcon weight="duotone" className="size-4 text-klein" /> See
            the Big Billion Days report
          </Link>
        </div>
      </div>
    </section>
  )
}

export function Footer() {
  return (
    <footer className="w-full border-t border-mist bg-white px-6 py-10">
      <div className="mx-auto flex max-w-[1140px] flex-col items-center justify-between gap-6 text-[12.5px] text-faint sm:flex-row">
        <Logo />
        <nav className="flex items-center gap-6">
          <a href="#how" className="transition-colors hover:text-ink-2">
            How it works
          </a>
          <a href="#study" className="transition-colors hover:text-ink-2">
            What we found
          </a>
          <a href="#faq" className="transition-colors hover:text-ink-2">
            FAQ
          </a>
          <Link href="/app" className="transition-colors hover:text-ink-2">
            Open Unpaid
          </Link>
        </nav>
        <div className="flex items-center gap-4">
          <a
            href="https://serpapi.com"
            target="_blank"
            rel="noreferrer"
            className="rounded-full bg-soft px-3 py-1 font-medium text-ink-2 shadow-[0_0_0_1px_rgb(15_23_42/0.08)] transition-colors hover:bg-mist"
          >
            Built with SerpApi
          </a>
          <span>© 2026 Unpaid</span>
        </div>
      </div>
    </footer>
  )
}
