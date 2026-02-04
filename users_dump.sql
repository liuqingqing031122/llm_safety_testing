PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email VARCHAR UNIQUE NOT NULL,
                name VARCHAR NOT NULL,
                hashed_password VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
INSERT INTO users VALUES(1,'liuqingqing0312@outlook.com','test1','$2b$12$Z3zTDSBiGeTrUGR2MPgUzurF7YewyREFb2foo9UHdnL3S/lBLOnoq','2026-01-30 16:10:05');
INSERT INTO users VALUES(2,'liuqingqing0313@outlook.com','test2','$2b$12$XbQtJsE3nPKG/pa2cLnA3O9Ah/jBnYyFiv/hK2BOiAsdC5d4ni7Mq','2026-02-02 16:23:45');
INSERT INTO users VALUES(3,'liuqingqing0314@outlook.com','test3','$2b$12$jTVaJeMCgWkjZoU4zqZQUeWMFBrCJtNHSuwHP.HVPJgSxzN3NXc5e','2026-02-02 16:27:09');
COMMIT;
