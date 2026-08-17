const TOKEN_KEY = "pocket_farm_access_token";

export function getAuthToken(): string {
  return String(uni.getStorageSync(TOKEN_KEY) || "");
}

export function hasAuthToken(): boolean {
  return Boolean(getAuthToken());
}

export function setAuthToken(token: string): void {
  uni.setStorageSync(TOKEN_KEY, token);
}

export function clearAuthToken(): void {
  uni.removeStorageSync(TOKEN_KEY);
}
