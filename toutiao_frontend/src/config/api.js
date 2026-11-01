import axios from "axios";

export const TOKEN_KEY = "toutiao_token";
export const DEFAULT_AVATAR =
  "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg";

export const apiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
};

export const aiChatConfig = {
  apiEndpoint: "https://api.deepseek.com/chat/completions",
  apiKey: import.meta.env.VITE_AI_API_KEY || "",
  model: "deepseek-flash",
};

const api = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: 15000,
});

const aiApi = axios.create({
  timeout: 60000,
});

function camelizeKey(key) {
  return key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

export function normalizeData(value) {
  if (Array.isArray(value)) return value.map(normalizeData);
  if (!value || typeof value !== "object") return value;

  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [
      camelizeKey(key),
      normalizeData(item),
    ]),
  );
}

function statusMessage(status) {
  const messages = {
    400: "请求失败",
    401: "登录已过期，请重新登录",
    404: "内容不存在",
    422: "请求参数校验失败",
    500: "服务器内部错误，请稍后重试",
  };
  return messages[status] || "请求失败，请稍后重试";
}

function normalizedError(error) {
  if (error?.isAppError) return error;

  const status = error?.response?.status;
  const backendMessage = error?.response?.data?.message;
  let message = backendMessage || statusMessage(status);

  if (!error?.response) {
    message =
      error?.code === "ECONNABORTED"
        ? "请求超时，请稍后重试"
        : "网络异常，请检查连接后重试";
  }

  const appError = new Error(message);
  appError.status = status;
  appError.original = error;
  appError.isAppError = true;
  return appError;
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = token;
  return config;
});

api.interceptors.response.use(
  (response) => {
    const payload = response.data;
    if (payload && typeof payload === "object" && "code" in payload) {
      const normalized = normalizeData(payload);
      if (normalized.code !== 200) {
        const appError = new Error(normalized.message || "请求失败");
        appError.status = normalized.code;
        appError.isAppError = true;
        return Promise.reject(appError);
      }
      return normalized.data;
    }
    return normalizeData(payload);
  },
  (error) => {
    const appError = normalizedError(error);
    const requestUrl = error?.config?.url || "";
    const isLoginRequest =
      requestUrl.includes("/user/login") ||
      requestUrl.includes("/user/register");

    if (appError.status === 401 && !isLoginRequest) {
      localStorage.removeItem(TOKEN_KEY);
      window.dispatchEvent(
        new CustomEvent("toutiao:unauthorized", { detail: appError }),
      );
    }

    return Promise.reject(appError);
  },
);

export const userApi = {
  register: (payload) => api.post("/user/register", payload),
  login: (payload) => api.post("/user/login", payload),
  getInfo: () => api.get("/user/info"),
  update: (payload) => api.put("/user/update", payload),
  updatePassword: (payload) => api.put("/user/password", payload),
};

export const newsApi = {
  getCategories: (params = {}) => api.get("/news/categories", { params }),
  getList: (params) => api.get("/news/list", { params }),
  getDetail: (id) => api.get("/news/detail", { params: { id } }),
};

export const favoriteApi = {
  check: (newsId) => api.get("/favorite/check", { params: { newsId } }),
  add: (newsId) => api.post("/favorite/add", { newsId }),
  remove: (newsId) => api.delete("/favorite/remove", { params: { newsId } }),
  getList: (params) => api.get("/favorite/list", { params }),
  clear: () => api.delete("/favorite/clear"),
};

export const historyApi = {
  add: (newsId) => api.post("/history/add", { newsId }),
  getList: (params) => api.get("/history/list", { params }),
  remove: (historyId) => api.delete(`/history/delete/${historyId}`),
  clear: () => api.delete("/history/clear"),
};

export async function sendAiChat(messages) {
  if (!aiChatConfig.apiKey) {
    throw new Error("未配置 VITE_AI_API_KEY，暂时无法使用 AI 问答");
  }

  try {
    const response = await aiApi.post(
      aiChatConfig.apiEndpoint,
      {
        model: aiChatConfig.model,
        messages,
        stream: false,
      },
      {
        headers: {
          Authorization: `Bearer ${aiChatConfig.apiKey}`,
          "Content-Type": "application/json",
        },
      },
    );

    const content = response.data?.choices?.[0]?.message?.content;
    if (!content) throw new Error("AI 服务未返回有效内容");
    return content;
  } catch (error) {
    if (error?.isAppError) throw error;
    const status = error?.response?.status;
    let message = "AI 服务请求失败，请稍后重试";

    if (status === 401 || status === 403) message = "AI API Key 无效或已过期";
    else if (status === 429) message = "AI 请求过于频繁，请稍后重试";
    else if (!error?.response)
      message = "AI 服务连接失败，请检查网络、CORS 或 API Key";

    const appError = new Error(message);
    appError.status = status;
    appError.original = error;
    throw appError;
  }
}
