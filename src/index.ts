/**
 * WideWorldImporters Sample Application
 *
 * This is a demo application showcasing Microsoft SQL Server (T-SQL) code
 * for the MigrateIQ database migration hackathon project.
 *
 * See database/ for SQL objects and src/queries/ for data access code.
 */

export { getPool, closePool } from './config/database.config';
export { getTopCustomers, getCustomerOrderHistory, searchCustomersByTerritory } from './queries/customers';
export { searchStockItems, getStockItemsAsJson, getLowStockItems } from './queries/stock-items';
export { executeStoredProcedure, getTemporalHistory, fullTextSearch } from './utils/sql-helpers';
