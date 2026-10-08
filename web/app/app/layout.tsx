import type { Metadata } from "next"

import { AppSidebar } from "@/components/app/app-sidebar"
import { TopBar } from "@/components/app/top-bar"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"

export const metadata: Metadata = { title: "Dashboard" }

export default function AppLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-[420px] opacity-70 glow-top" />
        <TopBar />
        <div className="relative mx-auto w-full max-w-[1400px] px-4 pt-2 pb-16 md:px-8">
          {children}
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
