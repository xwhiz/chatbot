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
  const [messageState, setMessageState] = useState<{
    isGenerating: boolean;
    message: string;
  }>({ isGenerating: false, message: "" });

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

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
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
      class AuthEventSource extends EventSource {
        constructor(url: string, configuration: any) {
          super(url, configuration);
        }
      }

      const eventSource = new AuthEventSource(
        `${process.env.NEXT_PUBLIC_API_URL}/generate-response?chat_id=${id}&token=${token}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setMessageState({ isGenerating: true, message: "" });

      let currentMessage = "";

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        currentMessage += data.partial_response;

        setMessageState({ isGenerating: false, message: currentMessage });
      };

      // @ts-ignore
      eventSource.onclose = async () => {
        try {
          await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL}/update-chat`,
            { chat_id: id, full_message: currentMessage.trim() },
            {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );

          addNewMessage({
            message: currentMessage,
            sender: "ai",
          });

          setMessageState({ isGenerating: false, message: "" });
        } catch (error: any) {
          toast.error(error.response?.data?.message || "An error occurred");
          console.log(error);
        }
      };

      eventSource.onerror = (error) => {
        console.error("EventSource failed:", error);
        eventSource.close();
        // @ts-ignore
        error.target.onclose();

        setMessageState({ isGenerating: false, message: "" });
      };
    } catch (error: any) {
      toast.error(error.response?.data?.message || "An error occurred");
      console.log(error);
    }
  };

  return (
    <WithSidebar>
      <MessagesFromActiveChatState message={messageState.message} />

      {messageState.isGenerating && (
        <div className="flex justify-center items-center h-16">
          <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>

          <p className="ml-2">Retrieving relevent data...</p>
        </div>
      )}

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
