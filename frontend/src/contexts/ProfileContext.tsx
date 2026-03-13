import {
  createContext,
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/api/client";
import { useAuth } from "@/hooks/useAuth";

export interface Profile {
  user_id: string;
  display_name: string | null;
  bio: string | null;
  region: string | null;
  languages: string[] | null;
  providers: string[] | null;
  preferences: Record<string, unknown> | null;
  consent: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

interface ProfileUpdatePayload {
  display_name?: string | null;
  bio?: string | null;
  region?: string | null;
  languages?: string[] | null;
  providers?: string[] | null;
}

interface ProfileState {
  profile: Profile | null;
  loading: boolean;
  error: string | null;
}

interface ProfileContextValue extends ProfileState {
  hasProfile: boolean;
  needsOnboarding: boolean;
  fetchProfile: () => Promise<void>;
  patchProfile: (data: ProfileUpdatePayload) => Promise<void>;
}

const ProfileContext = createContext<ProfileContextValue | null>(null);

export function ProfileProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [state, setState] = useState<ProfileState>({
    profile: null,
    loading: true,
    error: null,
  });

  const fetchProfile = useCallback(async () => {
    const token = localStorage.getItem("gurupix_token");
    if (!token || !user) {
      setState({ profile: null, loading: false, error: null });
      return;
    }
    try {
      const profile = await api.get<Profile | null>("/api/v1/profiles/me");
      setState({ profile, loading: false, error: null });
    } catch {
      setState({ profile: null, loading: false, error: null });
    }
  }, [user]);

  useEffect(() => {
    if (!user) {
      setState({ profile: null, loading: false, error: null });
      return;
    }
    fetchProfile();
  }, [user, fetchProfile]);

  const patchProfile = useCallback(async (data: ProfileUpdatePayload) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const profile = await api.patch<Profile>("/api/v1/profiles/me", data);
      setState({ profile, loading: false, error: null });
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "detail" in err
          ? (err as { detail: string }).detail
          : "Failed to update profile";
      setState((s) => ({ ...s, loading: false, error: msg }));
    }
  }, []);

  const isAdmin = user?.is_admin ?? false;
  const value: ProfileContextValue = {
    ...state,
    hasProfile: state.profile !== null,
    needsOnboarding: !state.loading && state.profile === null && !isAdmin,
    fetchProfile,
    patchProfile,
  };

  return (
    <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>
  );
}

export { ProfileContext };
