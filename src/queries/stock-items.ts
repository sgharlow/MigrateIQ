import { getPool, sql } from '../config/database.config';

export async function searchStockItems(searchText: string, maxResults: number = 20) {
  const pool = await getPool();
  const result = await pool.request()
    .input('searchText', sql.NVarChar(100), searchText)
    .input('maxResults', sql.Int, maxResults)
    .query(`
      SELECT TOP (@maxResults)
        si.[StockItemID],
        si.[StockItemName],
        si.[UnitPrice],
        si.[RecommendedRetailPrice],
        si.[RecommendedRetailPrice] - si.[UnitPrice] AS Margin,
        ISNULL(si.[MarketingComments], '') AS MarketingComments,
        JSON_QUERY(si.[CustomFields], '$.Tags') AS Tags,
        JSON_VALUE(si.[CustomFields], '$.CountryOfManufacture') AS CountryOfManufacture
      FROM [Warehouse].[StockItems] si
      WHERE si.[StockItemName] LIKE '%' + @searchText + '%'
         OR si.[MarketingComments] LIKE '%' + @searchText + '%'
      ORDER BY si.[StockItemName]
    `);
  return result.recordset;
}

export async function getStockItemsAsJson(tagFilter: string) {
  const pool = await getPool();
  const result = await pool.request()
    .input('tag', sql.NVarChar(100), tagFilter)
    .query(`
      SELECT
        si.[StockItemID],
        si.[StockItemName],
        si.[UnitPrice],
        JSON_QUERY(si.[CustomFields], '$.Tags') AS Tags
      FROM [Warehouse].[StockItems] si
      WHERE EXISTS (
        SELECT 1
        FROM OPENJSON(JSON_QUERY(si.[CustomFields], '$.Tags'))
        WHERE [value] = @tag
      )
      FOR JSON AUTO, ROOT('StockItems')
    `);
  return result.recordset[0];
}

export async function getLowStockItems(threshold: number = 10) {
  const pool = await getPool();
  const result = await pool.request()
    .input('threshold', sql.Int, threshold)
    .query(`
      SELECT TOP 25
        si.[StockItemName],
        sih.[QuantityOnHand],
        sih.[LastCostPrice],
        CONVERT(VARCHAR, sih.[LastCostPrice] * sih.[QuantityOnHand], 1) AS StockValue,
        sih.[LastStocktakeQuantity],
        IIF(sih.[QuantityOnHand] < @threshold, 'CRITICAL', 'LOW') AS AlertLevel
      FROM [Warehouse].[StockItemHoldings] sih
      JOIN [Warehouse].[StockItems] si ON sih.[StockItemID] = si.[StockItemID]
      WHERE sih.[QuantityOnHand] < @threshold * 2
      ORDER BY sih.[QuantityOnHand] ASC
    `);
  return result.recordset;
}
