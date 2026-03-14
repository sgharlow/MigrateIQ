// Translated from MSSQL to PostgreSQL by MigrateIQ

import { getPool } from '../config/database.config';

export async function searchStockItems(searchText: string, maxResults: number = 20) {
  const pool = await getPool();
  const result = await pool.query(
    `
      SELECT
        si.stock_item_id,
        si.stock_item_name,
        si.unit_price,
        si.recommended_retail_price,
        si.recommended_retail_price - si.unit_price AS margin,
        COALESCE(si.marketing_comments, '') AS marketing_comments,
        si.custom_fields::jsonb #> '{Tags}' AS tags,
        si.custom_fields::jsonb #>> '{CountryOfManufacture}' AS country_of_manufacture
      FROM warehouse.stock_items si
      WHERE si.stock_item_name LIKE '%' || $1 || '%'
         OR si.marketing_comments LIKE '%' || $1 || '%'
      ORDER BY si.stock_item_name
      LIMIT $2
    `,
    [searchText, maxResults]
  );
  return result.rows;
}

export async function getStockItemsAsJson(tagFilter: string) {
  const pool = await getPool();
  const result = await pool.query(
    `
      SELECT json_build_object(
        'StockItems', json_agg(row_to_json(subq))
      ) AS result
      FROM (
        SELECT
          si.stock_item_id,
          si.stock_item_name,
          si.unit_price,
          si.custom_fields::jsonb #> '{Tags}' AS tags
        FROM warehouse.stock_items si
        WHERE EXISTS (
          SELECT 1
          FROM jsonb_array_elements_text(si.custom_fields::jsonb #> '{Tags}') AS tag_value
          WHERE tag_value = $1
        )
      ) subq
    `,
    [tagFilter]
  );
  return result.rows[0];
}

export async function getLowStockItems(threshold: number = 10) {
  const pool = await getPool();
  const result = await pool.query(
    `
      SELECT
        si.stock_item_name,
        sih.quantity_on_hand,
        sih.last_cost_price,
        TO_CHAR(sih.last_cost_price * sih.quantity_on_hand, 'FM999,999,999.00') AS stock_value,
        sih.last_stocktake_quantity,
        CASE WHEN sih.quantity_on_hand < $1 THEN 'CRITICAL' ELSE 'LOW' END AS alert_level
      FROM warehouse.stock_item_holdings sih
      JOIN warehouse.stock_items si ON sih.stock_item_id = si.stock_item_id
      WHERE sih.quantity_on_hand < $1 * 2
      ORDER BY sih.quantity_on_hand ASC
      LIMIT 25
    `,
    [threshold]
  );
  return result.rows;
}
