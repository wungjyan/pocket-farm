import { setAuthToken } from "./auth";
import { request } from "./http";

export interface User {
  id: number;
  phoneNumber: string;
  nickname: string | null;
  createdAt?: string;
  updatedAt?: string;
}

interface LoginResponse {
  accessToken: string;
  tokenType: string;
  user: User;
}

export async function login(
  phoneNumber: string,
  verificationCode: string,
): Promise<LoginResponse> {
  const result = await request<LoginResponse>({
    url: "/auth/login",
    method: "POST",
    data: { phoneNumber, verificationCode },
  });
  setAuthToken(result.accessToken);
  return result;
}

export function getCurrentUser(): Promise<User> {
  return request<User>({ url: "/users/me" });
}

export function updateCurrentUser(nickname: string | null): Promise<User> {
  return request<User>({
    url: "/users/me",
    method: "PATCH",
    data: { nickname },
  });
}
