import { create } from "zustand";

export type Message = {
  message: string;
  sender: "user" | "ai";
};

type State = {
  activeChatMessages: Message[];
};

type Action = {
  setActiveChatMessages: (messages: Message[]) => void;
  addNewMessage: (message: Message) => void;
};

export const useActiveChatMessages = create<State & Action>((set) => ({
  activeChatMessages: [],
  setActiveChatMessages: (messages) => set({ activeChatMessages: messages }),
  addNewMessage: (message) => {
    set((state) => ({
      activeChatMessages: [...state.activeChatMessages, message],
    }));
  },
}));
