-- Run once on a developer SQL Server; use a dedicated database.
CREATE DATABASE retail;
GO
ALTER DATABASE retail SET ALLOW_SNAPSHOT_ISOLATION ON;
GO
USE retail;
GO
-- The seed adapter creates retail_source and the four source tables.
-- Prefer a dedicated least-privilege login rather than sa for ongoing use.
