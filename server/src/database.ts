import sqlite3 from 'sqlite3';
import { NanostationStatus } from './types';
import path from 'path';

const DB_PATH = path.join(__dirname, '..', 'nanostation.db');

export class Database {
  private db: sqlite3.Database;

  constructor() {
    this.db = new sqlite3.Database(DB_PATH);
    this.initDatabase();
  }

  private initDatabase(): void {
    this.db.serialize(() => {
      // Tabla principal de status
      this.db.run(`
        CREATE TABLE IF NOT EXISTS nanostation_status (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          timestamp TEXT NOT NULL,
          device_id TEXT NOT NULL,
          data TEXT NOT NULL
        )
      `);

      // Índice para búsquedas rápidas
      this.db.run(`
        CREATE INDEX IF NOT EXISTS idx_timestamp 
        ON nanostation_status(timestamp DESC)
      `);

      this.db.run(`
        CREATE INDEX IF NOT EXISTS idx_device_id 
        ON nanostation_status(device_id)
      `);
    });
  }

  public saveStatus(status: NanostationStatus): Promise<void> {
    return new Promise((resolve, reject) => {
      const sql = `
        INSERT INTO nanostation_status (timestamp, device_id, data)
        VALUES (?, ?, ?)
      `;
      
      this.db.run(
        sql,
        [status.timestamp, status.deviceId, JSON.stringify(status)],
        (err) => {
          if (err) reject(err);
          else resolve();
        }
      );
    });
  }

  public getLatestStatus(): Promise<NanostationStatus | null> {
    return new Promise((resolve, reject) => {
      const sql = `
        SELECT data FROM nanostation_status
        ORDER BY timestamp DESC
        LIMIT 1
      `;
      
      this.db.get(sql, [], (err, row: any) => {
        if (err) {
          reject(err);
        } else if (row) {
          resolve(JSON.parse(row.data));
        } else {
          resolve(null);
        }
      });
    });
  }

  public getAllStatus(limit: number = 100): Promise<NanostationStatus[]> {
    return new Promise((resolve, reject) => {
      const sql = `
        SELECT data FROM nanostation_status
        ORDER BY timestamp DESC
        LIMIT ?
      `;
      
      this.db.all(sql, [limit], (err, rows: any[]) => {
        if (err) {
          reject(err);
        } else {
          const statuses = rows.map(row => JSON.parse(row.data));
          resolve(statuses);
        }
      });
    });
  }

  public getStatusByDeviceId(deviceId: string, limit: number = 50): Promise<NanostationStatus[]> {
    return new Promise((resolve, reject) => {
      const sql = `
        SELECT data FROM nanostation_status
        WHERE device_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
      `;
      
      this.db.all(sql, [deviceId, limit], (err, rows: any[]) => {
        if (err) {
          reject(err);
        } else {
          const statuses = rows.map(row => JSON.parse(row.data));
          resolve(statuses);
        }
      });
    });
  }

  public close(): void {
    this.db.close();
  }
}

export const db = new Database();
