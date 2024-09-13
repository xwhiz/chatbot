import { create } from "zustand";

type State = {
  chatIDs: string[];
};

type Action = {
  setChatIDs: (chatIDs: string[]) => void;
};

export const useUserChatsStore = create<State & Action>((set) => ({
  chatIDs: [],
  setChatIDs: (chatIDs) => set({ chatIDs }),
}));
