import { clearAuthToken, getAuthToken } from "./auth";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  error: ApiErrorPayload | null;
}

export class ApiRequestError extends Error {
  readonly code: string;
  readonly statusCode: number;
  readonly details?: unknown;

  constructor(
    message: string,
    code = "REQUEST_FAILED",
    statusCode = 0,
    details?: unknown,
  ) {
    super(message);
    this.name = "ApiRequestError";
    this.code = code;
    this.statusCode = statusCode;
    this.details = details;
  }
}

type RequestMethod = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

interface RequestOptions {
  url: string;
  method?: RequestMethod;
  data?: object;
}

export function request<T>({ url, method = "GET", data }: RequestOptions): Promise<T> {
  return new Promise((resolve, reject) => {
    const token = getAuthToken();

    uni.request({
      url: `${API_BASE_URL}${url}`,
      // uni-app 类型声明遗漏了 PATCH，但微信小程序运行时支持该方法。
      method: method as unknown as "GET" | "POST" | "PUT" | "DELETE" | "OPTIONS" | "HEAD" | "TRACE" | "CONNECT",
      data: data as Record<string, unknown> | undefined,
      header: token ? { Authorization: `Bearer ${token}` } : {},
      success: (response) => {
        const envelope = response.data as ApiEnvelope<T>;

        if (response.statusCode === 401) {
          clearAuthToken();
        }

        if (response.statusCode === 204) {
          resolve(undefined as T);
          return;
        }

        if (
          response.statusCode >= 200 &&
          response.statusCode < 300 &&
          envelope?.success &&
          envelope.data !== null
        ) {
          resolve(envelope.data);
          return;
        }

        const error = envelope?.error;
        reject(
          new ApiRequestError(
            error?.message || "请求失败，请稍后再试",
            error?.code || `HTTP_${response.statusCode}`,
            response.statusCode,
            error?.details,
          ),
        );
      },
      fail: (error) => {
        reject(new ApiRequestError(error.errMsg || "网络连接失败"));
      },
    });
  });
}
