// Translated from MSSQL to PostgreSQL by MigrateIQ

import { getPool } from '../config/database.config';

/**
 * Execute a stored procedure (PostgreSQL function) by name with optional parameters.
 * Uses PostgreSQL CALL syntax for procedures.
 */
export async function executeStoredProcedure(
  procName: string,
  params: Record<string, { value: unknown }> = {}
) {
  const pool = await getPool();

  const paramEntries = Object.entries(params);
  const values = paramEntries.map(([, { value }]) => value);
  const placeholders = paramEntries.map((_, i) => `$${i + 1}`).join(', ');

  const queryText = placeholders
    ? `CALL ${procName}(${placeholders})`
    : `CALL ${procName}()`;

  return pool.query(queryText, values);
}

/**
 * Get temporal history for a record.
 * Note: PostgreSQL does not have native FOR SYSTEM_TIME ALL syntax.
 * This implementation queries a separate history table following the
 * common pattern of storing historical records in a "{schema}.{table}_history" table.
 * Adjust the approach based on your temporal table implementation
 * (e.g., temporal_tables extension, triggers, or partitioned history tables).
 */
export async function getTemporalHistory(
  schema: string,
  tableName: string,
  pkColumn: string,
  pkValue: number
) {
  const pool = await getPool();

  // Query both the current table and the history table to emulate FOR SYSTEM_TIME ALL
  const result = await pool.query(
    `
      SELECT *,
        valid_from,
        valid_to,
        CASE WHEN valid_to = '9999-12-31 23:59:59.9999999' THEN 'Current' ELSE 'Historical' END AS record_status
      FROM (
        SELECT * FROM ${schema}.${tableName}
        WHERE ${pkColumn} = $1
        UNION ALL
        SELECT * FROM ${schema}.${tableName}_history
        WHERE ${pkColumn} = $1
      ) combined
      ORDER BY valid_from DESC
    `,
    [pkValue]
  );
  return result.rows;
}

/**
 * Full-text search using PostgreSQL tsvector/tsquery.
 */
export async function fullTextSearch(
  searchTerm: string,
  maxResults: number = 20
) {
  const pool = await getPool();
  const result = await pool.query(
    `
      SELECT
        si.stock_item_id,
        si.stock_item_name,
        ts_rank(to_tsvector('english', si.search_details), plainto_tsquery('english', $1)) AS search_rank
      FROM warehouse.stock_items si
      WHERE to_tsvector('english', si.search_details) @@ plainto_tsquery('english', $1)
      ORDER BY search_rank DESC
      LIMIT $2
    `,
    [searchTerm, maxResults]
  );
  return result.rows;
}
