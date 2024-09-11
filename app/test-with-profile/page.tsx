"use client";
import React, { useState } from "react";
import {
  User,
  Lock,
  Edit,
  ChevronDown,
  Users,
  MessageSquare,
  Upload,
} from "lucide-react";

const Layout = () => {
  const [role, setRole] = useState("user");
  const [activeItem, setActiveItem] = useState("Profile");
  const [userName, setUserName] = useState("John Doe");
  const [newUserName, setNewUserName] = useState("");
  const [isEditingName, setIsEditingName] = useState(false);
  const [nameChangePassword, setNameChangePassword] = useState("");
  const [nameChangeMessage, setNameChangeMessage] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");

  const menuItems = {
    admin: [
      { name: "Dashboard", icon: <ChevronDown /> },
      { name: "Users", icon: <Users /> },
      { name: "Chats", icon: <MessageSquare /> },
      { name: "Upload Documents", icon: <Upload /> },
    ],
    user: [{ name: "Profile", icon: <User /> }],
  };

  const handleChangeName = (e: any) => {
    e.preventDefault();
    if (nameChangePassword === "correctpassword") {
      setUserName(newUserName);
      setNameChangeMessage("Name changed successfully");
      setIsEditingName(false);
      setNewUserName("");
      setNameChangePassword("");
    } else {
      setNameChangeMessage("Incorrect password");
    }
  };

  const handleChangePassword = (e: any) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setPasswordMessage("New passwords don't match");
    } else if (newPassword.length < 8) {
      setPasswordMessage("New password must be at least 8 characters long");
    } else {
      setPasswordMessage("Password changed successfully");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    }
  };

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
          {role === "admin"
            ? menuItems.admin.map((item) => (
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
            : menuItems.user.map((item) => (
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
              ))}
        </nav>
      </div>
      <div className="flex-1 flex flex-col">
        <div className="flex-1 p-8 overflow-y-auto">
          <h1 className="text-2xl font-bold mb-4">{activeItem}</h1>
          {activeItem === "Profile" && (
            <div className="flex flex-col items-center justify-center">
              <img
                src="/next.svg"
                alt="User Avatar"
                className="w-32 h-32 rounded-full mb-4"
              />
              {isEditingName ? (
                <form
                  onSubmit={handleChangeName}
                  className="w-full max-w-sm mb-4"
                >
                  <div className="mb-4">
                    <label
                      className="block text-gray-700 text-sm font-bold mb-2"
                      htmlFor="new-name"
                    >
                      New Name
                    </label>
                    <input
                      className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                      id="new-name"
                      type="text"
                      value={newUserName}
                      onChange={(e) => setNewUserName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="mb-4">
                    <label
                      className="block text-gray-700 text-sm font-bold mb-2"
                      htmlFor="name-change-password"
                    >
                      Confirm Password
                    </label>
                    <input
                      className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                      id="name-change-password"
                      type="password"
                      value={nameChangePassword}
                      onChange={(e) => setNameChangePassword(e.target.value)}
                      required
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <button
                      className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                      type="submit"
                    >
                      Change Name
                    </button>
                    <button
                      className="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                      onClick={() => setIsEditingName(false)}
                      type="button"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <div className="flex items-center mb-4">
                  <h2 className="text-2xl font-bold mr-2">{userName}</h2>
                  <button
                    onClick={() => setIsEditingName(true)}
                    className="bg-blue-500 hover:bg-blue-700 text-white rounded-full p-1"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
              )}
              {nameChangeMessage && (
                <p
                  className={`mb-4 text-sm ${
                    nameChangeMessage.includes("successfully")
                      ? "text-green-500"
                      : "text-red-500"
                  }`}
                >
                  {nameChangeMessage}
                </p>
              )}
              <form onSubmit={handleChangePassword} className="w-full max-w-sm">
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
        </div>
      </div>
    </div>
  );
};

export default Layout;
