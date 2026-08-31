import { ref } from "vue";
import { getCurrentUser, type User } from "./user";

/**
 * 全局当前用户上下文。
 * 用户信息只在登录（登录响应携带）与修改昵称（更新响应携带）时变化，
 * 由这两个写入点直接 setUser，Tab 页只读不请求。
 */
const CURRENT_USER_KEY = "pocket_farm_current_user";

function readStoredUser(): User | null {
  const value = uni.getStorageSync(CURRENT_USER_KEY);
  if (!value) return null;

  try {
    const parsed = typeof value === "string" ? JSON.parse(value) : value;
    if (typeof parsed?.id !== "number" || typeof parsed?.phoneNumber !== "string") {
      return null;
    }
    return parsed as User;
  } catch {
    return null;
  }
}

const currentUser = ref<User | null>(readStoredUser());
let pendingUserLoad: Promise<User | null> | null = null;

export function useUserContext() {
  function setUser(user: User | null): void {
    currentUser.value = user;
    if (user) {
      uni.setStorageSync(CURRENT_USER_KEY, JSON.stringify(user));
    } else {
      uni.removeStorageSync(CURRENT_USER_KEY);
    }
  }

  /**
   * 兜底加载：本地无缓存时请求一次 /users/me（如本次重构前已登录的老会话）。
   * 单飞保护，并发调用只产生一次请求。
   */
  function ensureCurrentUser(): Promise<User | null> {
    if (currentUser.value) return Promise.resolve(currentUser.value);
    if (!pendingUserLoad) {
      pendingUserLoad = getCurrentUser()
        .then((user) => {
          setUser(user);
          return user;
        })
        .finally(() => {
          pendingUserLoad = null;
        });
    }
    return pendingUserLoad;
  }

  return { currentUser, setUser, ensureCurrentUser };
}
