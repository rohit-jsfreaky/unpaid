import { ReportGate } from "@/components/app/report-gate"
import { ReportProvider } from "@/components/app/report-context"

export default async function ReportLayout({
  children,
  params,
}: Readonly<{ children: React.ReactNode; params: Promise<{ id: string }> }>) {
  const { id } = await params
  return (
    <ReportProvider id={id}>
      <ReportGate>{children}</ReportGate>
    </ReportProvider>
  )
}
