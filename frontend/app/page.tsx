"use client";
import { useEffect, useRef, useState } from "react";
import { FaArrowUp } from "react-icons/fa";
import WithSidebar from "@/layouts/WithSidebar";
import { useRouter } from "next/navigation";
import useAuth from "@/hooks/useAuth";
import MessagesFromActiveChatState from "../components/Chats/MessagesFromActiveChatState";
import { useActiveChatID } from "@/stores/activeChatID";
import axios from "axios";
import { useUserChatsStore } from "@/stores/userChatsStore";
import { toast } from "react-toastify";
import { useActiveChat } from "@/stores/activeChat";
import { useIsGeneratingStore } from "@/stores/useIsGeneratingStore";
import { Brain, Minus, Plus, PlusCircle, PlusCircleIcon } from "lucide-react";
import { Backdrop, Fade, Modal } from "@mui/material";

type Document = {
  id: string;
  title: string;
};

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
  const { isGenerating, setIsGenerating } = useIsGeneratingStore();
  const [shouldUseKnowledgeBase, setShouldUseKnowledgeBase] = useState(false);

  const [models, setModels] = useState<{ name: string; modelName: string }[]>([
    { name: "llama3.1", modelName: "llama3.1" },
    { name: "DeepSeek-r1", modelName: "deepseek-r1:14b" },
    { name: "Qwen2.5", modelName: "qwen2.5:14b" },
  ]);
  const [selectedModel, setSelectedModel] = useState<number>(0);
  const textAreaRef = useRef<HTMLTextAreaElement>(null);

  const [token, sessionInformation] = useAuth();
  const [socket, setSocket] = useState<any>(null);
  const [docSelectionModalOpen, setDocSelectionModalOpen] =
    useState<boolean>(false);
  const [allDocuments, setAllDocuments] = useState<Document[]>([]);
  const [selectedDocsForKB, setSelectedDocsForKB] = useState<Document[]>([]);

  const autoResize = () => {
    const textArea: HTMLTextAreaElement | null = textAreaRef.current;
    if (!textArea) return;
    textArea.style.height = "auto";
    textArea.style.height = Math.min(textArea.scrollHeight, 120) + "px"; // Max height ~5 lines
  };

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

    const fetchAllowedDocuments = async () => {
      try {
        const response = await axios.get(
          process.env.NEXT_PUBLIC_API_URL + `/documents/user-allowed-docs/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const documents = response.data.data;
        setAllDocuments(documents);
        setSelectedDocsForKB([]);
      } catch (error: any) {
        console.log(error);
      }
    };

    fetchChats();
    fetchAllowedDocuments();
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

    const body: {
      message: string;
      user_email: string;
      use_knowledge_base: boolean;
      selected_docs: Document[];
      chat_id?: string;
    } = {
      message: inputMessage,
      user_email: sessionInformation.email,
      use_knowledge_base: shouldUseKnowledgeBase,
      selected_docs: selectedDocsForKB,
    };
    if (activeChatId !== "") body.chat_id = activeChatId;

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
      setMessageState({ isGenerating: false, message: "" });
      setIsGenerating(false);
    }
  };

  const handleClosingSocket = async (currentMessage: string, id: string) => {
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

      // console.log(currentMessage);

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

  const getBotMessage = async (id: string) => {
    try {
      class AuthEventSource extends EventSource {
        constructor(url: string, configuration: any) {
          super(url, configuration);
        }
      }

      const socket = new AuthEventSource(
        `${process.env.NEXT_PUBLIC_API_URL}/generate-response?chat_id=${id}&token=${token}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setSocket(socket);
      setMessageState({ isGenerating: true, message: "" });

      let currentMessage = "";

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.completed) {
          socket.close();
          handleClosingSocket(currentMessage, id);
          return;
        }

        currentMessage += data.partial_response
          .replace("<think>", "<div class='thinking' data-state='open'>")
          .replace("</think>", "</div>");

        setMessageState({ isGenerating: false, message: currentMessage });
      };

      // @ts-ignore
      socket.onclose = async () => {
        handleClosingSocket(currentMessage, id);
      };

      socket.onerror = (error) => {
        console.error("EventSource failed:", error);
        socket.close();
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

  const stopCurrentMessage = async () => {
    console.log("Stopping current message");
    console.log(socket);
    if (socket) {
      socket.close();
      handleClosingSocket(messageState.message, activeChatId);
    }
  };

  const handleModelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    setSelectedModel(models.findIndex((m) => m.modelName === value));
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
    <>
      <WithSidebar>
        <div className="relative max-w-[50rem] w-full mx-auto h-full flex flex-col">
          <MessagesFromActiveChatState message={messageState.message} />

          {messageState.isGenerating && (
            <div className="flex justify-center items-center h-16">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>

              <p className="ml-2">Responding...</p>
            </div>
          )}

          <div className="bg-white border-t p-1 absolut w-full bottom-0 rounded-t-lg">
            <textarea
              ref={textAreaRef}
              value={inputMessage}
              onChange={handleInputChange}
              onKeyDown={handleKeyPress}
              className="w-full p-2 rounded resize-none overflow-y-auto max-h-[120px] outline-none bg-gray-100"
              placeholder="Type your message..."
              rows={1}
              autoFocus
            />

            <div className="flex items-center justify-between mt-2">
              <div className="flex gap-2">
                <select
                  value={models[selectedModel].modelName}
                  onChange={handleModelChange}
                  className="text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-100 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2"
                  disabled={messageState.isGenerating}
                >
                  {models.map((model) => (
                    <option key={model.modelName} value={model.modelName}>
                      {model.name}
                    </option>
                  ))}
                </select>

                <div>
                  <input
                    type="checkbox"
                    id="knowledgeBase"
                    className="hidden peer"
                    required
                    value={shouldUseKnowledgeBase as any}
                    onChange={(e) => {
                      setShouldUseKnowledgeBase(e.target.checked);
                      setSelectedDocsForKB([]);
                      if (e.target.checked) setDocSelectionModalOpen(true);
                    }}
                  />
                  <label
                    htmlFor="knowledgeBase"
                    className="text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-100 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2 inline-flex items-center justify-between w-full p-2 cursor-pointer peer-checked:border-blue-600 peer-checked:text-black"
                  >
                    <div className="flex justify-center items-center gap-1">
                      <Brain className="w-5 h-5" />
                      <span>Knowledge Base</span>
                    </div>
                  </label>
                </div>

                {shouldUseKnowledgeBase && (
                  <button
                    className="text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-100 font-medium rounded-lg text-sm px-5 py-2.5 me-2 mb-2"
                    onClick={() => setDocSelectionModalOpen(true)}
                  >
                    Select Docs
                  </button>
                )}
              </div>

              <button
                onClick={isGenerating ? stopCurrentMessage : send}
                className="bg-white p-3 text- rounded-full hover:bg-gray-200"
              >
                {isGenerating ? (
                  <div className="w-4 h-4 bg-black"></div>
                ) : (
                  <FaArrowUp className="w-4 h-4" />
                )}
              </button>
            </div>
          </div>
        </div>
      </WithSidebar>

      <Modal
        aria-labelledby="transition-modal-title"
        aria-describedby="transition-modal-description"
        open={docSelectionModalOpen}
        onClose={() => setDocSelectionModalOpen(false)}
        closeAfterTransition
        slots={{ backdrop: Backdrop }}
        slotProps={{
          backdrop: {
            timeout: 500,
          },
        }}
      >
        <Fade in={docSelectionModalOpen}>
          <article className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-min bg-white shadow-md max-w-[600px] w-full overflow-hidden rounded">
            <div className="flex items-center justify-between p-4 md:p-5 border-b rounded-t border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                Select documents
              </h3>
              <button
                type="button"
                className="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm h-8 w-8 ms-auto inline-flex justify-center items-center dark:hover:bg-gray-600 dark:hover:text-white"
                onClick={() => setDocSelectionModalOpen(false)}
              >
                <svg
                  className="w-3 h-3"
                  aria-hidden="true"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 14 14"
                >
                  <path
                    stroke="currentColor"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"
                  />
                </svg>
                <span className="sr-only">Close modal</span>
              </button>
            </div>

            {/* Modal body */}
            <div className="p-4 md:p-5 space-y-2">
              <h3>Documents</h3>
              <div className="flex flex-wrap gap-1">
                {allDocuments.filter(
                  (item) => !selectedDocsForKB.includes(item)
                ).length === 0 && (
                  <span className="bg-gray-100 text-gray-800 me-2 px-2.5 py-0.5 rounded-full">
                    All documents selected
                  </span>
                )}

                {allDocuments
                  .filter((item) => !selectedDocsForKB.includes(item))
                  .map((item, i) => {
                    return (
                      <button
                        key={i}
                        className="text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-2 focus:ring-gray-100 rounded-full pl-4 pr-2 py-2.5 flex gap-1 items-center"
                        onClick={() => {
                          if (selectedDocsForKB.includes(item)) {
                            setSelectedDocsForKB(
                              selectedDocsForKB.filter(
                                (doc) => doc.id != item.id
                              )
                            );
                          } else {
                            setSelectedDocsForKB([...selectedDocsForKB, item]);
                          }
                        }}
                      >
                        {item.title}
                        <Plus />
                      </button>
                    );
                  })}
              </div>

              <hr />

              <h3>Selected Documents</h3>
              <div className="flex flex-wrap gap-1">
                {selectedDocsForKB.length === 0 && (
                  <span className="bg-gray-100 text-gray-800 me-2 px-2.5 py-0.5 rounded-full">
                    No documents selected
                  </span>
                )}
                {selectedDocsForKB.map((item, i) => {
                  return (
                    <button
                      key={i}
                      className="text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-2 focus:ring-gray-100 rounded-full pl-4 pr-2 py-2.5 flex gap-1 items-center"
                      onClick={() => {
                        if (selectedDocsForKB.includes(item)) {
                          setSelectedDocsForKB(
                            selectedDocsForKB.filter((doc) => doc.id != item.id)
                          );
                        } else {
                          setSelectedDocsForKB([...selectedDocsForKB, item]);
                        }
                      }}
                    >
                      {item.title}
                      <Minus />
                    </button>
                  );
                })}
              </div>
            </div>
          </article>
        </Fade>
      </Modal>

      {/* <Modal
        title="Select documents to use as knowledgebase"
        open={docSelectionModalOpen}
        handleClose={() => setDocSelectionModalOpen(!docSelectionModalOpen)}
      /> */}
    </>
  );
}
