"use client"

import { ArrowUpIcon } from "@phosphor-icons/react"
import { useRouter } from "next/navigation"
import { useState } from "react"

import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group"

/** `examples`: questions that already have a report, so a click opens a check that works. */
export function AskBox({
  initial = "",
  examples = [],
}: {
  initial?: string
  examples?: string[]
}) {
  const router = useRouter()
  const [q, setQ] = useState(initial)
  const go = (text: string) => {
    const t = text.trim()
    if (t) router.push(`/app/check?q=${encodeURIComponent(t)}`)
  }
  return (
    <div id="ask" className="flex flex-col gap-3">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          go(q)
        }}
      >
        <InputGroup className="h-auto rounded-2xl bg-card! shadow-[0_0_0_1px_rgb(15_23_42/0.06),0_18px_45px_-20px_rgb(15_23_42/0.18)]">
          <InputGroupTextarea
            rows={2}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                go(q)
              }
            }}
            aria-label="What do you want to buy?"
            placeholder="What do you want to buy? e.g. best phone under ₹30k for camera and battery"
            className="min-h-16 text-[15px]"
          />
          <InputGroupAddon align="block-end" className="justify-between">
            <span className="text-[12px] text-muted-foreground">
              We check reviews from the last 3 weeks
            </span>
            <InputGroupButton
              type="submit"
              variant="default"
              size="icon-sm"
              className="rounded-full"
              disabled={!q.trim()}
              aria-label="Check reviews"
            >
              <ArrowUpIcon weight="bold" />
            </InputGroupButton>
          </InputGroupAddon>
        </InputGroup>
      </form>
      {examples.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 text-[12.5px]">
          <span className="text-faint">Try:</span>
          {examples.map((e) => (
            <button
              key={e}
              type="button"
              onClick={() => go(e)}
              className="rounded-full bg-white px-3 py-1 font-medium text-ink-2 shadow-[0_0_0_1px_rgb(15_23_42/0.08)] transition-colors hover:bg-soft"
            >
              {e}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
