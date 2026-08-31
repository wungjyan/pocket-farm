const TOKEN_KEY = "pocket_farm_access_token";
// 与 services/user-context.ts 的存储 key 保持一致，退出/鉴权失效时同步清除。
const CURRENT_USER_KEY = "pocket_farm_current_user";

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
  uni.removeStorageSync(CURRENT_USER_KEY);
}
