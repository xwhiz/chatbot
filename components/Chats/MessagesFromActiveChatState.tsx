"use client";

import { useEffect, useRef, useState } from "react";
import { FaCopy } from "react-icons/fa6";
import { useActiveChat } from "@/stores/activeChat";

export default function MessagesFromActiveChatState({
  message,
}: {
  message: string | null;
}) {
  const chatContainer = useRef<HTMLDivElement>(null);
  const { chat } = useActiveChat();

  // scroll to the bottom of the chat
  useEffect(() => {
    if (chatContainer.current) {
      chatContainer.current.scrollTop = chatContainer.current.scrollHeight;
    }
  }, [chat]);

  return (
    <section
      className="container mx-auto p-4 md:p-6 lg:p-8 overflow-y-auto scrollbar flex-1"
      ref={chatContainer}
    >
      {chat.messages.length === 0 && (
        <>
          <h1 className="text-4xl font-bold text-center my-8">
            Welcome to P. Chatbot
          </h1>

          <p className="text-xl text-center">
            Start a conversation by typing a message in the input box below.
          </p>
        </>
      )}

      <div className="flex flex-col gap-4 mt-8">
        {chat.messages.map((m, i) => (
          <div
            key={i}
            className={`flex flex-col gap-1 justify-center ${
              m.sender === "human" ? "items-end" : "items-start"
            }`}
          >
            <div
              className={`px-4 py-3 rounded-lg ${
                m.sender === "human"
                  ? "bg-slate-700 text-white"
                  : "bg-slate-200 text-slate-800"
              }`}
            >
              {m.message}
            </div>

            <button
              className={`text-sm text-slate-800 ${
                m.sender === "human" ? "hidden" : "text-left"
              }`}
              onClick={() => navigator.clipboard.writeText(m.message)}
            >
              <FaCopy className="text-slate-800" />
            </button>
          </div>
        ))}

        {message && (
          <div
            className={`flex flex-col gap-1 justify-center ${"items-start"}`}
          >
            <div
              className={`px-4 py-3 rounded-lg ${"bg-slate-200 text-slate-800"}`}
            >
              {message}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
