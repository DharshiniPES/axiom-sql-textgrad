/**
 * AxiomSQL Enterprise Studio - Node.js Server
 * Provides REST API and serves the modern web application.
 */

const express = require('express');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const multer = require('multer');

const app = express();
const PORT = process.env.PORT || 3000;

const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const safeName = file.originalname.replace(/[^a-zA-Z0-9_.-]/g, '_');
    cb(null, `db_${Date.now()}_${safeName}`);
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 50 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if (['.sqlite', '.db', '.sql'].includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error('Only .sqlite, .db, and .sql database files are supported.'));
    }
  }
});

app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname, 'public')));

const BRIDGE_SCRIPT = path.join(__dirname, 'scripts', 'bridge.py');

/**
 * Executes python bridge CLI with action and JSON payload.
 */
function invokePythonBridge(action, payload = null) {
  return new Promise((resolve, reject) => {
    const pythonExe = process.platform === 'win32' ? 'python' : 'python3';
    let args = [BRIDGE_SCRIPT, action];
    let tempFilePath = null;

    if (payload !== null) {
      // Write payload to a temporary file to avoid shell escaping issues
      const tempId = `payload_${Date.now()}_${Math.random().toString(36).substring(7)}.json`;
      tempFilePath = path.join(__dirname, '.temp_' + tempId);
      fs.writeFileSync(tempFilePath, JSON.stringify(payload), 'utf8');
      args.push(tempFilePath);
    }

    const proc = spawn(pythonExe, args, { cwd: __dirname });
    let stdoutData = '';
    let stderrData = '';

    proc.stdout.on('data', (chunk) => {
      stdoutData += chunk.toString();
    });

    proc.stderr.on('data', (chunk) => {
      stderrData += chunk.toString();
    });

    proc.on('close', (code) => {
      if (tempFilePath && fs.existsSync(tempFilePath)) {
        try {
          fs.unlinkSync(tempFilePath);
        } catch (e) {
          // ignore cleanup error
        }
      }

      if (code !== 0) {
        return reject(new Error(`Python bridge process exited with code ${code}: ${stderrData}`));
      }

      try {
        const parsed = JSON.parse(stdoutData.trim());
        resolve(parsed);
      } catch (err) {
        reject(new Error(`Failed to parse bridge JSON output: ${err.message}. Raw output: ${stdoutData.substring(0, 500)}`));
      }
    });

    proc.on('error', (err) => {
      if (tempFilePath && fs.existsSync(tempFilePath)) {
        try {
          fs.unlinkSync(tempFilePath);
        } catch (e) {}
      }
      reject(err);
    });
  });
}

// REST Endpoints
app.get('/api/metadata', async (req, res) => {
  try {
    const data = await invokePythonBridge('get-metadata');
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/upload-database', upload.single('database'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No database file provided.' });
    }
    const uploadedPath = req.file.path;
    const inspectResult = await invokePythonBridge('inspect-database', { db_path: uploadedPath });
    if (inspectResult.error) {
      return res.status(400).json({ error: inspectResult.error });
    }

    const dbId = 'custom_' + Date.now();
    res.json({
      success: true,
      db_id: dbId,
      name: `Custom DB (${req.file.originalname})`,
      original_name: req.file.originalname,
      db_path: inspectResult.db_path,
      tables: inspectResult.tables,
      schema_summary: inspectResult.schema_summary,
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/run-query', async (req, res) => {
  try {
    const data = await invokePythonBridge('run-query', req.body);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/benchmark', async (req, res) => {
  try {
    const data = await invokePythonBridge('run-benchmark', req.body);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/scratchpad', async (req, res) => {
  try {
    const data = await invokePythonBridge('run-scratchpad', req.body);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Fallback to index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`[AxiomSQL Server] Running on http://localhost:${PORT}`);
  console.log(`[AxiomSQL Server] Environment: Node.js ${process.version}`);
});
