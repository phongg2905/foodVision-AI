import { ErrorResponse } from './types';

const DEFAULT_BASE_URL = '/api/v1';

export function getApiBaseUrl(): string {
  const configured = import.meta.env?.VITE_API_BASE_URL;
  return typeof configured === 'string' && configured.trim().length > 0
    ? configured.replace(/\/+$/, '')
    : DEFAULT_BASE_URL;
}

export function isForceMockMode(): boolean {
  const mode = import.meta.env?.VITE_API_MOCK_MODE;
  return mode === 'true';
}

export function isFallbackAllowed(): boolean {
  const mode = import.meta.env?.VITE_API_MOCK_MODE;
  return mode !== 'false';
}

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly traceId?: string;

  constructor(status: number, code: string, message: string, traceId?: string) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = code;
    this.traceId = traceId;
  }
}

function isAbortError(err: unknown): boolean {
  if (!err || typeof err !== 'object') return false;
  return (err as { name?: string }).name === 'AbortError';
}

function parseErrorEnvelope(
  status: number,
  body: Partial<ErrorResponse> | null
): ApiClientError {
  const code = body?.code ?? body?.error?.code ?? 'HTTP_ERROR';
  const message =
    body?.message ?? body?.error?.message ?? `Lỗi HTTP ${status}`;
  const traceId = body?.request_id ?? body?.error?.trace_id;
  return new ApiClientError(status, code, message, traceId);
}

async function executeJsonRequestWithFallback<T>(
  url: string,
  init: RequestInit,
  fallbackFn: () => T
): Promise<T> {
  if (isForceMockMode()) {
    return fallbackFn();
  }

  try {
    const response = await fetch(url, init);
    const contentType = response.headers.get('content-type') ?? '';

    if (!contentType.includes('application/json')) {
      throw new ApiClientError(
        response.status,
        'NON_JSON_RESPONSE',
        'Phản hồi từ máy chủ không đúng định dạng JSON.'
      );
    }

    if (!response.ok) {
      const errorBody = (await response.json()) as Partial<ErrorResponse>;
      // F3: Tuyệt đối KHÔNG nuốt lỗi HTTP 4xx/5xx sang mock data; chỉ fallback khi VITE_API_MOCK_MODE=true hoặc lỗi mạng TypeError
      throw parseErrorEnvelope(response.status, errorBody);
    }

    return (await response.json()) as T;
  } catch (err) {
    if (isAbortError(err)) {
      throw err;
    }
    if (err instanceof ApiClientError) {
      throw err;
    }
    if (err instanceof TypeError && isFallbackAllowed()) {
      return fallbackFn();
    }
    throw err;
  }
}

/**
 * Thực thi GET request tới Backend API (hỗ trợ AbortSignal).
 */
export async function apiGetWithFallback<T>(
  path: string,
  queryParams: Record<string, string | number | boolean | undefined | null>,
  fallbackFn: () => T,
  signal?: AbortSignal
): Promise<T> {
  const searchParams = new URLSearchParams();
  Object.entries(queryParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, String(value));
    }
  });

  const queryString = searchParams.toString();
  const url = `${getApiBaseUrl()}${path}${queryString ? `?${queryString}` : ''}`;

  return executeJsonRequestWithFallback<T>(
    url,
    {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
      signal,
    },
    fallbackFn
  );
}

/**
 * Thực thi POST request JSON tới Backend API (hỗ trợ AbortSignal).
 */
export async function apiPostWithFallback<TBody, TRes>(
  path: string,
  body: TBody,
  fallbackFn: () => TRes,
  signal?: AbortSignal
): Promise<TRes> {
  const url = `${getApiBaseUrl()}${path}`;

  return executeJsonRequestWithFallback<TRes>(
    url,
    {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal,
    },
    fallbackFn
  );
}

/**
 * Thực thi POST multipart/form-data (VD: POST /api/v1/ai/detect).
 * Bảo toàn 100% các mã lỗi nghiệp vụ có cấu trúc từ Backend (401, 413, 415, 422, 429, 500, 503, 504).
 */
export async function apiPostMultipartWithFallback<TRes>(
  path: string,
  formData: FormData,
  fallbackFn: () => TRes | Promise<TRes>,
  signal?: AbortSignal
): Promise<TRes> {
  if (isForceMockMode()) {
    return await fallbackFn();
  }

  const url = `${getApiBaseUrl()}${path}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
      },
      body: formData,
      signal,
    });

    const contentType = response.headers.get('content-type') ?? '';

    if (!contentType.includes('application/json')) {
      throw new ApiClientError(
        response.status,
        'NON_JSON_RESPONSE',
        'Phản hồi từ dịch vụ nhận diện ảnh không đúng định dạng JSON.'
      );
    }

    if (!response.ok) {
      const errorBody = (await response.json()) as Partial<ErrorResponse>;
      throw parseErrorEnvelope(response.status, errorBody);
    }

    return (await response.json()) as TRes;
  } catch (err) {
    if (isAbortError(err)) {
      throw err;
    }
    if (err instanceof ApiClientError) {
      throw err;
    }
    if (err instanceof TypeError && isFallbackAllowed()) {
      return await fallbackFn();
    }
    throw err;
  }
}
