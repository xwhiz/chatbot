"use client";

import { useActionState, useEffect, useState } from "react";
import { useSidebarStore } from "@/stores/sidebar";
import { FaTimes } from "react-icons/fa";
import { FaTrash, FaChevronDown } from "react-icons/fa6";
import { User, Users, MessageSquare, Upload, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCookies } from "next-client-cookies";
import Swal from "sweetalert2";
import useAuth from "@/hooks/useAuth";
import axios, { AxiosError } from "axios";
import { renderToStaticMarkup } from "react-dom/server";
import { toast } from "react-toastify";
import { useUserChatsStore } from "@/stores/userChatsStore";
import { useActiveChatID } from "@/stores/activeChatID";
import { useActiveChat } from "@/stores/activeChat";
import Link from "next/link";

export function Sidebar() {
  const [token, session] = useAuth();
  const router = useRouter();
  const cookies = useCookies();
  const { isOpen } = useSidebarStore();
  const { activeChatId, setActiveChatId } = useActiveChatID();
  const { chatIDs, setChatIDs } = useUserChatsStore();
  const { chat, setActiveChat } = useActiveChat();

  useEffect(() => {
    if (!session) return;

    const fetchChatIDs = async () => {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL + "/chats/ids",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const chatIDs = response.data.data;
        setChatIDs(chatIDs);
      } catch (error: any) {
        const data = error.response;
        if (data) toast.error(data.message);
      }
    };

    fetchChatIDs();
  }, [session, token]);

  const menuItems = {
    admin: [
      { name: "Profile", icon: <User />, href: "/profile" },
      { name: "Dashboard", icon: <FaChevronDown />, href: "/dashboard" },
      { name: "Users", icon: <Users />, href: "/users" },
      { name: "Chats", icon: <MessageSquare />, href: "/chats" },
      { name: "Upload Documents", icon: <Upload />, href: "/documents" },
    ],
    user: [{ name: "Profile", icon: <User /> }],
  };

  const handleDeleteChat = async (chatID: string) => {
    Swal.fire({
      title: "Are you sure?",
      text: "You will not be able to recover this chat!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: "Yes, delete it!",
      cancelButtonText: "No, cancel",
    }).then(async (result) => {
      if (result.isConfirmed) {
        try {
          await axios.delete(
            process.env.NEXT_PUBLIC_API_URL + `/chats/${chatID}`,
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );
          setChatIDs(chatIDs.filter((chat) => chat.id !== chatID));
          setActiveChatId("");
          setActiveChat({
            id: "",
            title: "",
            user_email: "",
            messages: [],
          });

          toast.success("Chat deleted successfully!");
        } catch (error: any) {
          const data = error.response;
          toast.error(data.message);
        }
      }
    });
  };

  if (!session) return null;

  return (
    <aside
      className={`w-64 h-screen pt-8 pb-2 bg-gray-100 text-white fixed z-50 top-0 left-0 flex flex-col gap-4 justify-start items-center transition-transform ease-out duration-300 md:static md:translate-x-0 ${
        isOpen ? "-translate-x-full" : "translate-x-0"
      }`}
    >
      <nav className="w-full mt-4 flex-grow overflow-y-auto">
        {session.role.toLowerCase() === "admin" ? (
          menuItems.admin.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center px-4 py-2 text-gray-700 hover:bg-gray-200`}
            >
              {item.icon}
              <span className="ml-2">{item.name}</span>
            </Link>
          ))
        ) : (
          <>
            <Link
              href="/profile"
              className={`flex items-center px-4 py-2 text-gray-700 hover:bg-gray-200`}
            >
              <User />
              <span className="ml-2">Profile</span>
            </Link>
            <div className="px-4 py-2 text-gray-700 font-semibold">Chats</div>
            <div className="overflow-y-auto">
              {chatIDs.map((chat) => (
                <div
                  key={chat.id}
                  className={`trigger hover:cursor-pointer flex items-center justify-between px-4 py-2 text-gray-700 hover:bg-gray-200 ${
                    chat.id === useActiveChatID.getState().activeChatId
                      ? "bg-gray-200"
                      : ""
                  }`}
                  onClick={(e: any) => {
                    if (!e.target.classList.contains("trigger")) return;
                    useActiveChatID.setState({ activeChatId: chat.id });
                  }}
                >
                  <MessageSquare className="trigger w-4 h-4" />
                  <div className="trigger ml-2 truncate block w-full">
                    {chat.title || "Untitled Chat"}
                  </div>
                  <button
                    onClick={() => handleDeleteChat(chat.id)}
                    className="text-gray-500 hover:text-red-500"
                  >
                    <FaTrash />
                  </button>
                </div>
              ))}
            </div>
            <a
              className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-200 mt-2 hover:cursor-pointer"
              onClick={() => {
                setActiveChat({
                  id: "",
                  title: "",
                  user_email: "",
                  messages: [],
                });
                useActiveChatID.setState({ activeChatId: "" });
              }}
            >
              <Plus className="w-4 h-4" />
              <span className="ml-2">New Chat</span>
            </a>
          </>
        )}
      </nav>

      <button
        onClick={() => {
          Swal.fire({
            title: "Are you sure?",
            text: "You will be logged out.",
            icon: "warning",
            showCancelButton: true,
            confirmButtonText: "Yes, logout",
            cancelButtonText: "No, cancel",
          }).then((result) => {
            if (result.isConfirmed) {
              cookies.remove("token");
              router.push("/login");
            }
          });
        }}
        className="bg-transparent text-red-500 px-4 py-2 w-full hover:bg-red-500 hover:text-white transition-colors"
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
