
export const API_BASE = "http://127.0.0.1:8000";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const contentType = response.headers.get("content-type") ?? "";

  const data: unknown = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;

    if (typeof data === "string" && data) {
      message = data;
    } else if (
      typeof data === "object" &&
      data !== null &&
      "detail" in data &&
      typeof data.detail === "string"
    ) {
      message = data.detail;
    }

    throw new Error(message);
  }

  return data as T;
}

export const apiClient = {
  get<T>(path: string): Promise<T> {
    return request<T>(path, {
      method: "GET",
    });
  },

  post<T>(path: string, body: unknown): Promise<T> {
    return request<T>(path, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  delete(path: string): Promise<void> {
    return request<void>(path, {
      method: "DELETE",
    });
  },

  async postStream(path: string, body: unknown): Promise<Response> {
    const response = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok || !response.body) {
      throw new Error(
        `Streaming request failed (${response.status}).`
      );
    }

    return response;
  },
};
