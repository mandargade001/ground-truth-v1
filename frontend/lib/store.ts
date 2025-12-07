import { create } from 'zustand';

interface User {
    id: number;
    email: string;
}

interface AppState {
    user: User | null;
    isAuthenticated: boolean;
    accessToken: string | null;

    // Actions
    setAuth: (token: string, user: User) => void;
    logout: () => void;
}

export const useAppStore = create<AppState>((set) => ({
    user: null,
    isAuthenticated: false,
    accessToken: null,

    setAuth: (token, user) => {
        localStorage.setItem('access_token', token);
        set({ accessToken: token, user, isAuthenticated: true });
    },

    logout: () => {
        localStorage.removeItem('access_token');
        set({ accessToken: null, user: null, isAuthenticated: false });
    },
}));
