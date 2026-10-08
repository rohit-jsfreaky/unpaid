"use client"

import {
  CalendarBlankIcon,
  FileXIcon,
  LinkSimpleIcon,
  MagnifyingGlassIcon,
  VideoCameraIcon,
} from "@phosphor-icons/react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import type { ReactNode } from "react"
import { toast } from "sonner"

import { useReport } from "@/components/app/report-context"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty"
import { Skeleton } from "@/components/ui/skeleton"
import { day, sentence } from "@/lib/format"
import { productWords } from "@/lib/product"
import { cn } from "@/lib/utils"

const TABS = [
  { slug: "", label: "Overview" },
  { slug: "/reviews", label: "Reviews" },
  { slug: "/products", label: "Products" },
  { slug: "/prices", label: "Prices" },
]

export function ReportGate({ children }: { children: ReactNode }) {
  const state = useReport()
  const path = usePathname()

  if (state.status === "loading") {
    return (
      <div className="flex flex-col gap-6 pt-6">
        <Skeleton className="h-9 w-2/3" />
        <Skeleton className="h-5 w-1/3" />
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-32 rounded-2xl" />
          ))}
        </div>
        <Skeleton className="h-80 rounded-2xl" />
      </div>
    )
  }

  if (state.status === "error") {
    return (
      <Empty className="mt-16">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <FileXIcon weight="duotone" />
          </EmptyMedia>
          <EmptyTitle>{state.title}</EmptyTitle>
          <EmptyDescription>{state.body}</EmptyDescription>
        </EmptyHeader>
        <EmptyContent>
          <Button nativeButton={false} render={<Link href="/app" />}>
            Back to your reports
          </Button>
        </EmptyContent>
      </Empty>
    )
  }

  const { report, sample } = state
  const base = `/app/r/${report.id}`
  return (
    <div className="flex flex-col gap-6 pt-4">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            {sample ? <Badge variant="secondary">Sample report</Badge> : null}
            <Badge variant="outline">
              {productWords(report.product).title}
            </Badge>
          </div>
          <h1 className="mt-3 text-[26px] leading-tight font-medium tracking-[-0.02em] text-ink md:text-[32px]">
            {sentence(report.question)}
          </h1>
          <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[13px] text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <CalendarBlankIcon weight="duotone" className="size-4" /> Checked{" "}
              {day(report.checked_at)}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <VideoCameraIcon weight="duotone" className="size-4" />{" "}
              {report.videos.length} reviews from the last 3 weeks
            </span>
            <span className="inline-flex items-center gap-1.5">
              <MagnifyingGlassIcon weight="duotone" className="size-4" />{" "}
              {report.videos_found} videos looked at
            </span>
          </div>
          {report.must_haves.length ? (
            <div className="mt-3 flex flex-wrap items-center gap-1.5 text-[12.5px]">
              <span className="text-muted-foreground">You asked for:</span>
              {report.must_haves.map((m) => (
                <Badge key={m} variant="outline" className="capitalize">
                  {m}
                </Badge>
              ))}
              {report.not_tracked.length ? (
                <span className="text-faint">
                  ({report.not_tracked.join(", ")} not ranked yet)
                </span>
              ) : null}
            </div>
          ) : null}
        </div>
        <Button
          variant="outline"
          onClick={() => {
            navigator.clipboard.writeText(window.location.href).then(
              () => toast.success("Link copied"),
              () => toast.error("Couldn't copy the link")
            )
          }}
        >
          <LinkSimpleIcon data-icon="inline-start" />
          Copy link
        </Button>
      </div>

      <nav className="flex max-w-full gap-1 self-start overflow-x-auto rounded-full bg-mist/80 p-1 text-[13px] font-medium whitespace-nowrap">
        {TABS.map((t) => {
          const href = `${base}${t.slug}`
          const active = path === href
          return (
            <Link
              key={t.label}
              href={href}
              className={cn(
                "rounded-full px-3.5 py-1.5 transition-all",
                active
                  ? "bg-white text-ink shadow-[0_0_0_1px_rgb(15_23_42/0.06),0_2px_6px_-2px_rgb(15_23_42/0.12)]"
                  : "text-muted-foreground hover:text-ink"
              )}
            >
              {t.slug === "/products"
                ? productWords(report.product).title
                : t.label}
            </Link>
          )
        })}
      </nav>

      {children}
    </div>
  )
}
