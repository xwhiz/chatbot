"use client";
import { useEffect, useRef, useState } from "react";
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
import { useIsGeneratingStore } from "@/stores/useIsGeneratingStore";

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
  const { setIsGenerating } = useIsGeneratingStore();

  const [models, setModels] = useState<string[]>([
    "llama3.1",
    "deepseek-r1:14b",
    "qwen2.5:14b",
  ]);
  const [selectedModel, setSelectedModel] = useState<string>(models[0]);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  const [token, sessionInformation] = useAuth();

  const autoResize = () => {
    const textArea: HTMLTextAreaElement | null = textAreaRef.current;
    if (!textArea) return;
    textArea.style.height = "auto";
    textArea.style.height = Math.min(textArea.scrollHeight, 120) + "px"; // Max height ~5 lines
  };

  // .forEach((item) => {
  //   console.log(item);
  //   item.addEventListener("click", () => {
  //     console.log("Hello world");
  //   });
  // });

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeChatId, sessionInformation, token]);

  useEffect(() => {
    autoResize();
  }, [inputMessage]);

  if (!sessionInformation) {
    return null;
  }

  if (sessionInformation.role === "admin") {
    router.push("/dashboard");
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
      setIsGenerating(true);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    autoResize();
  };

  const send = () => {
    if (inputMessage.trim()) {
      sendMessage();
      setInputMessage("");
      autoResize();
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

        currentMessage = currentMessage.replace(
          "<think>",
          "<div class='thinking' data-state='open'>"
        );
        currentMessage = currentMessage.replace("</think>", "</div>");

        setMessageState({ isGenerating: false, message: currentMessage });
      };

      // @ts-ignore
      eventSource.onclose = async () => {
        try {
          currentMessage = currentMessage.replace(
            "<think>",
            "<div class='thinking' data-state='closed'>"
          );
          currentMessage = currentMessage.replace("</think>", "</div>");
          currentMessage = currentMessage.replace(
            "<div class='thinking' data-state='open'>",
            "<div class='thinking' data-state='closed'>"
          );

          console.log(currentMessage);

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
          setIsGenerating(false);
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
        setIsGenerating(false);
      };
    } catch (error: any) {
      toast.error(error.response?.data?.message || "An error occurred");
      console.log(error);
    }
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedModel(e.target.value);
    toast.promise(
      axios.post(
        process.env.NEXT_PUBLIC_API_URL + `/change-model`,
        {
          model: e.target.value,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      ),
      {
        pending: "Changing model...",
        success: "Model changed",
        error: "An error occurred",
      }
    );
  };

  return (
    <WithSidebar>
      <div className="relative max-w-[50rem] w-full mx-auto h-full flex flex-col">
        <MessagesFromActiveChatState message={messageState.message} />

        {messageState.isGenerating && (
          <div className="flex justify-center items-center h-16">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>

            <p className="ml-2">Retrieving relevent data...</p>
          </div>
        )}

        <div className="bg-slate-200 border-t p-1 absolut w-full bottom-0 rounded-t-lg">
          <textarea
            ref={textAreaRef}
            value={inputMessage}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            className="w-full p-2 rounded resize-none overflow-y-auto max-h-[120px] outline-none bg-slate-100"
            placeholder="Type your message..."
            rows={1}
            autoFocus
          />

          <div className="flex items-center justify-between mt-2">
            <select
              value={selectedModel}
              onChange={handleModelChange}
              className="p-2 border rounded bg-slate-100"
              disabled={messageState.isGenerating}
            >
              {models.map((model) => (
                <option key={model} value={model}>
                  {model}
                </option>
              ))}
            </select>

            <button
              onClick={send}
              className="p-2 text-blue-500 rounded-full hover:bg-gray-400"
            >
              <FaArrowCircleUp className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>
    </WithSidebar>
  );
}
