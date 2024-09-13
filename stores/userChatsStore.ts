import { create } from "zustand";

type ChatTitle = {
  id: string;
  title: string;
};

type State = {
  chatIDs: ChatTitle[];
};

type Action = {
  setChatIDs: (chatIDs: ChatTitle[]) => void;
};

export const useUserChatsStore = create<State & Action>((set) => ({
  chatIDs: [],
  setChatIDs: (chatIDs) => set({ chatIDs }),
}));
