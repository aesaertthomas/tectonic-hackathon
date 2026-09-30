import { createContext, useContext } from "react";
import type { Me } from "./types";

export type AuthState = { me: Me; logout: () => Promise<void>; expire: () => void };

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthContext");
  return ctx;
}
