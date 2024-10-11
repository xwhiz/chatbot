import { create } from "zustand";

type State = {
  isGenerating: boolean;
};

type Action = {
  setIsGenerating: (isGenerating: boolean) => void;
};

export const useIsGeneratingStore = create<State & Action>((set) => ({
  isGenerating: false,
  setIsGenerating: (isGenerating) => set({ isGenerating }),
}));
