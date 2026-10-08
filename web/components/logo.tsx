import Link from "next/link"

import { cn } from "@/lib/utils"

/** The mark: a play button inside a speech bubble — "what reviewers say". */
export function Mark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" aria-hidden className={cn("size-7", className)}>
      <defs>
        <linearGradient id="unpaid-mark" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0a3cc2" />
          <stop offset="1" stopColor="#002fa7" />
        </linearGradient>
      </defs>
      <path
        d="M9 3h14a6 6 0 0 1 6 6v10a6 6 0 0 1-6 6h-6.6l-5.2 4.2c-.65.52-1.6.06-1.6-.77V25H9a6 6 0 0 1-6-6V9a6 6 0 0 1 6-6Z"
        fill="url(#unpaid-mark)"
      />
      <path
        d="M13.2 10.4v8.2c0 .6.66.97 1.17.65l6.5-4.1a.77.77 0 0 0 0-1.3l-6.5-4.1a.77.77 0 0 0-1.17.65Z"
        fill="#fff"
      />
    </svg>
  )
}

export function Logo({
  href = "/",
  className,
}: {
  href?: string
  className?: string
}) {
  return (
    <Link
      href={href}
      className={cn("flex items-center gap-2.5", className)}
      aria-label="Unpaid home"
    >
      <Mark />
      <span className="text-[16.5px] font-semibold tracking-tight text-ink">
        Unpaid
      </span>
    </Link>
  )
}
