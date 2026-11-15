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

/**
 * Thực thi GET request tới Backend API.
 * Nếu đang ở chế độ mock hoặc Backend của TV2 chưa khởi chạy (network error / 502 / 504),
 * tự động gọi hàm fallback để UI của TV3 hoạt động độc lập chuẩn hợp đồng OpenAPI.
 */
export async function apiGetWithFallback<T>(
  path: string,
  queryParams: Record<string, string | number | boolean | undefined | null>,
  fallbackFn: () => T
): Promise<T> {
  if (isForceMockMode()) {
    return fallbackFn();
  }

  const searchParams = new URLSearchParams();
  Object.entries(queryParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, String(value));
    }
  });

  const queryString = searchParams.toString();
  const url = `${getApiBaseUrl()}${path}${queryString ? `?${queryString}` : ''}`;

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    });

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
      throw new ApiClientError(
        response.status,
        errorBody.error?.code ?? 'HTTP_ERROR',
        errorBody.error?.message ?? `Lỗi HTTP ${response.status}`,
        errorBody.error?.trace_id
      );
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
