const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs');
const { exec } = require('child_process');
const path = require('path');

const app = express();
const PORT = 8080;
const CONFIG_FILE = '/data/config.json';
const STATUS_FILE = '/data/status.json';
const LOG_DIR = '/data/logs';

app.use(cors());
app.use(bodyParser.json());
app.use(express.static(__dirname));

// Load/Save config
function loadConfig() {
    try {
        if (fs.existsSync(CONFIG_FILE)) {
            return JSON.parse(fs.readFileSync(CONFIG_FILE, 'utf8'));
        }
    } catch(e) {}
    return {};
}

function saveConfig(config) {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
}

// Load/Save status
function loadStatus() {
    try {
        if (fs.existsSync(STATUS_FILE)) {
            return JSON.parse(fs.readFileSync(STATUS_FILE, 'utf8'));
        }
    } catch(e) {}
    return { status: 'idle', lastRun: null };
}

function saveStatus(status) {
    fs.writeFileSync(STATUS_FILE, JSON.stringify(status, null, 2), 'utf8');
}

// Run the script
function runScript(dryRun = false, callback) {
    const config = loadConfig();
    // Validate required fields
    const required = ['apiKey', 'immichServer', 'dbPassword', 'dbContainer', 'dbUser', 'dbName'];
    for (const key of required) {
        if (!config[key]) {
            return callback(new Error(`Missing required configuration: ${key}`));
        }
    }

    const status = loadStatus();
    status.status = 'running';
    saveStatus(status);

    const logFile = path.join(LOG_DIR, `run-${Date.now()}.log`);
    const scriptPath = '/app/scripts/immich-album-creator.ps1';

    // Build command
    let cmd = `pwsh ${scriptPath} -ApiKey '${config.apiKey}' -ImmichServer '${config.immichServer}' -DbContainer '${config.dbContainer}' -DbUser '${config.dbUser}' -DbName '${config.dbName}' -DbPassword '${config.dbPassword}'`;
    if (config.ownerId) cmd += ` -OwnerId '${config.ownerId}'`;
    if (dryRun) cmd += ' -DryRun';
    if (config.logFile) cmd += ` -LogFile '${config.logFile}'`;

    exec(cmd, { maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
        const status = loadStatus();
        status.status = 'idle';
        status.lastRun = new Date().toISOString();
        saveStatus(status);
        callback(error, stdout, stderr);
    });
}

// API endpoints
app.get('/api/config', (req, res) => {
    const config = loadConfig();
    // Don't send passwords back (optional, but we can send a flag)
    // For simplicity, we'll send everything – the UI can show asterisks.
    res.json(config);
});

app.post('/api/config', (req, res) => {
    const newConfig = req.body;
    saveConfig(newConfig);
    res.json({ success: true });
});

app.post('/api/run', (req, res) => {
    const { dryRun } = req.body;
    runScript(dryRun, (error, stdout, stderr) => {
        if (error) {
            res.status(500).json({ success: false, error: stderr || error.message });
        } else {
            res.json({ success: true, message: 'Completed', output: stdout });
        }
    });
});

app.get('/api/status', (req, res) => {
    res.json(loadStatus());
});

app.get('/api/logs', (req, res) => {
    // Return last 50 log entries (simplified)
    fs.readdir(LOG_DIR, (err, files) => {
        if (err) return res.json([]);
        const logFiles = files.filter(f => f.startsWith('run-')).sort().slice(-5);
        const entries = [];
        for (const f of logFiles) {
            const content = fs.readFileSync(path.join(LOG_DIR, f), 'utf8');
            const lines = content.split('\n').filter(l => l.trim()).slice(-20);
            entries.push({ file: f, lines });
        }
        res.json(entries);
    });
});

// Serve index.html
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Immich Album Creator UI running on port ${PORT}`);
});