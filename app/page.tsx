import HeaderWithButton from "@/components/Headers/HeaderWithButton";
import { Sidebar } from "@/components/Sidebars/Sidebar";
import { FaArrowCircleUp } from "react-icons/fa";
import Chats from "./Chats";
import WithSidebar from "@/layouts/WithSidebar";

export default function Home() {
  // if this is admin, redirect them to /dashboard

  const messages = [
    {
      id: 1,
      text: "Hello from user",
      from: "user",
    },
    {
      id: 2,
      text: "Hello from AI",
      from: "ai",
    },
    {
      id: 3,
      text: "Hello from user",
      from: "user",
    },
    {
      id: 4,
      text: "Hello from AI",
      from: "ai",
    },
    {
      id: 5,
      text: "Hello from user",
      from: "user",
    },
    {
      id: 6,
      text: "Hello from AI",
      from: "ai",
    },
    {
      id: 7,
      text: "Hello from user",
      from: "user",
    },
    {
      id: 8,
      text: "Hello from AI",
      from: "ai",
    },
    {
      id: 9,
      text: "Hello from user",
      from: "user",
    },
    {
      id: 10,
      text: "Hello from AI",
      from: "ai",
    },
  ];

  return (
    <WithSidebar>
      <Chats chats={messages} />

      <div className="bg-white p-4 relative h-20">
        <input
          type="text"
          placeholder="Type a message..."
          className="w-full border border-slate-200 rounded-lg p-3"
        />

        <button className="absolute z-10 right-4 top-1/2 -translate-y-1/2 text-slate-700 px-4 py-3 rounded-lg ml-2">
          <FaArrowCircleUp className="text-2xl" />
        </button>
      </div>
    </WithSidebar>
  );
}
