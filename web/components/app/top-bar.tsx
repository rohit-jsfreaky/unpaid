"use client"

import { ArrowUpRightIcon } from "@phosphor-icons/react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"

const TITLES: [RegExp, string][] = [
  [/^\/app\/r\/[^/]+\/reviews$/, "Reviews"],
  [/^\/app\/r\/[^/]+\/products$/, "Products"],
  [/^\/app\/r\/[^/]+\/prices$/, "Prices"],
  [/^\/app\/r\/[^/]+$/, "Overview"],
  [/^\/app\/check/, "New check"],
  [/^\/app\/method$/, "How we label"],
  [/^\/app$/, "Home"],
]

export function TopBar() {
  const path = usePathname()
  const title = TITLES.find(([re]) => re.test(path))?.[1] ?? "Unpaid"
  const inReport = path.startsWith("/app/r/")
  return (
    <header className="relative z-10 flex h-14 shrink-0 items-center justify-between gap-2 px-4 md:px-6">
      <div className="flex items-center gap-2">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-1 data-vertical:h-4" />
        <Breadcrumb>
          <BreadcrumbList>
            {inReport ? (
              <>
                <BreadcrumbItem className="hidden md:block">
                  Reports
                </BreadcrumbItem>
                <BreadcrumbSeparator className="hidden md:block" />
              </>
            ) : null}
            <BreadcrumbItem>
              <BreadcrumbPage>{title}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>
      <Link
        href="/"
        className="hidden items-center gap-1 text-[12.5px] font-medium text-muted-foreground transition-colors hover:text-ink sm:inline-flex"
      >
        About Unpaid <ArrowUpRightIcon weight="bold" className="size-3" />
      </Link>
    </header>
  )
}
