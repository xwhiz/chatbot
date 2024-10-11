import Link from "next/link";

export default function MinHeader() {
  return (
    <nav className="z-10 w-full flex flex-wrap items-center justify-between px-2 py-3 navbar-expand-lg bg-white">
      <div className="container px-4 mx-auto flex flex-wrap items-center justify-between">
        <div className="w-full relative flex justify-between md:w-auto md:static md:block md:justify-start">
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
