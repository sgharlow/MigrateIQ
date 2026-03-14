// Translated from MSSQL to PostgreSQL by MigrateIQ

import { getPool } from '../config/database.config';

export async function getTopCustomers(limit: number = 10) {
  const pool = await getPool();
  const result = await pool.query(
    `
      SELECT
        c.customer_id,
        c.customer_name,
        COALESCE(c.phone_number, 'N/A') AS phone_number,
        c.delivery_address_line1 || ', ' || c.delivery_city AS full_address,
        COUNT(o.order_id) AS order_count,
        TO_CHAR(SUM(ol.quantity * ol.unit_price), 'FM999,999,999.00') AS total_spent
      FROM sales.customers c
      LEFT JOIN sales.orders o ON c.customer_id = o.customer_id
      LEFT JOIN sales.order_lines ol ON o.order_id = ol.order_id
      WHERE c.valid_to > NOW()
      GROUP BY c.customer_id, c.customer_name, c.phone_number,
               c.delivery_address_line1, c.delivery_city
      ORDER BY SUM(ol.quantity * ol.unit_price) DESC
      LIMIT $1
    `,
    [limit]
  );
  return result.rows;
}

export async function getCustomerOrderHistory(customerId: number) {
  const pool = await getPool();
  const result = await pool.query(
    `
      SELECT
        o.order_id,
        o.order_date,
        o.expected_delivery_date,
        (o.expected_delivery_date::date - o.order_date::date) AS lead_days,
        (SELECT COUNT(*) FROM sales.order_lines ol WHERE ol.order_id = o.order_id) AS line_count,
        CASE WHEN o.is_undersupply_backordered = 1 THEN 'Yes' ELSE 'No' END AS is_backordered
      FROM sales.orders o
      WHERE o.customer_id = $1
      ORDER BY o.order_date DESC
      LIMIT 50
    `,
    [customerId]
  );
  return result.rows;
}

export async function searchCustomersByTerritory(territory: string) {
  const pool = await getPool();
  const result = await pool.query(
    `
      SELECT
        c.customer_id,
        c.customer_name,
        ST_AsText(c.delivery_location) AS location_wkt,
        ST_Y(c.delivery_location) AS latitude,
        ST_X(c.delivery_location) AS longitude
      FROM sales.customers c
      CROSS JOIN LATERAL (
        SELECT dm.delivery_method_name
        FROM application.delivery_methods dm
        WHERE dm.delivery_method_id = c.delivery_method_id
      ) delivery
      WHERE c.delivery_city_id IN (
        SELECT city_id FROM application.cities
        WHERE state_province_id IN (
          SELECT state_province_id FROM application.state_provinces
          WHERE sales_territory = $1
        )
      )
    `,
    [territory]
  );
  return result.rows;
}
