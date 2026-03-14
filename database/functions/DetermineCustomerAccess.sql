-- Translated from MSSQL to PostgreSQL by MigrateIQ

CREATE OR REPLACE FUNCTION application.determine_customer_access(p_city_id int)
RETURNS TABLE(access_result int)
LANGUAGE sql
AS $$
    SELECT 1 AS access_result
    WHERE pg_has_role(current_user, 'db_owner', 'MEMBER')
    OR pg_has_role(current_user,
        (SELECT sp.sales_territory
         FROM application.cities AS c
         INNER JOIN application.state_provinces AS sp
         ON c.state_province_id = sp.state_province_id
         WHERE c.city_id = p_city_id) || ' Sales',
        'MEMBER')
    OR ((session_user = 'Website' OR session_user = 'WebApi')
        AND EXISTS (SELECT 1
                    FROM application.cities AS c
                    INNER JOIN application.state_provinces AS sp
                    ON c.state_province_id = sp.state_province_id
                    WHERE c.city_id = p_city_id
                    AND sp.sales_territory = current_setting('app.SalesTerritory')));
$$;
