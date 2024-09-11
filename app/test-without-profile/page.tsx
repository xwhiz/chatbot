"use client";
import React, { useState, useRef, useEffect } from "react";
import {
  ChevronDown,
  User,
  Users,
  MessageSquare,
  Upload,
  Plus,
  Send,
  Lock,
} from "lucide-react";

const DeleteIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M3 6h18"></path>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path>
    <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
    <line x1="10" y1="11" x2="10" y2="17"></line>
    <line x1="14" y1="11" x2="14" y2="17"></line>
  </svg>
);

const dummyResponses = [
  "That's an interesting point. Can you elaborate?",
  "I see. Have you considered looking at it from a different perspective?",
  "That's a great question. Let me think about that for a moment.",
  "I understand your concern. Here's what I think about that...",
  "Thank you for sharing that. It's definitely something to consider.",
];

const Layout = () => {
  const [role, setRole] = useState("user");
  const [activeItem, setActiveItem] = useState("");
  const [chats, setChats] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const chatContainerRef = useRef(null);

  const menuItems = {
    admin: [
      { name: "Dashboard", icon: <ChevronDown /> },
      { name: "Users", icon: <Users /> },
      { name: "Chats", icon: <MessageSquare /> },
      { name: "Upload Documents", icon: <Upload /> },
    ],
    user: [{ name: "Profile", icon: <User /> }],
  };

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [chats]);

  const deleteChat = (id) => {
    setChats(chats.filter((chat) => chat.id !== id));
    if (activeItem === `Chat ${id}`) {
      setActiveItem("");
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
    if (inputMessage.trim() && activeItem !== "Profile") {
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

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleChangePassword = (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setPasswordMessage("New passwords don't match");
    } else if (newPassword.length < 8) {
      setPasswordMessage("New password must be at least 8 characters long");
    } else {
      // Here you would typically send a request to your backend to change the password
      setPasswordMessage("Password changed successfully");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    }
  };

  const activeChat = chats.find((chat) => chat.name === activeItem);

  return (
    <div className="flex h-screen bg-gray-100">
      <div className="w-64 bg-white shadow-md flex flex-col h-full">
        <div className="p-4 border-b">
          <select
            className="w-full p-2 border rounded"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          >
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <nav className="mt-4 flex-grow overflow-y-auto">
          {role === "admin" ? (
            menuItems.admin.map((item) => (
              <a
                key={item.name}
                href="#"
                className={`flex items-center px-4 py-2 text-gray-700 hover:bg-gray-200 ${
                  activeItem === item.name ? "bg-gray-200" : ""
                }`}
                onClick={() => setActiveItem(item.name)}
              >
                {item.icon}
                <span className="ml-2">{item.name}</span>
              </a>
            ))
          ) : (
            <>
              <a
                href="#"
                className={`flex items-center px-4 py-2 text-gray-700 hover:bg-gray-200 ${
                  activeItem === "Profile" ? "bg-gray-200" : ""
                }`}
                onClick={() => setActiveItem("Profile")}
              >
                <User />
                <span className="ml-2">Profile</span>
              </a>
              <div className="px-4 py-2 text-gray-700 font-semibold">Chats</div>
              <div className="overflow-y-auto">
                {chats.map((chat) => (
                  <div
                    key={chat.id}
                    className={`flex items-center justify-between px-4 py-2 text-gray-700 hover:bg-gray-200 ${
                      activeItem === chat.name ? "bg-gray-200" : ""
                    }`}
                  >
                    <a
                      href="#"
                      className="flex items-center flex-grow"
                      onClick={() => setActiveItem(chat.name)}
                    >
                      <MessageSquare className="w-4 h-4" />
                      <span className="ml-2">{chat.name}</span>
                    </a>
                    <button
                      onClick={() => deleteChat(chat.id)}
                      className="text-gray-500 hover:text-red-500"
                    >
                      <DeleteIcon />
                    </button>
                  </div>
                ))}
              </div>
              <a
                href="#"
                className="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-200 mt-2"
                onClick={() => {
                  setActiveItem("");
                  setInputMessage("");
                }}
              >
                <Plus className="w-4 h-4" />
                <span className="ml-2">New Chat</span>
              </a>
            </>
          )}
        </nav>
      </div>
      <div className="lg:w-8/12 xl:w-7/12 2xl:w-6/12 mx-auto flex flex-col">
        <div ref={chatContainerRef} className="flex-1 p-8 overflow-y-auto">
          {activeItem ? (
            <>
              <h1 className="text-2xl font-bold mb-4">{activeItem}</h1>
              {activeChat && (
                <div className="space-y-4">
                  {activeChat.messages.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${
                        message.sender === "user"
                          ? "justify-end"
                          : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-xs rounded-lg p-3 ${
                          message.sender === "user"
                            ? "bg-blue-500 text-white"
                            : "bg-gray-300"
                        }`}
                      >
                        {message.text}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {activeItem === "Profile" && (
                <div className="flex flex-col items-center justify-center h-full">
                  <img
                    src="/api/placeholder/200/200"
                    alt="User Avatar"
                    className="w-40 h-40 rounded-full mb-4"
                  />
                  <h2 className="text-2xl font-bold mb-4">John Doe</h2>
                  <form
                    onSubmit={handleChangePassword}
                    className="w-full max-w-sm"
                  >
                    <div className="mb-4">
                      <label
                        className="block text-gray-700 text-sm font-bold mb-2"
                        htmlFor="current-password"
                      >
                        Current Password
                      </label>
                      <input
                        className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                        id="current-password"
                        type="password"
                        value={currentPassword}
                        onChange={(e) => setCurrentPassword(e.target.value)}
                        required
                      />
                    </div>
                    <div className="mb-4">
                      <label
                        className="block text-gray-700 text-sm font-bold mb-2"
                        htmlFor="new-password"
                      >
                        New Password
                      </label>
                      <input
                        className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                        id="new-password"
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                      />
                    </div>
                    <div className="mb-6">
                      <label
                        className="block text-gray-700 text-sm font-bold mb-2"
                        htmlFor="confirm-password"
                      >
                        Confirm New Password
                      </label>
                      <input
                        className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                        id="confirm-password"
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        required
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <button
                        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline flex items-center"
                        type="submit"
                      >
                        <Lock className="w-4 h-4 mr-2" />
                        Change Password
                      </button>
                    </div>
                  </form>
                  {passwordMessage && (
                    <p
                      className={`mt-4 text-sm ${
                        passwordMessage.includes("successfully")
                          ? "text-green-500"
                          : "text-red-500"
                      }`}
                    >
                      {passwordMessage}
                    </p>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full">
              <h1 className="text-3xl font-bold mb-4">Welcome to P. Chatbot</h1>
              <p className="text-xl mb-8">How can I assist you today?</p>
            </div>
          )}
        </div>
        {activeItem !== "Profile" && (
          <div className="p-4 border-t">
            <div className="relative">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full p-2 pr-12 border rounded"
                placeholder={
                  activeItem ? "Type your message..." : "Ask me anything..."
                }
              />
              <button
                onClick={sendMessage}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 bg-blue-500 text-white rounded-full hover:bg-blue-600"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Layout;
