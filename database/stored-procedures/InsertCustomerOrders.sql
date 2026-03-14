-- Translated from MSSQL to PostgreSQL by MigrateIQ

CREATE OR REPLACE PROCEDURE website.insert_customer_orders(
    p_orders website.order_list[],
    p_order_lines website.order_line_list[],
    p_orders_created_by_person_id INT,
    p_salesperson_person_id INT
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    -- Create a temporary table to hold orders to generate
    CREATE TEMP TABLE orders_to_generate (
        order_reference INT PRIMARY KEY,   -- reference from the application
        order_id INT
    ) ON COMMIT DROP;

    -- allocate the new order numbers
    INSERT INTO orders_to_generate (order_reference, order_id)
    SELECT o.order_reference, nextval('sequences.order_id')
    FROM unnest(p_orders) AS o;

    BEGIN
        INSERT INTO sales.orders
            (order_id, customer_id, salesperson_person_id, picked_by_person_id, contact_person_id, backorder_order_id, order_date,
             expected_delivery_date, customer_purchase_order_number, is_undersupply_backordered, comments, delivery_instructions, internal_comments,
             picking_completed_when, last_edited_by, last_edited_when)
        SELECT otg.order_id, o.customer_id, p_salesperson_person_id, NULL, o.contact_person_id, NULL, NOW(),
               o.expected_delivery_date, o.customer_purchase_order_number, o.is_undersupply_backordered, o.comments, o.delivery_instructions, NULL,
               NULL, p_orders_created_by_person_id, NOW()
        FROM orders_to_generate AS otg
        INNER JOIN unnest(p_orders) AS o
        ON otg.order_reference = o.order_reference;

        INSERT INTO sales.order_lines
            (order_id, stock_item_id, description, package_type_id, quantity, unit_price,
             tax_rate, picked_quantity, picking_completed_when, last_edited_by, last_edited_when)
        SELECT otg.order_id, ol.stock_item_id, ol.description, si.unit_package_id, ol.quantity,
               website.calculate_customer_price(o.customer_id, ol.stock_item_id, NOW()),
               si.tax_rate, 0, NULL, p_orders_created_by_person_id, NOW()
        FROM orders_to_generate AS otg
        INNER JOIN unnest(p_order_lines) AS ol
        ON otg.order_reference = ol.order_reference
        INNER JOIN unnest(p_orders) AS o
        ON ol.order_reference = o.order_reference
        INNER JOIN warehouse.stock_items AS si
        ON ol.stock_item_id = si.stock_item_id;

    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Unable to create the customer orders.';
        RAISE;
    END;
END;
$$;
