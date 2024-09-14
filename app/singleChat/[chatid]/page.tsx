"use client";
import useAuth from "@/hooks/useAuth";
import { useActiveChat } from "@/stores/activeChat";
import axios from "axios";
import { useParams, useRouter } from "next/navigation";
import { useEffect } from "react";
import { toast } from "react-toastify";
import MessagesFromActiveChatState from "@/components/Chats/MessagesFromActiveChatState";
import WithSidebar from "@/layouts/WithSidebar";

export default function ChatPage() {
  const router = useRouter();
  const params = useParams();
  const [token, session] = useAuth();
  const { setActiveChat } = useActiveChat();

  const chatId = params.chatid;

  useEffect(() => {
    if (!session) return;

    async function fetchChat() {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL + `/chats/${chatId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        console.log(response.data);
        setActiveChat(response.data.data);
      } catch (error: any) {
        const data = error.response;
        if (data) {
          console.log(data.message);
          toast.error(data.message);
        }
      }
    }

    fetchChat();
  }, [token, session]);

  if (!session) {
    return null;
  }

  if (session.role !== "admin") {
    router.push("/");
  }

  return (
    <WithSidebar>
      <MessagesFromActiveChatState />
    </WithSidebar>
  );
}
