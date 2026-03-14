import { getPool, sql } from '../config/database.config';

/**
 * Execute a stored procedure by name with optional parameters.
 * Uses MSSQL-specific EXEC syntax and output parameter handling.
 */
export async function executeStoredProcedure(
  procName: string,
  params: Record<string, { type: sql.ISqlTypeFactory; value: unknown }> = {}
) {
  const pool = await getPool();
  const request = pool.request();

  for (const [name, { type, value }] of Object.entries(params)) {
    request.input(name, type, value);
  }

  return request.execute(procName);
}

/**
 * Get temporal history for a record in a system-versioned table.
 * Uses MSSQL-specific FOR SYSTEM_TIME syntax.
 */
export async function getTemporalHistory(
  schema: string,
  tableName: string,
  pkColumn: string,
  pkValue: number
) {
  const pool = await getPool();
  const result = await pool.request()
    .input('pkValue', sql.Int, pkValue)
    .query(`
      SELECT *,
        [ValidFrom],
        [ValidTo],
        IIF([ValidTo] = '9999-12-31 23:59:59.9999999', 'Current', 'Historical') AS RecordStatus
      FROM [${schema}].[${tableName}]
      FOR SYSTEM_TIME ALL
      WHERE [${pkColumn}] = @pkValue
      ORDER BY [ValidFrom] DESC
    `);
  return result.recordset;
}

/**
 * Full-text search using MSSQL FREETEXTTABLE.
 */
export async function fullTextSearch(
  searchTerm: string,
  maxResults: number = 20
) {
  const pool = await getPool();
  const result = await pool.request()
    .input('searchTerm', sql.NVarChar(200), searchTerm)
    .input('maxResults', sql.Int, maxResults)
    .query(`
      SELECT TOP (@maxResults)
        si.[StockItemID],
        si.[StockItemName],
        ft.[RANK] AS SearchRank
      FROM [Warehouse].[StockItems] si
      INNER JOIN FREETEXTTABLE([Warehouse].[StockItems], [SearchDetails], @searchTerm, @maxResults) ft
        ON si.[StockItemID] = ft.[KEY]
      ORDER BY ft.[RANK] DESC
    `);
  return result.recordset;
}
