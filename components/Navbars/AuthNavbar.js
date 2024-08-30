"use client";
import React from "react";
import Link from "next/link";
// components

import PagesDropdown from "@/components/Dropdowns/PagesDropdown.js";
import { FaArrowAltCircleDown, FaBars } from "react-icons/fa";

export default function Navbar() {
  const [navbarOpen, setNavbarOpen] = React.useState(false);
  return (
    <nav className="z-10 w-full flex flex-wrap items-center justify-between px-2 py-3 navbar-expand-lg">
      <div className="container px-4 mx-auto flex flex-wrap items-center justify-between">
        <div className="w-full relative flex justify-between md:w-auto md:static md:block md:justify-start">
          <Link
            href="/"
            className="text-slate-800 text-sm font-bold leading-relaxed inline-block mr-4 py-2 whitespace-nowrap uppercase"
          >
            P. Chatbot
          </Link>
          <button
            className="cursor-pointer text-xl leading-none px-3 py-1 border border-solid border-transparent rounded bg-transparent block md:hidden outline-none focus:outline-none"
            type="button"
            onClick={() => setNavbarOpen(!navbarOpen)}
          >
            <FaBars className="text-slate-800" />
          </button>
        </div>
        <div
          className={
            "md:flex flex-grow items-center bg-white md:bg-opacity-0 md:shadow-none" +
            (navbarOpen ? " block rounded shadow-md" : " hidden")
          }
          id="example-navbar-warning"
        >
          <li className="flex items-center">
            <a
              className="lg:text-white lg:hover:text-blueGray-200 text-blueGray-700 px-3 py-4 lg:py-2 flex items-center text-xs uppercase font-bold"
              href="https://github.com/creativetimofficial/notus-nextjs?ref=nnjs-auth-navbar"
              target="_blank"
            >
              <i className="lg:text-blueGray-200 text-blueGray-400 fab fa-github text-lg leading-lg " />
              <span className="lg:hidden inline-block ml-2">Star</span>
            </a>
          </li>
        </div>
      </div>
    </nav>
  );
}
