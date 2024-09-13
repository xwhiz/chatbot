import { create } from "zustand";

type State = {
  activeChatId: string;
};
type Action = {
  setActiveChatId: (id: string) => void;
};

export const useActiveChatID = create<State & Action>((set) => ({
  activeChatId: "",
  setActiveChatId: (id) => set({ activeChatId: id }),
}));
