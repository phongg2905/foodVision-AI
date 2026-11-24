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
      if (isFallbackAllowed()) {
        return fallbackFn();
      }
      throw new ApiClientError(
        response.status,
        'NON_JSON_RESPONSE',
        'Phản hồi từ máy chủ không đúng định dạng JSON.'
      );
    }

    if (!response.ok) {
      const errorBody = (await response.json()) as Partial<ErrorResponse>;
      if (response.status >= 500 && isFallbackAllowed()) {
        return fallbackFn();
      }
      throw parseErrorEnvelope(response.status, errorBody);
    }

    return (await response.json()) as T;
  } catch (err) {
    if (err instanceof ApiClientError && err.status < 500) {
      throw err;
    }
    if (isFallbackAllowed()) {
      return fallbackFn();
    }
    throw err;
  }
}

/**
 * Thực thi GET request tới Backend API.
 * Nếu đang ở chế độ mock hoặc Backend chưa khởi chạy (network error / 5xx),
 * tự động gọi hàm fallback để UI của TV3 hoạt động độc lập chuẩn OpenAPI.
 */
export async function apiGetWithFallback<T>(
  path: string,
  queryParams: Record<string, string | number | boolean | undefined | null>,
  fallbackFn: () => T
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
    },
    fallbackFn
  );
}

/**
 * Thực thi POST request JSON tới Backend API kèm fallback chuẩn OpenAPI khi Backend offline.
 * Giữ nguyên các lỗi nghiệp vụ/hợp đồng 4xx (VD: 422 INVALID_INGREDIENTS) thay vì nuốt lỗi.
 */
export async function apiPostWithFallback<TBody, TRes>(
  path: string,
  body: TBody,
  fallbackFn: () => TRes
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
    },
    fallbackFn
  );
}

/**
 * Thực thi POST multipart/form-data (VD: POST /api/v1/ai/detect).
 * Bảo toàn 100% các mã lỗi nghiệp vụ có cấu trúc từ Backend (401, 413, 415, 422, 429, 503 MODEL_NOT_READY, 504 INFERENCE_TIMEOUT)
 * để giao diện hiển thị đúng cảnh báo & lối tắt nhập tay FR-18 (TC-05, TC-06, TC-29, TC-30).
 * Chỉ fallback sang mock khi chạy độc lập không có Backend (network error / non-JSON proxy response).
 */
export async function apiPostMultipartWithFallback<TRes>(
  path: string,
  formData: FormData,
  fallbackFn: () => TRes | Promise<TRes>
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
    });

    const contentType = response.headers.get('content-type') ?? '';

    if (!contentType.includes('application/json')) {
      if (isFallbackAllowed()) {
        return await fallbackFn();
      }
      throw new ApiClientError(
        response.status,
        'NON_JSON_RESPONSE',
        'Phản hồi từ dịch vụ nhận diện ảnh không đúng định dạng JSON.'
      );
    }

    if (!response.ok) {
      const errorBody = (await response.json()) as Partial<ErrorResponse>;
      const hasCanonicalCode = Boolean(
        errorBody?.code || errorBody?.error?.code
      );
      if (!hasCanonicalCode && response.status >= 500 && isFallbackAllowed()) {
        return await fallbackFn();
      }
      throw parseErrorEnvelope(response.status, errorBody);
    }

    return (await response.json()) as TRes;
  } catch (err) {
    if (err instanceof ApiClientError) {
      throw err;
    }
    if (isFallbackAllowed()) {
      return await fallbackFn();
    }
    throw err;
  }
}
