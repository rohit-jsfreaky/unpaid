"use client"

import {
  ArrowUpRightIcon,
  ChartPieSliceIcon,
  DeviceMobileIcon,
  FileTextIcon,
  HouseIcon,
  PlusCircleIcon,
  SealCheckIcon,
  TagIcon,
  VideoCameraIcon,
} from "@phosphor-icons/react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useEffect, useState } from "react"

import { Mark } from "@/components/logo"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import { sentence } from "@/lib/format"
import type { ReportCard } from "@/lib/types"

const REPORT_TABS = [
  { slug: "", label: "Overview", icon: ChartPieSliceIcon },
  { slug: "/reviews", label: "Reviews", icon: VideoCameraIcon },
  { slug: "/products", label: "Products", icon: DeviceMobileIcon },
  { slug: "/prices", label: "Prices", icon: TagIcon },
]

export function AppSidebar() {
  const path = usePathname()
  const [reports, setReports] = useState<ReportCard[] | null>(null)
  useEffect(() => {
    api
      .reports()
      .then(setReports)
      .catch(() => setReports([]))
  }, [path])

  const reportBase = path.match(/^\/app\/r\/[^/]+/)?.[0]

  // On phones the sidebar is a sheet: close it once a link has taken you somewhere.
  const { setOpenMobile } = useSidebar()
  useEffect(() => setOpenMobile(false), [path, setOpenMobile])

  return (
    <Sidebar collapsible="icon" variant="inset">
      <SidebarHeader className="px-3 pt-4 pb-2 group-data-[collapsible=icon]:px-2">
        {/* Collapsed to icons: only the mark, so nothing spills into the page. */}
        <Link
          href="/"
          aria-label="Unpaid home"
          className="flex items-center gap-2.5 overflow-hidden"
        >
          <Mark className="shrink-0" />
          <span className="text-[16.5px] font-semibold tracking-tight whitespace-nowrap text-ink group-data-[collapsible=icon]:hidden">
            Unpaid
          </span>
        </Link>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  isActive={path === "/app"}
                  tooltip="Home"
                  render={<Link href="/app" />}
                >
                  <HouseIcon weight="duotone" />
                  <span>Home</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  isActive={path.startsWith("/app/check")}
                  tooltip="New check"
                  render={<Link href="/app/check" />}
                >
                  <PlusCircleIcon weight="duotone" />
                  <span>New check</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  isActive={path === "/app/method"}
                  tooltip="How we label"
                  render={<Link href="/app/method" />}
                >
                  <SealCheckIcon weight="duotone" />
                  <span>How we label</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {reportBase ? (
          <SidebarGroup>
            <SidebarGroupLabel>This report</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {REPORT_TABS.map((t) => {
                  const href = `${reportBase}${t.slug}`
                  return (
                    <SidebarMenuItem key={t.label}>
                      <SidebarMenuButton
                        isActive={path === href}
                        tooltip={t.label}
                        render={<Link href={href} />}
                      >
                        <t.icon weight="duotone" />
                        <span>{t.label}</span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ) : null}

        <SidebarGroup className="group-data-[collapsible=icon]:hidden">
          <SidebarGroupLabel>Reports</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {reports === null
                ? Array.from({ length: 2 }, (_, i) => (
                    <SidebarMenuItem key={i}>
                      <Skeleton className="mx-2 my-1.5 h-5" />
                    </SidebarMenuItem>
                  ))
                : reports.map((r) => (
                    <SidebarMenuItem key={r.id}>
                      <SidebarMenuButton
                        isActive={reportBase === `/app/r/${r.id}`}
                        render={<Link href={`/app/r/${r.id}`} />}
                        className="h-auto py-2"
                      >
                        <FileTextIcon weight="duotone" className="self-start" />
                        <span className="line-clamp-2 leading-snug whitespace-normal">
                          {sentence(r.question)}
                        </span>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="group-data-[collapsible=icon]:hidden">
        <div className="rounded-xl bg-white p-3.5 shadow-[0_0_0_1px_rgb(15_23_42/0.07)]">
          <p className="text-[12.5px] font-medium text-ink">Before you buy</p>
          <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
            Labels show what reviewers disclosed, with their own words. Not
            who&apos;s honest.
          </p>
          <Link
            href="/"
            className="mt-2.5 inline-flex items-center gap-1 text-[12px] font-medium text-klein hover:underline"
          >
            About Unpaid <ArrowUpRightIcon weight="bold" className="size-3" />
          </Link>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
