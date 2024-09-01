"use client";

import { useEffect, useRef } from "react";
import { FaCopy } from "react-icons/fa6";

interface IChat {
  id: number;
  text: string;
  from: string;
}

export default function Chats({ chats }: Readonly<{ chats: IChat[] }>) {
  const chatContainer = useRef<HTMLDivElement>(null);

  // scroll to the bottom of the chat
  useEffect(() => {
    if (chatContainer.current) {
      chatContainer.current.scrollTop = chatContainer.current.scrollHeight;
    }
  }, [chats]);

  return (
    <section
      className="container mx-auto p-4 md:p-6 lg:p-8 overflow-y-auto scrollbar flex-1"
      ref={chatContainer}
    >
      <h1 className="text-4xl font-bold text-center my-8">
        Welcome to P. Chatbot
      </h1>

      <p className="text-xl text-center">
        This is a chatbot application built with Next.js and Zustand.
      </p>

      <div className="flex flex-col gap-4 mt-8">
        {chats.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col gap-1 justify-center ${
              m.from === "user" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`px-4 py-3 rounded-lg ${
                m.from === "user"
                  ? "bg-slate-700 text-white"
                  : "bg-slate-200 text-slate-800"
              }`}
            >
              {m.text}
            </div>

            <button
              className={`text-sm text-slate-800 ${
                m.from === "user" ? "hidden" : "text-left"
              }`}
              onClick={() => navigator.clipboard.writeText(m.text)}
            >
              <FaCopy className="text-slate-800" />
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
