import { create } from "zustand";

export type Message = {
  message: string;
  sender: "human" | "ai";
};

export type ChatType = {
  id: string;
  title: string;
  user_email: string;
  messages: Message[];
};

type State = {
  chat: ChatType;
};

type Action = {
  setActiveChat: (chat: ChatType) => void;
  addNewMessage: (message: Message) => void;
};

export const useActiveChat = create<State & Action>((set) => ({
  chat: {
    id: "",
    title: "",
    user_email: "",
    messages: [],
  },
  setActiveChat: (chat) => set({ chat }),
  addNewMessage: (message) =>
    set((state) => ({
      chat: {
        ...state.chat,
        messages: [...state.chat.messages, message],
      },
    })),
}));
