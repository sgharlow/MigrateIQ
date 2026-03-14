-- Translated from MSSQL to PostgreSQL by MigrateIQ

CREATE OR REPLACE PROCEDURE application.configuration_apply_full_text_indexing()
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    dynamic_sql TEXT;
BEGIN
    -- Ensure pg_trgm and unaccent extensions are available for full-text support
    CREATE EXTENSION IF NOT EXISTS pg_trgm;

    -- Create GIN full-text indexes if they do not already exist

    IF to_regclass('application.ix_people_fulltext') IS NULL THEN
        dynamic_sql := '
CREATE INDEX ix_people_fulltext
    ON application.people
    USING gin (to_tsvector(''english'', COALESCE(search_name, '''') || '' '' || COALESCE(custom_fields, '''') || '' '' || COALESCE(other_languages, '''')))';
        EXECUTE dynamic_sql;
    END IF;

    IF to_regclass('sales.ix_customers_fulltext') IS NULL THEN
        dynamic_sql := '
CREATE INDEX ix_customers_fulltext
    ON sales.customers
    USING gin (to_tsvector(''english'', COALESCE(customer_name, '''')))';
        EXECUTE dynamic_sql;
    END IF;

    IF to_regclass('purchasing.ix_suppliers_fulltext') IS NULL THEN
        dynamic_sql := '
CREATE INDEX ix_suppliers_fulltext
    ON purchasing.suppliers
    USING gin (to_tsvector(''english'', COALESCE(supplier_name, '''')))';
        EXECUTE dynamic_sql;
    END IF;

    IF to_regclass('warehouse.ix_stock_items_fulltext') IS NULL THEN
        dynamic_sql := '
CREATE INDEX ix_stock_items_fulltext
    ON warehouse.stock_items
    USING gin (to_tsvector(''english'', COALESCE(search_details, '''') || '' '' || COALESCE(custom_fields, '''') || '' '' || COALESCE(tags, '''')))';
        EXECUTE dynamic_sql;
    END IF;

    -- SearchForPeople
    dynamic_sql := 'DROP PROCEDURE IF EXISTS website.search_for_people(TEXT, INT, JSON)';
    EXECUTE dynamic_sql;

    dynamic_sql := '
CREATE OR REPLACE PROCEDURE website.search_for_people(
    search_text TEXT,
    maximum_rows_to_return INT,
    INOUT result_json JSON DEFAULT NULL
)
LANGUAGE plpgsql
AS $proc$
BEGIN
    SELECT json_build_object(
        ''People'',
        json_agg(row_to_json(t))
    ) INTO result_json
    FROM (
        SELECT p.person_id AS "PersonID",
               p.full_name AS "FullName",
               p.preferred_name AS "PreferredName",
               CASE WHEN p.is_salesperson <> 0 THEN ''Salesperson''
                    WHEN p.is_employee <> 0 THEN ''Employee''
                    WHEN c.customer_id IS NOT NULL THEN ''Customer''
                    WHEN sp.supplier_id IS NOT NULL THEN ''Supplier''
                    WHEN sa.supplier_id IS NOT NULL THEN ''Supplier''
               END AS "Relationship",
               COALESCE(c.customer_name, sp.supplier_name, sa.supplier_name, ''WWI'') AS "Company"
        FROM application.people AS p
        LEFT OUTER JOIN sales.customers AS c
            ON c.primary_contact_person_id = p.person_id
        LEFT OUTER JOIN purchasing.suppliers AS sp
            ON sp.primary_contact_person_id = p.person_id
        LEFT OUTER JOIN purchasing.suppliers AS sa
            ON sa.alternate_contact_person_id = p.person_id
        WHERE to_tsvector(''english'', p.search_name) @@ plainto_tsquery(''english'', search_text)
        ORDER BY ts_rank(to_tsvector(''english'', p.search_name), plainto_tsquery(''english'', search_text)) DESC
        LIMIT maximum_rows_to_return
    ) t;
END;
$proc$';
    EXECUTE dynamic_sql;

    -- SearchForSuppliers
    dynamic_sql := 'DROP PROCEDURE IF EXISTS website.search_for_suppliers(TEXT, INT, JSON)';
    EXECUTE dynamic_sql;

    dynamic_sql := '
CREATE OR REPLACE PROCEDURE website.search_for_suppliers(
    search_text TEXT,
    maximum_rows_to_return INT,
    INOUT result_json JSON DEFAULT NULL
)
LANGUAGE plpgsql
AS $proc$
BEGIN
    SELECT json_build_object(
        ''Suppliers'',
        json_agg(row_to_json(t))
    ) INTO result_json
    FROM (
        SELECT s.supplier_id AS "SupplierID",
               s.supplier_name AS "SupplierName",
               c.city_name AS "CityName",
               s.phone_number AS "PhoneNumber",
               s.fax_number AS "FaxNumber",
               p.full_name AS "PrimaryContactFullName",
               p.preferred_name AS "PrimaryContactPreferredName"
        FROM purchasing.suppliers AS s
        INNER JOIN application.cities AS c
            ON s.delivery_city_id = c.city_id
        LEFT OUTER JOIN application.people AS p
            ON s.primary_contact_person_id = p.person_id
        WHERE to_tsvector(''english'', s.supplier_name) @@ plainto_tsquery(''english'', search_text)
        ORDER BY ts_rank(to_tsvector(''english'', s.supplier_name), plainto_tsquery(''english'', search_text)) DESC
        LIMIT maximum_rows_to_return
    ) t;
END;
$proc$';
    EXECUTE dynamic_sql;

    -- SearchForCustomers
    dynamic_sql := 'DROP PROCEDURE IF EXISTS website.search_for_customers(TEXT, INT, JSON)';
    EXECUTE dynamic_sql;

    dynamic_sql := '
CREATE OR REPLACE PROCEDURE website.search_for_customers(
    search_text TEXT,
    maximum_rows_to_return INT,
    INOUT result_json JSON DEFAULT NULL
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $proc$
BEGIN
    SELECT json_build_object(
        ''Customers'',
        json_agg(row_to_json(t))
    ) INTO result_json
    FROM (
        SELECT c.customer_id AS "CustomerID",
               c.customer_name AS "CustomerName",
               ct.city_name AS "CityName",
               c.phone_number AS "PhoneNumber",
               c.fax_number AS "FaxNumber",
               p.full_name AS "PrimaryContactFullName",
               p.preferred_name AS "PrimaryContactPreferredName"
        FROM sales.customers AS c
        INNER JOIN application.cities AS ct
            ON c.delivery_city_id = ct.city_id
        LEFT OUTER JOIN application.people AS p
            ON c.primary_contact_person_id = p.person_id
        WHERE to_tsvector(''english'', c.customer_name) @@ plainto_tsquery(''english'', search_text)
        ORDER BY ts_rank(to_tsvector(''english'', c.customer_name), plainto_tsquery(''english'', search_text)) DESC
        LIMIT maximum_rows_to_return
    ) t;
END;
$proc$';
    EXECUTE dynamic_sql;

    -- SearchForStockItems
    dynamic_sql := 'DROP PROCEDURE IF EXISTS website.search_for_stock_items(TEXT, INT, JSON)';
    EXECUTE dynamic_sql;

    dynamic_sql := '
CREATE OR REPLACE PROCEDURE website.search_for_stock_items(
    search_text TEXT,
    maximum_rows_to_return INT,
    INOUT result_json JSON DEFAULT NULL
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $proc$
BEGIN
    SELECT json_build_object(
        ''StockItems'',
        json_agg(row_to_json(t))
    ) INTO result_json
    FROM (
        SELECT si.stock_item_id AS "StockItemID",
               si.stock_item_name AS "StockItemName"
        FROM warehouse.stock_items AS si
        WHERE to_tsvector(''english'', si.search_details) @@ plainto_tsquery(''english'', search_text)
        ORDER BY ts_rank(to_tsvector(''english'', si.search_details), plainto_tsquery(''english'', search_text)) DESC
        LIMIT maximum_rows_to_return
    ) t;
END;
$proc$';
    EXECUTE dynamic_sql;

    -- SearchForStockItemsByTags
    dynamic_sql := 'DROP PROCEDURE IF EXISTS website.search_for_stock_items_by_tags(TEXT, INT, JSON)';
    EXECUTE dynamic_sql;

    dynamic_sql := '
CREATE OR REPLACE PROCEDURE website.search_for_stock_items_by_tags(
    search_text TEXT,
    maximum_rows_to_return INT,
    INOUT result_json JSON DEFAULT NULL
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $proc$
BEGIN
    SELECT json_build_object(
        ''StockItems'',
        json_agg(row_to_json(t))
    ) INTO result_json
    FROM (
        SELECT si.stock_item_id AS "StockItemID",
               si.stock_item_name AS "StockItemName"
        FROM warehouse.stock_items AS si
        WHERE to_tsvector(''english'', si.tags) @@ plainto_tsquery(''english'', search_text)
        ORDER BY ts_rank(to_tsvector(''english'', si.tags), plainto_tsquery(''english'', search_text)) DESC
        LIMIT maximum_rows_to_return
    ) t;
END;
$proc$';
    EXECUTE dynamic_sql;

    RAISE NOTICE 'Full text successfully enabled';
END;
$$;
