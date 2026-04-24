import { create } from "zustand";

interface AuthState {
  accessToken: string | null;
  setAuth: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: typeof window !== "undefined" ? localStorage.getItem("access_token") : null,

  setAuth: (accessToken, refreshToken) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    set({ accessToken });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ accessToken: null });
  },
}));
