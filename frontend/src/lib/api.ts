import axios from "axios";
import { useAuthStore } from "@/store/authStore";


const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  withCredentials: true, // refresh cookie
  
});

// 🔐 Attach access token automatically
api.interceptors.request.use((config: any) => {
  const token = useAuthStore.getState().accessToken;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;

});

export default api;
