"use client";
import { useSidebarStore } from "@/stores/sidebar";
import Link from "next/link";

export default function HeaderWithButton() {
  const { toggle } = useSidebarStore();
  return (
    <nav className="w-full flex flex-wrap items-center justify-between px-2 py-3 navbar-expand-lg bg-white">
      <div className="container px-4 mx-auto flex flex-wrap items-center justify-between">
        <div className="w-full relative flex gap-4 items-center justify-start">
          <button
            onClick={toggle}
            className="text-slate-800 text-sm font-bold leading-relaxed inline-block py-2 whitespace-nowrap uppercase md:hidden"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16m-7 6h7"
              />
            </svg>
          </button>

          <Link
            href="/"
            className="text-slate-800 text-sm font-bold leading-relaxed inline-block py-2 whitespace-nowrap uppercase"
          >
            P. Chatbot
          </Link>
        </div>
      </div>
    </nav>
  );
}
