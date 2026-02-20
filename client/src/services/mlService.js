/**
 * ML Service - Client interface for ML data
 *
 * NOTE: The client does NOT call HF or Render ML endpoints directly.
 * ML predictions are made by the RPi → HF Space, saved to Supabase,
 * and read back through Render's ml-history routes.
 *
 * All ML API calls go through mlAPI in services/api.js which handles
 * auth tokens and base URL automatically.
 *
 * This file is kept for backward compatibility only.
 * Prefer importing { mlAPI } from './api' directly.
 */

export { mlAPI as default } from "./api";
