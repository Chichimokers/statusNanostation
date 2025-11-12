import express, { Request, Response } from 'express';
import bodyParser from 'body-parser';
import cors from 'cors';
import { engine } from 'express-handlebars';
import path from 'path';
import { db } from './database';
import { NanostationStatus } from './types';

const app = express();
const PORT = process.env.PORT || 5000;

// Configurar Handlebars
app.engine('handlebars', engine({
  defaultLayout: 'main',
  layoutsDir: path.join(__dirname, '../views/layouts'),
  partialsDir: path.join(__dirname, '../views/partials'),
  helpers: {
    json: (context: any) => JSON.stringify(context),
    formatDate: (timestamp: string) => {
      return new Date(timestamp).toLocaleString('es-ES');
    },
    formatBytes: (bytes: number) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    },
    formatUptime: (seconds: number) => {
      const days = Math.floor(seconds / 86400);
      const hours = Math.floor((seconds % 86400) / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${days}d ${hours}h ${minutes}m`;
    },
    eq: (a: any, b: any) => a === b,
    gt: (a: number, b: number) => a > b,
    lt: (a: number, b: number) => a < b,
    signalQuality: (rssi: number) => {
      if (rssi >= -50) return 'Excelente';
      if (rssi >= -60) return 'Muy Buena';
      if (rssi >= -70) return 'Buena';
      if (rssi >= -80) return 'Regular';
      return 'Mala';
    },
    signalClass: (rssi: number) => {
      if (rssi >= -50) return 'excellent';
      if (rssi >= -60) return 'very-good';
      if (rssi >= -70) return 'good';
      if (rssi >= -80) return 'fair';
      return 'poor';
    }
  }
}));

app.set('view engine', 'handlebars');
app.set('views', path.join(__dirname, '../views'));

// Middleware
app.use(cors());
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, '../public')));

// Ruta principal - Dashboard
app.get('/', async (req: Request, res: Response) => {
  try {
    const status = await db.getLatestStatus();
    
    if (!status) {
      return res.render('home', {
        title: 'Nanostation M5 Monitor',
        noData: true,
        message: 'No hay datos disponibles. Esperando información del cliente...'
      });
    }

    res.render('home', {
      title: 'Nanostation M5 Monitor',
      status: status,
      hasData: true
    });
  } catch (error) {
    console.error('Error al obtener datos:', error);
    res.status(500).render('error', {
      title: 'Error',
      message: 'Error al cargar los datos'
    });
  }
});

// Endpoint API para recibir información del cliente
app.post('/api/info', async (req: Request, res: Response) => {
  try {
    const status: NanostationStatus = req.body;
    
    // Validar que tenga la estructura básica
    if (!status.timestamp || !status.deviceId || !status.system) {
      return res.status(400).json({
        success: false,
        error: 'Datos incompletos'
      });
    }

    // Guardar en base de datos
    await db.saveStatus(status);
    
    console.log(`✓ Status recibido del dispositivo ${status.deviceId} a las ${status.timestamp}`);
    
    res.json({
      success: true,
      message: 'Datos guardados correctamente'
    });
  } catch (error) {
    console.error('Error al guardar datos:', error);
    res.status(500).json({
      success: false,
      error: 'Error al guardar los datos'
    });
  }
});

// Endpoint API para obtener el último status
app.get('/api/status', async (req: Request, res: Response) => {
  try {
    const status = await db.getLatestStatus();
    
    if (!status) {
      return res.status(404).json({
        success: false,
        error: 'No hay datos disponibles'
      });
    }

    res.json({
      success: true,
      data: status
    });
  } catch (error) {
    console.error('Error al obtener datos:', error);
    res.status(500).json({
      success: false,
      error: 'Error al obtener los datos'
    });
  }
});

// Endpoint API para obtener historial
app.get('/api/history', async (req: Request, res: Response) => {
  try {
    const limit = parseInt(req.query.limit as string) || 100;
    const history = await db.getAllStatus(limit);
    
    res.json({
      success: true,
      data: history,
      count: history.length
    });
  } catch (error) {
    console.error('Error al obtener historial:', error);
    res.status(500).json({
      success: false,
      error: 'Error al obtener el historial'
    });
  }
});

// Iniciar servidor
app.listen(PORT, () => {
  console.log(`🚀 Servidor iniciado en http://localhost:${PORT}`);
  console.log(`📡 Endpoint para recibir datos: POST http://localhost:${PORT}/api/info`);
  console.log(`🌐 Dashboard disponible en: http://localhost:${PORT}/`);
});

// Manejo de cierre graceful
process.on('SIGINT', () => {
  console.log('\n🛑 Cerrando servidor...');
  db.close();
  process.exit(0);
});
