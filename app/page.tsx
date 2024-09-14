"use client";
import { useEffect, useState } from "react";
import { FaArrowCircleUp } from "react-icons/fa";
import WithSidebar from "@/layouts/WithSidebar";
import { useRouter } from "next/navigation";
import useAuth from "@/hooks/useAuth";
import MessagesFromActiveChatState from "../components/Chats/MessagesFromActiveChatState";
import { Message } from "@/stores/activeChat";
import { useActiveChatID } from "@/stores/activeChatID";
import axios from "axios";
import { useUserChatsStore } from "@/stores/userChatsStore";
import { toast } from "react-toastify";
import { useActiveChat } from "@/stores/activeChat";

export default function Home() {
  const router = useRouter();
  const [inputMessage, setInputMessage] = useState("");
  const { activeChatId, setActiveChatId } = useActiveChatID();
  const { setChatIDs, chatIDs } = useUserChatsStore();
  const { setActiveChat, addNewMessage } = useActiveChat();

  const [token, sessionInformation] = useAuth();

  useEffect(() => {
    if (!sessionInformation) {
      return;
    }

    const fetchChats = async () => {
      if (activeChatId === "") {
        return;
      }

      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL + `/chats/${activeChatId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const chat = response.data.data;
        setActiveChat(chat);
      } catch (error: any) {
        console.log(error);
      }
    };

    fetchChats();
  }, [activeChatId, sessionInformation, token]);

  if (!sessionInformation) {
    return null;
  }

  if (sessionInformation.role === "admin") {
    router.push("/dashboard");
  }

  const handleKeyPress = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const sendMessage = async () => {
    if (inputMessage.trim() === "") {
      return;
    }

    const body =
      activeChatId === ""
        ? {
            message: inputMessage,
            user_email: sessionInformation.email,
          }
        : {
            message: inputMessage,
            chat_id: activeChatId,
            user_email: sessionInformation.email,
          };

    try {
      const response = await axios.post(
        process.env.NEXT_PUBLIC_API_URL + `/add-message`,
        body,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const data = response.data;

      if (activeChatId === "") {
        setChatIDs([
          ...chatIDs,
          {
            id: data.chat_id,
            title: inputMessage.slice(0, 10),
          },
        ]);
      }

      setActiveChatId(data.chat_id);
      addNewMessage({
        message: inputMessage,
        sender: "human",
      });
      setInputMessage("");

      await getBotMessage(data.chat_id);
    } catch (error: any) {
      toast.error(error.response.data.message);
      console.log(error);
    }
  };

  const getBotMessage = async (id: string) => {
    try {
      const body = {
        chat_id: id,
      };
      const response = await axios.post(
        process.env.NEXT_PUBLIC_API_URL + `/generate-response`,
        body,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      const data = response.data;
      const messageObj = data.messageObject as Message;
      addNewMessage(messageObj);
    } catch (error: any) {
      toast.error(error.response.data.message);
      console.log(error);
    }
  };

  return (
    <WithSidebar>
      <MessagesFromActiveChatState />

      <div className="p-4 border-t">
        <div className="relative">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyUp={handleKeyPress}
            className="w-full p-2 pr-12 border rounded"
            placeholder={"Type your message..."}
          />
          <button
            onClick={sendMessage}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-blue-500 rounded-full"
          >
            <FaArrowCircleUp className="w-6 h-6" />
          </button>
        </div>
      </div>
    </WithSidebar>
  );
}
