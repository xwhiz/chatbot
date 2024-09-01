"use client";

import { useSidebarStore } from "@/stores/sidebar";
import Link from "next/link";
import { FaTimes } from "react-icons/fa";
import { FaTrash } from "react-icons/fa6";

export function Sidebar() {
  const { isOpen } = useSidebarStore();

  return (
    <aside
      className={`w-full h-screen px-12 py-8 bg-slate-800 text-white fixed z-50 top-0 left-0 flex flex-col gap-4 justify-start items-center transition-transform ease-out duration-300 sm:w-9/12 md:static md:translate-x-0 md:w-full md:px-4 ${
        isOpen ? "-translate-x-full" : "translate-x-0"
      }`}
    >
      <nav className="w-full">
        <h3 className="text-lg font-bold mb-2">Links</h3>
        <Link href="/profile" className="text-white cursor-pointer underline">
          Profile
        </Link>
      </nav>

      <hr className="w-full my-1" />

      <ul className="flex flex-col flex-grow gap-2 w-full overflow-y-auto scrollbar pr-1 relative">
        <h3 className="text-lg font-bold sticky top-0 bg-slate-800 pb-2">
          Chats
        </h3>

        {Array.from({ length: 10 }).map((_, i) => (
          <Link
            href="/"
            className="flex gap-2 justify-between items-center bg-slate-700 px-4 py-2 rounded cursor-pointer hover:bg-slate-600"
            key={i}
          >
            <p className="text-white truncate w-full">Chat title</p>
            <FaTrash className="text-gray-100 hover:text-white" />
          </Link>
        ))}
      </ul>

      <hr className="w-full my-1" />

      <button
        onClick={() => console.log("logout")}
        className="bg-transparent border border-red-500 text-red-500 px-4 py-2 rounded w-full hover:bg-red-500 hover:text-white transition-colors"
      >
        Logout
      </button>

      <button
        onClick={() => useSidebarStore.getState().toggle()}
        className="absolute top-0 right-0 text-white p-4 md:hidden"
      >
        <FaTimes className="text-2xl" />
      </button>
    </aside>
  );
}
