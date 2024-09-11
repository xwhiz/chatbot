import { create } from "zustand";

type State = {
  chats: {
    id: string;
    name: string;
    messages: { text: string; sender: string }[];
  }[];
};

type Action = {
  addChat: (chat: {
    id: string;
    name: string;
    messages: { text: string; sender: string }[];
  }) => void;
  deleteChat: (chat: string) => void;
};

export const useChatsStore = create<State & Action>((set) => ({
  chats: [],
  addChat: (chat) => set((state) => ({ chats: [...state.chats, chat] })),
  deleteChat: (chat) =>
    set((state) => ({ chats: state.chats.filter((c) => c.id !== chat) })),
}));
