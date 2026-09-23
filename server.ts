import express, { Request, Response } from 'express';
import path from 'path';
import fs from 'fs';
import http from 'http';
import { spawn, ChildProcess } from 'child_process';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const PORT = Number(process.env.PORT) || 3000;
const PYTHON_PORT = 5001;

app.use(express.json());

// Spawn Flask server on port 5001
let pythonProcess: ChildProcess | null = null;
let isPythonReady = false;

function startPythonBackend() {
  console.log('[Node-Bridge] Starting Python Flask backend on port ' + PYTHON_PORT + '...');
  pythonProcess = spawn('python3', ['app.py'], {
    env: {
      ...process.env,
      PORT: String(PYTHON_PORT),
      PYTHONUNBUFFERED: '1'
    }
  });

  pythonProcess.stdout?.on('data', (data) => {
    const msg = data.toString();
    process.stdout.write(`[Flask stdout] ${msg}`);
    if (msg.includes('Running on') || msg.includes('Debugger PIN') || msg.includes('5001')) {
      isPythonReady = true;
    }
  });

  pythonProcess.stderr?.on('data', (data) => {
    const msg = data.toString();
    process.stderr.write(`[Flask stderr] ${msg}`);
    if (msg.includes('Running on') || msg.includes('5001')) {
      isPythonReady = true;
    }
  });

  pythonProcess.on('exit', (code) => {
    console.log(`[Node-Bridge] Python process exited with code ${code}. Restarting in 2s...`);
    isPythonReady = false;
    setTimeout(startPythonBackend, 2000);
  });
}

startPythonBackend();

// Static asset serving
app.use('/static', express.static(path.join(process.cwd(), 'static')));
app.use(express.static(path.join(process.cwd(), 'public')));

// Forward API requests to Python Flask backend
app.all('/api/*', (req: Request, res: Response) => {
  const options: http.RequestOptions = {
    hostname: '127.0.0.1',
    port: PYTHON_PORT,
    path: req.originalUrl,
    method: req.method,
    headers: {
      ...req.headers,
      host: `127.0.0.1:${PYTHON_PORT}`
    }
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (err) => {
    console.error('[Node-Bridge] Proxy error to Flask:', err.message);

    // Fallback if Flask is still booting
    if (req.originalUrl.startsWith('/api/products')) {
      try {
        const data = fs.readFileSync(path.join(process.cwd(), 'data', 'products.json'), 'utf-8');
        const prods = JSON.parse(data);
        return res.json({ count: prods.length, products: prods });
      } catch (e) {
        return res.status(503).json({ error: 'Backend booting up, please refresh in 2 seconds.' });
      }
    }

    res.status(503).json({
      error: 'Backend is initializing, please try again in a few moments.',
      reply: 'The AI assistant is initializing. Please wait a second and send your message again!'
    });
  });

  if (req.body && Object.keys(req.body).length > 0) {
    const bodyData = JSON.stringify(req.body);
    proxyReq.setHeader('Content-Length', Buffer.byteLength(bodyData));
    proxyReq.write(bodyData);
  }

  proxyReq.end();
});

// Root HTML route
app.get('/', (_req: Request, res: Response) => {
  const templatePath = path.join(process.cwd(), 'templates', 'index.html');
  if (fs.existsSync(templatePath)) {
    res.sendFile(templatePath);
  } else {
    res.sendFile(path.join(process.cwd(), 'index.html'));
  }
});

// Start Express server on PORT 3000
app.listen(PORT, '0.0.0.0', () => {
  console.log(`[Node-Bridge] Electronics Shopping Assistant running at http://0.0.0.0:${PORT}`);
});

process.on('SIGINT', () => {
  if (pythonProcess) pythonProcess.kill();
  process.exit(0);
});
