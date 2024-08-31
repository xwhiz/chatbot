import { create } from "zustand";

type State = {
  isOpen: boolean;
};

type Action = {
  toggle: () => void;
};

export const useSidebarStore = create<State & Action>((set) => ({
  isOpen: false,
  toggle: () => set((state) => ({ isOpen: !state.isOpen })),
}));
