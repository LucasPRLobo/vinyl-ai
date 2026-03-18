import { create } from "zustand";
import type { CollectionItem, SearchResult } from "./types";

interface AppStore {
  // Auth
  token: string | null;
  userId: string;
  userName: string;
  isLoggedIn: boolean;
  login: (token: string, userId: string, name: string) => void;
  logout: () => void;
  loadAuth: () => void;

  // Collection
  collection: CollectionItem[];
  setCollection: (items: CollectionItem[]) => void;

  // Smart Add
  searchResults: SearchResult[];
  setSearchResults: (results: SearchResult[]) => void;
  isSearching: boolean;
  setIsSearching: (v: boolean) => void;
  isAdding: boolean;
  setIsAdding: (v: boolean) => void;
}

export const useStore = create<AppStore>((set) => ({
  token: null,
  userId: "default-user",
  userName: "",
  isLoggedIn: false,
  login: (token, userId, name) => {
    localStorage.setItem("crate_token", token);
    localStorage.setItem("crate_user_id", userId);
    localStorage.setItem("crate_user_name", name);
    set({ token, userId, userName: name, isLoggedIn: true });
  },
  logout: () => {
    localStorage.removeItem("crate_token");
    localStorage.removeItem("crate_user_id");
    localStorage.removeItem("crate_user_name");
    set({ token: null, userId: "default-user", userName: "", isLoggedIn: false });
  },
  loadAuth: () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem("crate_token");
    const userId = localStorage.getItem("crate_user_id");
    const name = localStorage.getItem("crate_user_name");
    if (token && userId) {
      set({ token, userId, userName: name || "", isLoggedIn: true });
    }
  },

  collection: [],
  setCollection: (items) => set({ collection: items }),

  searchResults: [],
  setSearchResults: (results) => set({ searchResults: results }),
  isSearching: false,
  setIsSearching: (v) => set({ isSearching: v }),
  isAdding: false,
  setIsAdding: (v) => set({ isAdding: v }),
}));
