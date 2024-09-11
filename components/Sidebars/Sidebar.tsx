"use client";

import { useState } from "react";
import { useSidebarStore } from "@/stores/sidebar";
import { useChatsStore } from "@/stores/chats";
import { FaTimes } from "react-icons/fa";
import { FaTrash, FaChevronDown } from "react-icons/fa6";
import { User, Users, MessageSquare, Upload, Plus } from "lucide-react";

export function Sidebar() {
  const { isOpen } = useSidebarStore();
  const [role, setRole] = useState("user");
  const { chats } = useChatsStore();

  const menuItems = {
    admin: [
      { name: "Dashboard", icon: <FaChevronDown /> },
      { name: "Users", icon: <Users /> },
      { name: "Chats", icon: <MessageSquare /> },
      { name: "Upload Documents", icon: <Upload /> },
    ],
    user: [{ name: "Profile", icon: <User /> }],
  };

  const deleteChat = useChatsStore((state) => state.deleteChat);
  const addChat = useChatsStore((state) => state.addChat);

  return (
    <aside
      className={`w-64 h-screen py-8 bg-gray-100 text-white fixed z-50 top-0 left-0 flex flex-col gap-4 justify-start items-center transition-transform ease-out duration-300 md:static md:translate-x-0 ${
        isOpen ? "-translate-x-full" : "translate-x-0"
      }`}
    >
      <nav className="w-full mt-4 flex-grow overflow-y-auto">
        {role === "admin" ? (
          menuItems.admin.map((item) => (
            <a
              key={item.name}
              href="#"
              className={`flex items-center px-4 py-2 text-gray-700 hover:bg-gray-200`}
            >
              {item.icon}
              <span className="ml-2">{item.name}</span>
            </a>
          ))
        ) : (
          <>
            <a
              href="#"
              className={`flex items-center px-4 py-2 text-gray-700 hover:bg-gray-200`}
            >
              <User />
              <span className="ml-2">Profile</span>
            </a>
            <div className="px-4 py-2 text-gray-700 font-semibold">Chats</div>
            <div className="overflow-y-auto">
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className={`flex items-center justify-between px-4 py-2 text-gray-700 hover:bg-gray-200`}
                >
                  <a href="#" className="flex items-center flex-grow">
                    <MessageSquare className="w-4 h-4" />
                    <span className="ml-2">{chat.name}</span>
                  </a>
                  <button
                    onClick={() => deleteChat(chat.id)}
                    className="text-gray-500 hover:text-red-500"
                  >
                    <FaTrash />
                  </button>
                </div>
              ))}
            </div>
            <a
              className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-200 mt-2 hover:cursor-pointer"
              onClick={() =>
                addChat({
                  id: "new-chat",
                  name: "New Chat",
                  messages: [],
                })
              }
            >
              <Plus className="w-4 h-4" />
              <span className="ml-2">New Chat</span>
            </a>
          </>
        )}
      </nav>

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
