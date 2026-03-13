import { useContext } from "react";
import { ProfileContext } from "@/contexts/ProfileContext";
import type { Profile } from "@/contexts/ProfileContext";

export function useProfile() {
  const ctx = useContext(ProfileContext);
  if (!ctx) {
    throw new Error("useProfile must be used within ProfileProvider");
  }
  return ctx;
}

export type { Profile };
