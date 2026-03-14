-- Translated from MSSQL to PostgreSQL by MigrateIQ

CREATE OR REPLACE FUNCTION website.calculate_customer_price(
    p_customer_id int,
    p_stock_item_id int,
    p_pricing_date date
)
RETURNS decimal(18,2)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_calculated_price decimal(18,2);
    v_unit_price decimal(18,2);
    v_lowest_unit_price decimal(18,2);
    v_highest_discount_amount decimal(18,2);
    v_highest_discount_percentage decimal(18,3);
    v_buying_group_id int;
    v_customer_category_id int;
    v_discounted_unit_price decimal(18,2);
BEGIN
    SELECT buying_group_id, customer_category_id
    INTO v_buying_group_id, v_customer_category_id
    FROM sales.customers
    WHERE customer_id = p_customer_id;

    SELECT si.unit_price
    INTO v_unit_price
    FROM warehouse.stock_items AS si
    WHERE si.stock_item_id = p_stock_item_id;

    v_calculated_price := v_unit_price;

    SELECT MIN(sd.unit_price)
    INTO v_lowest_unit_price
    FROM sales.special_deals AS sd
    WHERE ((sd.stock_item_id = p_stock_item_id) OR (sd.stock_item_id IS NULL))
    AND ((sd.customer_id = p_customer_id) OR (sd.customer_id IS NULL))
    AND ((sd.buying_group_id = v_buying_group_id) OR (sd.buying_group_id IS NULL))
    AND ((sd.customer_category_id = v_customer_category_id) OR (sd.customer_category_id IS NULL))
    AND ((sd.stock_group_id IS NULL) OR EXISTS (SELECT 1 FROM warehouse.stock_item_stock_groups AS sisg
                                                         WHERE sisg.stock_item_id = p_stock_item_id
                                                         AND sisg.stock_group_id = sd.stock_group_id))
    AND sd.unit_price IS NOT NULL
    AND p_pricing_date BETWEEN sd.start_date AND sd.end_date;

    IF v_lowest_unit_price IS NOT NULL AND v_lowest_unit_price < v_unit_price THEN
        v_calculated_price := v_lowest_unit_price;
    END IF;

    SELECT MAX(sd.discount_amount)
    INTO v_highest_discount_amount
    FROM sales.special_deals AS sd
    WHERE ((sd.stock_item_id = p_stock_item_id) OR (sd.stock_item_id IS NULL))
    AND ((sd.customer_id = p_customer_id) OR (sd.customer_id IS NULL))
    AND ((sd.buying_group_id = v_buying_group_id) OR (sd.buying_group_id IS NULL))
    AND ((sd.customer_category_id = v_customer_category_id) OR (sd.customer_category_id IS NULL))
    AND ((sd.stock_group_id IS NULL) OR EXISTS (SELECT 1 FROM warehouse.stock_item_stock_groups AS sisg
                                                         WHERE sisg.stock_item_id = p_stock_item_id
                                                         AND sisg.stock_group_id = sd.stock_group_id))
    AND sd.discount_amount IS NOT NULL
    AND p_pricing_date BETWEEN sd.start_date AND sd.end_date;

    IF v_highest_discount_amount IS NOT NULL AND (v_unit_price - v_highest_discount_amount) < v_calculated_price THEN
        v_calculated_price := v_unit_price - v_highest_discount_amount;
    END IF;

    SELECT MAX(sd.discount_percentage)
    INTO v_highest_discount_percentage
    FROM sales.special_deals AS sd
    WHERE ((sd.stock_item_id = p_stock_item_id) OR (sd.stock_item_id IS NULL))
    AND ((sd.customer_id = p_customer_id) OR (sd.customer_id IS NULL))
    AND ((sd.buying_group_id = v_buying_group_id) OR (sd.buying_group_id IS NULL))
    AND ((sd.customer_category_id = v_customer_category_id) OR (sd.customer_category_id IS NULL))
    AND ((sd.stock_group_id IS NULL) OR EXISTS (SELECT 1 FROM warehouse.stock_item_stock_groups AS sisg
                                                         WHERE sisg.stock_item_id = p_stock_item_id
                                                         AND sisg.stock_group_id = sd.stock_group_id))
    AND sd.discount_percentage IS NOT NULL
    AND p_pricing_date BETWEEN sd.start_date AND sd.end_date;

    IF v_highest_discount_percentage IS NOT NULL THEN
        v_discounted_unit_price := ROUND(v_unit_price * v_highest_discount_percentage / 100.0, 2);
        IF v_discounted_unit_price < v_calculated_price THEN
            v_calculated_price := v_discounted_unit_price;
        END IF;
    END IF;

    RETURN v_calculated_price;
END;
$$;
