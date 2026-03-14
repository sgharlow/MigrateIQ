import { getPool, sql } from '../config/database.config';

export async function getTopCustomers(limit: number = 10) {
  const pool = await getPool();
  const result = await pool.request()
    .input('limit', sql.Int, limit)
    .query(`
      SELECT TOP (@limit)
        c.[CustomerID],
        c.[CustomerName],
        ISNULL(c.[PhoneNumber], 'N/A') AS PhoneNumber,
        c.[DeliveryAddressLine1] + ', ' + c.[DeliveryCity] AS FullAddress,
        COUNT(o.[OrderID]) AS OrderCount,
        CONVERT(VARCHAR, SUM(ol.[Quantity] * ol.[UnitPrice]), 1) AS TotalSpent
      FROM [Sales].[Customers] c
      LEFT JOIN [Sales].[Orders] o ON c.[CustomerID] = o.[CustomerID]
      LEFT JOIN [Sales].[OrderLines] ol ON o.[OrderID] = ol.[OrderID]
      WHERE c.[ValidTo] > GETDATE()
      GROUP BY c.[CustomerID], c.[CustomerName], c.[PhoneNumber],
               c.[DeliveryAddressLine1], c.[DeliveryCity]
      ORDER BY SUM(ol.[Quantity] * ol.[UnitPrice]) DESC
    `);
  return result.recordset;
}

export async function getCustomerOrderHistory(customerId: number) {
  const pool = await getPool();
  const result = await pool.request()
    .input('customerId', sql.Int, customerId)
    .query(`
      SELECT TOP 50
        o.[OrderID],
        o.[OrderDate],
        o.[ExpectedDeliveryDate],
        DATEDIFF(DAY, o.[OrderDate], o.[ExpectedDeliveryDate]) AS LeadDays,
        (SELECT COUNT(*) FROM [Sales].[OrderLines] ol WHERE ol.[OrderID] = o.[OrderID]) AS LineCount,
        IIF(o.[IsUndersupplyBackordered] = 1, 'Yes', 'No') AS IsBackordered
      FROM [Sales].[Orders] o
      WHERE o.[CustomerID] = @customerId
      ORDER BY o.[OrderDate] DESC
    `);
  return result.recordset;
}

export async function searchCustomersByTerritory(territory: string) {
  const pool = await getPool();
  const result = await pool.request()
    .input('territory', sql.NVarChar(50), territory)
    .query(`
      SELECT
        c.[CustomerID],
        c.[CustomerName],
        c.[DeliveryLocation].STAsText() AS LocationWKT,
        c.[DeliveryLocation].Lat AS Latitude,
        c.[DeliveryLocation].Long AS Longitude
      FROM [Sales].[Customers] c
      CROSS APPLY (
        SELECT [DeliveryMethodName]
        FROM [Application].[DeliveryMethods] dm
        WHERE dm.[DeliveryMethodID] = c.[DeliveryMethodID]
      ) delivery
      WHERE c.[DeliveryCityID] IN (
        SELECT [CityID] FROM [Application].[Cities]
        WHERE [StateProvinceID] IN (
          SELECT [StateProvinceID] FROM [Application].[StateProvinces]
          WHERE [SalesTerritory] = @territory
        )
      )
    `);
  return result.recordset;
}
