-- Translated from MSSQL to PostgreSQL by MigrateIQ

-- TEMPORAL TABLE NOTE: MSSQL uses native system-versioned temporal tables.
-- PostgreSQL approach: Use temporal_tables extension or implement via triggers.
-- The ValidFrom/ValidTo columns are preserved for manual temporal implementation.
-- Original history table: Warehouse.StockItems_Archive

CREATE TABLE warehouse.stock_items (
    stock_item_id            INT             NOT NULL DEFAULT nextval('sequences.stockitemid'),
    stock_item_name          VARCHAR(100)    NOT NULL,
    supplier_id              INT             NOT NULL,
    color_id                 INT             NULL,
    unit_package_id          INT             NOT NULL,
    outer_package_id         INT             NOT NULL,
    brand                    VARCHAR(50)     NULL,
    size                     VARCHAR(20)     NULL,
    lead_time_days           INT             NOT NULL,
    quantity_per_outer       INT             NOT NULL,
    is_chiller_stock         BOOLEAN         NOT NULL,
    barcode                  VARCHAR(50)     NULL,
    tax_rate                 DECIMAL(18, 3)  NOT NULL,
    unit_price               DECIMAL(18, 2)  NOT NULL,
    recommended_retail_price DECIMAL(18, 2)  NULL,
    typical_weight_per_unit  DECIMAL(18, 3)  NOT NULL,
    marketing_comments       TEXT            NULL,
    internal_comments        TEXT            NULL,
    photo                    BYTEA           NULL,
    custom_fields            TEXT            NULL,
    -- NOTE: Tags was a computed column using json_query(CustomFields, '$.Tags').
    -- In PostgreSQL, use a view or application logic: (custom_fields::jsonb -> 'Tags')
    search_details           TEXT            GENERATED ALWAYS AS (concat(stock_item_name, ' ', marketing_comments)) STORED,
    last_edited_by           INT             NOT NULL,
    valid_from               TIMESTAMP       NOT NULL DEFAULT now(),
    valid_to                 TIMESTAMP       NOT NULL DEFAULT '9999-12-31 23:59:59.9999999',
    CONSTRAINT pk_warehouse_stockitems PRIMARY KEY (stock_item_id),
    CONSTRAINT fk_warehouse_stockitems_application_people FOREIGN KEY (last_edited_by) REFERENCES application.people (person_id),
    CONSTRAINT fk_warehouse_stockitems_colorid_warehouse_colors FOREIGN KEY (color_id) REFERENCES warehouse.colors (color_id),
    CONSTRAINT fk_warehouse_stockitems_outerpackageid_warehouse_packagetypes FOREIGN KEY (outer_package_id) REFERENCES warehouse.package_types (package_type_id),
    CONSTRAINT fk_warehouse_stockitems_supplierid_purchasing_suppliers FOREIGN KEY (supplier_id) REFERENCES purchasing.suppliers (supplier_id),
    CONSTRAINT fk_warehouse_stockitems_unitpackageid_warehouse_packagetypes FOREIGN KEY (unit_package_id) REFERENCES warehouse.package_types (package_type_id),
    CONSTRAINT uq_warehouse_stockitems_stockitemname UNIQUE (stock_item_name)
);

CREATE INDEX fk_warehouse_stockitems_supplierid
    ON warehouse.stock_items (supplier_id);

CREATE INDEX fk_warehouse_stockitems_colorid
    ON warehouse.stock_items (color_id);

CREATE INDEX fk_warehouse_stockitems_unitpackageid
    ON warehouse.stock_items (unit_package_id);

CREATE INDEX fk_warehouse_stockitems_outerpackageid
    ON warehouse.stock_items (outer_package_id);

COMMENT ON INDEX fk_warehouse_stockitems_supplierid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX fk_warehouse_stockitems_colorid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX fk_warehouse_stockitems_unitpackageid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX fk_warehouse_stockitems_outerpackageid IS 'Auto-created to support a foreign key';

COMMENT ON TABLE warehouse.stock_items IS 'Main entity table for stock items';
COMMENT ON COLUMN warehouse.stock_items.stock_item_id IS 'Numeric ID used for reference to a stock item within the database';
COMMENT ON COLUMN warehouse.stock_items.stock_item_name IS 'Full name of a stock item (but not a full description)';
COMMENT ON COLUMN warehouse.stock_items.supplier_id IS 'Usual supplier for this stock item';
COMMENT ON COLUMN warehouse.stock_items.color_id IS 'Color (optional) for this stock item';
COMMENT ON COLUMN warehouse.stock_items.unit_package_id IS 'Usual package for selling units of this stock item';
COMMENT ON COLUMN warehouse.stock_items.outer_package_id IS 'Usual package for selling outers of this stock item (ie cartons, boxes, etc.)';
COMMENT ON COLUMN warehouse.stock_items.brand IS 'Brand for the stock item (if the item is branded)';
COMMENT ON COLUMN warehouse.stock_items.size IS 'Size of this item (eg: 100mm)';
COMMENT ON COLUMN warehouse.stock_items.lead_time_days IS 'Number of days typically taken from order to receipt of this stock item';
COMMENT ON COLUMN warehouse.stock_items.quantity_per_outer IS 'Quantity of the stock item in an outer package';
COMMENT ON COLUMN warehouse.stock_items.is_chiller_stock IS 'Does this stock item need to be in a chiller?';
COMMENT ON COLUMN warehouse.stock_items.barcode IS 'Barcode for this stock item';
COMMENT ON COLUMN warehouse.stock_items.tax_rate IS 'Tax rate to be applied';
COMMENT ON COLUMN warehouse.stock_items.unit_price IS 'Selling price (ex-tax) for one unit of this product';
COMMENT ON COLUMN warehouse.stock_items.recommended_retail_price IS 'Recommended retail price for this stock item';
COMMENT ON COLUMN warehouse.stock_items.typical_weight_per_unit IS 'Typical weight for one unit of this product (packaged)';
COMMENT ON COLUMN warehouse.stock_items.marketing_comments IS 'Marketing comments for this stock item (shared outside the organization)';
COMMENT ON COLUMN warehouse.stock_items.internal_comments IS 'Internal comments (not exposed outside organization)';
COMMENT ON COLUMN warehouse.stock_items.photo IS 'Photo of the product';
COMMENT ON COLUMN warehouse.stock_items.custom_fields IS 'Custom fields added by system users';
COMMENT ON COLUMN warehouse.stock_items.search_details IS 'Combination of columns used by full text search';
