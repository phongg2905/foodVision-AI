# ADR-001 — Frontend React và Backend FastAPI tách biệt

- **Status:** Proposed
- **Date:** 03/11/2026
- **Context:** cần website responsive, giao diện người dùng hiện đại, Python để nạp/tích hợp YOLO và tính thuật toán gợi ý; FE/BE cần phát triển song song.
- **Decision:** React + TypeScript + Vite + Tailwind; backend Python FastAPI expose REST JSON và multipart upload theo OpenAPI.
- **Alternatives:** Next.js fullstack + Python inference riêng (thêm cầu nối); Django monolith (nặng hơn cho nhóm quen REST); chỉ Supabase Edge Functions (không phù hợp để mặc định chạy YOLO inference Python).
- **Consequences:** có CORS, deployment 2 thành phần và contract API phải đồng bộ; đổi lại tách module, Swagger dễ test, FE có thể mock.
- **Revisit when:** nhóm có yêu cầu SSR/SEO lớn hoặc hạn chế tài nguyên hosting.
- **References:** `docs/02-architecture/system-architecture.md`, `docs/03-api/openapi.yaml`.
