-- Translated from MSSQL to PostgreSQL by MigrateIQ

CREATE OR REPLACE PROCEDURE website.search_for_stock_items_by_tags(
    search_text TEXT,
    maximum_rows_to_return INT,
    INOUT result_json JSON DEFAULT NULL
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    SELECT json_build_object(
        'StockItems',
        json_agg(row_to_json(t))
    ) INTO result_json
    FROM (
        SELECT si.stock_item_id AS "StockItemID",
               si.stock_item_name AS "StockItemName"
        FROM warehouse.stock_items AS si
        WHERE si.tags LIKE '%' || search_text || '%'
        ORDER BY si.stock_item_name
        LIMIT maximum_rows_to_return
    ) t;
END;
$$;
