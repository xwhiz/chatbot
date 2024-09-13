"use client";
import { useState } from "react";
import { FaArrowCircleUp } from "react-icons/fa";
import WithSidebar from "@/layouts/WithSidebar";
import { useRouter } from "next/navigation";
import useAuth from "@/hooks/useAuth";

const dummyResponses = [
  "That's an interesting point. Can you elaborate?",
  "I see. Have you considered looking at it from a different perspective?",
  "That's a great question. Let me think about that for a moment.",
  "I understand your concern. Here's what I think about that...",
  "Thank you for sharing that. It's definitely something to consider.",
];

export default function Home() {
  const router = useRouter();
  const [inputMessage, setInputMessage] = useState("");
  const [chats, setChats] = useState([]);
  const [activeItem, setActiveItem] = useState("");

  const sessionInformation = useAuth();

  if (!sessionInformation) {
    return null;
  }

  if (sessionInformation.role === "admin") {
    router.push("/dashboard");
  }

  console.log(sessionInformation);

  const deleteChat = (id) => {
    setChats(chats.filter((chat) => chat.id !== id));
    if (activeItem === `Chat ${id}`) {
      setActiveItem("");
    }
  };
  const handleKeyPress = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  const startNewChat = (message) => {
    const newChat = {
      id: chats.length + 1,
      name: `Chat ${chats.length + 1}`,
      messages: [
        { text: message, sender: "user" },
        {
          text: dummyResponses[
            Math.floor(Math.random() * dummyResponses.length)
          ],
          sender: "ai",
        },
      ],
    };
    setChats([...chats, newChat]);
    setActiveItem(newChat.name);
    setInputMessage("");
  };
  const sendMessage = () => {
    if (inputMessage.trim()) {
      if (activeItem === "") {
        startNewChat(inputMessage);
      } else {
        const updatedChats = chats.map((chat) => {
          if (chat.name === activeItem) {
            const userMessage = { text: inputMessage, sender: "user" };
            const aiResponse = {
              text: dummyResponses[
                Math.floor(Math.random() * dummyResponses.length)
              ],
              sender: "ai",
            };
            return {
              ...chat,
              messages: [...chat.messages, userMessage, aiResponse],
            };
          }
          return chat;
        });
        setChats(updatedChats);
        setInputMessage("");
      }
    }
  };

  return (
    <WithSidebar>
      {/* <Chats chats={messages} /> */}

      <div className="p-4 border-t">
        <div className="relative">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
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
