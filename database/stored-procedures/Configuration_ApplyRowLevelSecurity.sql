-- Translated from MSSQL to PostgreSQL by MigrateIQ

CREATE OR REPLACE PROCEDURE application.configuration_apply_row_level_security()
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    dynamic_sql TEXT;
BEGIN
    BEGIN
        -- Drop existing policy if it exists
        dynamic_sql := 'DROP POLICY IF EXISTS filter_customers_by_sales_territory_role ON sales.customers';
        EXECUTE dynamic_sql;

        -- Drop existing function if it exists
        dynamic_sql := 'DROP FUNCTION IF EXISTS application.determine_customer_access(INT)';
        EXECUTE dynamic_sql;

        -- Create the row-level security function
        dynamic_sql := '
CREATE OR REPLACE FUNCTION application.determine_customer_access(city_id INT)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $func$
BEGIN
    RETURN (
        pg_has_role(current_user, ''db_owner'', ''MEMBER'')
        OR pg_has_role(current_user,
            (SELECT sp.sales_territory
             FROM application.cities AS c
             INNER JOIN application.state_provinces AS sp
                 ON c.state_province_id = sp.state_province_id
             WHERE c.city_id = city_id) || '' Sales'',
            ''MEMBER'')
        OR (session_user IN (''Website'', ''WebApi'')
            AND EXISTS (SELECT 1
                        FROM application.cities AS c
                        INNER JOIN application.state_provinces AS sp
                            ON c.state_province_id = sp.state_province_id
                        WHERE c.city_id = determine_customer_access.city_id
                        AND sp.sales_territory = current_setting(''app.SalesTerritory'')))
    );
END;
$func$';
        EXECUTE dynamic_sql;

        -- Enable RLS on the table
        dynamic_sql := 'ALTER TABLE sales.customers ENABLE ROW LEVEL SECURITY';
        EXECUTE dynamic_sql;

        -- Create the filter policy
        dynamic_sql := '
CREATE POLICY filter_customers_by_sales_territory_role
    ON sales.customers
    USING (application.determine_customer_access(delivery_city_id))
    WITH CHECK (application.determine_customer_access(delivery_city_id))';
        EXECUTE dynamic_sql;

        RAISE NOTICE 'Successfully applied row level security';

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Unable to apply row level security';
        RAISE NOTICE '%', SQLERRM;
        RAISE EXCEPTION 'Unable to apply row level security';
    END;
END;
$$;
