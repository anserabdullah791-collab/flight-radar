#!/usr/bin/env python3
"""
Flight Radar - Real-time aircraft tracking radar display
Uses OpenSky Network API for live flight data
No hardware required - runs on any laptop
"""

from flask import Flask, jsonify, render_template_string, request
import requests
import math
import time
from datetime import datetime

app = Flask(__name__)

# OpenSky Network API endpoint
OPENSKY_API = "https://opensky-network.org/api/states/all"

# Cache for flight data
cached_data = {"timestamp": 0, "states": []}
CACHE_DURATION = 10  # seconds

# Default center (can be changed via UI)
DEFAULT_LAT = 31.5204  # Lahore, Pakistan
DEFAULT_LON = 74.3587
DEFAULT_RADIUS = 500  # km

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in km"""
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def fetch_flights(lat, lon, radius_km):
    """Fetch real-time flight data from OpenSky Network API"""
    global cached_data
    
    now = time.time()
    if now - cached_data["timestamp"] < CACHE_DURATION and cached_data["states"]:
        # Use cached data but filter by location
        states = cached_data["states"]
    else:
        try:
            # Fetch all states from OpenSky
            resp = requests.get(OPENSKY_API, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                cached_data = {"timestamp": now, "states": data.get("states", []) or []}
                states = cached_data["states"]
            else:
                return {"error": f"API returned {resp.status_code}", "flights": []}
        except Exception as e:
            return {"error": str(e), "flights": []}
    
    # Filter flights within radius
    flights = []
    for s in states:
        try:
            icao24 = s[0]
            callsign = (s[1] or "").strip()
            origin = s[2] or ""
            longitude = s[5]
            latitude = s[6]
            altitude = s[7] or s[13] or 0  # barometric or geometric
            velocity = s[9] or 0  # m/s
            heading = s[10] or 0  # degrees
            on_ground = s[8] or False
            vertical_rate = s[11] or 0  # m/s
            
            if latitude is None or longitude is None:
                continue
            
            distance = haversine(lat, lon, latitude, longitude)
            
            if distance <= radius_km:
                flights.append({
                    "icao24": icao24,
                    "callsign": callsign if callsign else icao24.upper(),
                    "origin": origin,
                    "lat": latitude,
                    "lon": longitude,
                    "altitude": round(altitude, 1) if altitude else 0,
                    "velocity": round(velocity * 3.6, 1) if velocity else 0,  # km/h
                    "heading": round(heading, 1) if heading else 0,
                    "distance": round(distance, 1),
                    "on_ground": on_ground,
                    "vertical_rate": round(vertical_rate, 1) if vertical_rate else 0,
                    "bearing": round(math.degrees(math.atan2(
                        math.radians(longitude - lon) * math.cos(math.radians(lat)),
                        math.radians(latitude - lat)
                    )) % 360, 1)
                })
        except (IndexError, TypeError):
            continue
    
    # Sort by distance
    flights.sort(key=lambda x: x["distance"])
    
    return {
        "total": len(flights),
        "flights": flights[:100],  # Limit to 100 closest
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "center": {"lat": lat, "lon": lon, "radius": radius_km}
    }

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flight Radar</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { 
    background: #000; 
    color: #00ff00; 
    font-family: 'Courier New', monospace; 
    overflow: hidden; 
    height: 100vh;
    display: flex;
    flex-direction: column;
}
.header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 20px; background: #001100; border-bottom: 1px solid #003300;
}
.header h1 { font-size: 18px; letter-spacing: 3px; color: #00ff00; }
.header .status { font-size: 12px; color: #00aa00; }
.controls {
    display: flex; gap: 15px; padding: 8px 20px; background: #001100;
    border-bottom: 1px solid #003300; align-items: center; flex-wrap: wrap;
}
.controls label { font-size: 12px; color: #00aa00; }
.controls input, .controls select, .controls button {
    background: #002200; border: 1px solid #004400; color: #00ff00;
    padding: 4px 8px; font-family: 'Courier New', monospace; font-size: 12px; border-radius: 3px;
}
.controls button { cursor: pointer; }
.controls button:hover { background: #004400; }
.main { display: flex; flex: 1; overflow: hidden; }
.radar-container { flex: 1; position: relative; display: flex; align-items: center; justify-content: center; }
#radarCanvas { display: block; }
.sidebar {
    width: 320px; background: #001100; border-left: 1px solid #003300;
    overflow-y: auto; padding: 10px;
}
.sidebar h2 { font-size: 14px; color: #00ff00; margin-bottom: 10px; letter-spacing: 2px; }
.flight-item {
    background: #001a00; border: 1px solid #003300; padding: 8px 10px;
    margin-bottom: 6px; border-radius: 4px; cursor: pointer; transition: all 0.2s;
}
.flight-item:hover { background: #003300; border-color: #006600; }
.flight-item .cs { font-weight: bold; color: #00ff00; font-size: 13px; }
.flight-item .info { font-size: 11px; color: #008800; margin-top: 3px; }
.flight-item .dist { color: #00cc00; }
.footer { padding: 5px 20px; background: #001100; border-top: 1px solid #003300; font-size: 11px; color: #005500; }
.hidden { display: none; }
.flight-detail {
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    background: #001a00; border: 1px solid #006600; padding: 15px 25px;
    border-radius: 8px; z-index: 100; font-size: 12px; box-shadow: 0 0 20px rgba(0,255,0,0.3);
}
.flight-detail h3 { color: #00ff00; margin-bottom: 8px; }
.flight-detail .row { display: flex; justify-content: space-between; margin: 3px 0; gap: 30px; }
.flight-detail .label { color: #008800; }
.flight-detail .value { color: #00cc00; }
.flight-detail .close { position: absolute; top: 8px; right: 12px; cursor: pointer; color: #ff0000; font-weight: bold; }
</style>
</head>
<body>

<div class="header">
    <h1>&#9678; FLIGHT RADAR</h1>
    <div class="status" id="status">Initializing...</div>
</div>

<div class="controls">
    <label>Lat: <input type="number" id="latInput" value="31.5204" step="0.01"></label>
    <label>Lon: <input type="number" id="lonInput" value="74.3587" step="0.01"></label>
    <label>Radius: <input type="number" id="radiusInput" value="500" step="50">km</label>
    <button onclick="updateLocation()">Update</button>
    <select id="cityPreset" onchange="setPreset()">
        <option value="">-- City Preset --</option>
        <option value="31.5204,74.3587">Lahore, PK</option>
        <option value="24.8607,67.0011">Karachi, PK</option>
        <option value="33.6844,73.0479">Islamabad, PK</option>
        <option value="51.5074,-0.1278">London, UK</option>
        <option value="40.7128,-74.0060">New York, US</option>
        <option value="25.2048,55.2708">Dubai, UAE</option>
        <option value="28.6139,77.2090">Delhi, IN</option>
    </select>
    <label>Auto-refresh: <input type="checkbox" id="autoRefresh" checked onchange="toggleAuto()"></label>
</div>

<div class="main">
    <div class="radar-container">
        <canvas id="radarCanvas" width="600" height="600"></canvas>
    </div>
    <div class="sidebar">
        <h2>&#9650; TRACKED AIRCRAFT (<span id="count">0</span>)</h2>
        <div id="flightList"></div>
    </div>
</div>

<div class="footer" id="footer">OpenSky Network API | No hardware required | Data updates every 10s</div>

<div class="flight-detail hidden" id="flightDetail">
    <span class="close" onclick="closeDetail()">X</span>
    <div id="detailContent"></div>
</div>

<script>
const canvas = document.getElementById('radarCanvas');
const ctx = canvas.getContext('2d');
let flights = [];
let centerLat = 31.5204;
let centerLon = 74.3587;
let radius = 500;
let sweepAngle = 0;
let autoRefresh = true;
let refreshInterval = null;
let selectedFlight = null;

function resizeCanvas() {
    const container = canvas.parentElement;
    const size = Math.min(container.clientWidth, container.clientHeight) - 20;
    canvas.width = size;
    canvas.height = size;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

function drawRadar() {
    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;
    const maxR = Math.min(w, h) / 2 - 20;
    
    // Clear
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, w, h);
    
    // Radar circles
    for (let i = 1; i <= 4; i++) {
        ctx.beginPath();
        ctx.arc(cx, cy, maxR * i / 4, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(0, 255, 0, ${0.15 + i * 0.05})`;
        ctx.lineWidth = 1;
        ctx.stroke();
        
        // Distance labels
        ctx.fillStyle = 'rgba(0, 200, 0, 0.5)';
        ctx.font = '10px Courier New';
        ctx.fillText(`${Math.round(radius * i / 4)}km`, cx + 4, cy - maxR * i / 4 + 12);
    }
    
    // Cross lines
    ctx.strokeStyle = 'rgba(0, 255, 0, 0.15)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(cx, cy - maxR); ctx.lineTo(cx, cy + maxR);
    ctx.moveTo(cx - maxR, cy); ctx.lineTo(cx + maxR, cy);
    ctx.stroke();
    
    // Diagonal lines
    ctx.strokeStyle = 'rgba(0, 255, 0, 0.08)';
    ctx.beginPath();
    for (let a = 0; a < 360; a += 30) {
        const rad = (a - 90) * Math.PI / 180;
        ctx.moveTo(cx, cy);
        ctx.lineTo(cx + Math.cos(rad) * maxR, cy + Math.sin(rad) * maxR);
    }
    ctx.stroke();
    
    // Compass labels
    ctx.fillStyle = 'rgba(0, 255, 0, 0.4)';
    ctx.font = '11px Courier New';
    ctx.textAlign = 'center';
    ctx.fillText('N', cx, 14);
    ctx.fillText('S', cx, h - 4);
    ctx.fillText('E', w - 8, cy + 4);
    ctx.fillText('W', 8, cy + 4);
    ctx.textAlign = 'left';
    
    // Sweep
    const sweepRad = (sweepAngle - 90) * Math.PI / 180;
    const gradient = ctx.createLinearGradient(
        cx, cy,
        cx + Math.cos(sweepRad) * maxR,
        cy + Math.sin(sweepRad) * maxR
    );
    gradient.addColorStop(0, 'rgba(0, 255, 0, 0.4)');
    gradient.addColorStop(1, 'rgba(0, 255, 0, 0)');
    
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, maxR, sweepRad - 0.5, sweepRad);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();
    
    // Draw flights
    flights.forEach(f => {
        const ratio = f.distance / radius;
        if (ratio > 1) return;
        
        const bearingRad = (f.bearing - 90) * Math.PI / 180;
        const fx = cx + Math.cos(bearingRad) * (maxR * ratio);
        const fy = cy + Math.sin(bearingRad) * (maxR * ratio);
        
        // Calculate fade based on sweep proximity
        const angleDiff = ((sweepAngle - f.bearing + 360) % 360) / 360;
        const fade = Math.max(0.3, 1 - angleDiff);
        
        // Plane triangle (pointing in heading direction)
        const headingRad = (f.heading - 90) * Math.PI / 180;
        const size = f.on_ground ? 4 : 6;
        
        ctx.save();
        ctx.translate(fx, fy);
        ctx.rotate(headingRad);
        ctx.beginPath();
        ctx.moveTo(size, 0);
        ctx.lineTo(-size, -size * 0.6);
        ctx.lineTo(-size, size * 0.6);
        ctx.closePath();
        ctx.fillStyle = f.on_ground ? `rgba(0, 180, 0, ${fade})` : `rgba(0, 255, 0, ${fade})`;
        ctx.fill();
        ctx.strokeStyle = `rgba(0, 255, 0, ${fade})`;
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.restore();
        
        // Label for nearby flights
        if (f.distance < radius * 0.5) {
            ctx.fillStyle = `rgba(0, 255, 0, ${fade * 0.6})`;
            ctx.font = '9px Courier New';
            ctx.fillText(f.callsign, fx + 8, fy - 4);
            ctx.fillText(`${f.altitude}m`, fx + 8, fy + 8);
        }
    });
    
    // Center dot
    ctx.beginPath();
    ctx.arc(cx, cy, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#00ff00';
    ctx.fill();
    
    // Sweep animation
    sweepAngle = (sweepAngle + 1.5) % 360;
    requestAnimationFrame(drawRadar);
}

function updateLocation() {
    centerLat = parseFloat(document.getElementById('latInput').value);
    centerLon = parseFloat(document.getElementById('lonInput').value);
    radius = parseFloat(document.getElementById('radiusInput').value);
    fetchFlights();
}

function setPreset() {
    const preset = document.getElementById('cityPreset').value;
    if (!preset) return;
    const [lat, lon] = preset.split(',');
    document.getElementById('latInput').value = lat;
    document.getElementById('lonInput').value = lon;
    updateLocation();
}

async function fetchFlights() {
    const status = document.getElementById('status');
    status.textContent = 'Scanning airspace...';
    status.style.color = '#ffff00';
    
    try {
        const resp = await fetch(`/api/flights?lat=${centerLat}&lon=${centerLon}&radius=${radius}`);
        const data = await resp.json();
        
        if (data.error) {
            status.textContent = `Error: ${data.error}`;
            status.style.color = '#ff0000';
            return;
        }
        
        flights = data.flights || [];
        document.getElementById('count').textContent = flights.length;
        status.textContent = `${data.total} aircraft detected | Last update: ${data.timestamp}`;
        status.style.color = '#00ff00';
        document.getElementById('footer').textContent = 
            `OpenSky Network API | Center: ${centerLat.toFixed(2)}, ${centerLon.toFixed(2)} | Radius: ${radius}km | ${flights.length} aircraft`;
        
        renderFlightList();
    } catch (e) {
        status.textContent = `Connection error: ${e.message}`;
        status.style.color = '#ff0000';
    }
}

function renderFlightList() {
    const list = document.getElementById('flightList');
    list.innerHTML = '';
    
    if (flights.length === 0) {
        list.innerHTML = '<div style="color:#005500;text-align:center;padding:20px;">No aircraft in range</div>';
        return;
    }
    
    flights.forEach(f => {
        const item = document.createElement('div');
        item.className = 'flight-item';
        item.onclick = () => showDetail(f);
        item.innerHTML = `
            <div class="cs">${f.callsign}</div>
            <div class="info">Alt: ${f.altitude}m | Spd: ${f.velocity}km/h</div>
            <div class="info">Hdg: ${f.heading}&deg; | Dist: <span class="dist">${f.distance}km</span></div>
            <div class="info">${f.origin ? 'From: ' + f.origin : ''} ${f.on_ground ? '| ON GROUND' : ''}</div>
        `;
        list.appendChild(item);
    });
}

function showDetail(f) {
    const detail = document.getElementById('flightDetail');
    const content = document.getElementById('detailContent');
    content.innerHTML = `
        <h3>&#9650; ${f.callsign}</h3>
        <div class="row"><span class="label">ICAO24:</span><span class="value">${f.icao24}</span></div>
        <div class="row"><span class="label">Origin Country:</span><span class="value">${f.origin}</span></div>
        <div class="row"><span class="label">Latitude:</span><span class="value">${f.lat.toFixed(4)}</span></div>
        <div class="row"><span class="label">Longitude:</span><span class="value">${f.lon.toFixed(4)}</span></div>
        <div class="row"><span class="label">Altitude:</span><span class="value">${f.altitude}m</span></div>
        <div class="row"><span class="label">Velocity:</span><span class="value">${f.velocity}km/h</span></div>
        <div class="row"><span class="label">Heading:</span><span class="value">${f.heading}&deg;</span></div>
        <div class="row"><span class="label">Distance:</span><span class="value">${f.distance}km</span></div>
        <div class="row"><span class="label">Bearing:</span><span class="value">${f.bearing}&deg;</span></div>
        <div class="row"><span class="label">Vertical Rate:</span><span class="value">${f.vertical_rate}m/s</span></div>
        <div class="row"><span class="label">On Ground:</span><span class="value">${f.on_ground ? 'Yes' : 'No'}</span></div>
    `;
    detail.classList.remove('hidden');
}

function closeDetail() {
    document.getElementById('flightDetail').classList.add('hidden');
}

function toggleAuto() {
    autoRefresh = document.getElementById('autoRefresh').checked;
    if (autoRefresh) {
        startAutoRefresh();
    } else {
        stopAutoRefresh();
    }
}

function startAutoRefresh() {
    if (refreshInterval) clearInterval(refreshInterval);
    refreshInterval = setInterval(fetchFlights, 10000); // 10 seconds
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

// Initialize
drawRadar();
fetchFlights();
startAutoRefresh();
</script>

</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/flights')
def get_flights():
    lat = float(request.args.get('lat', DEFAULT_LAT))
    lon = float(request.args.get('lon', DEFAULT_LON))
    radius = float(request.args.get('radius', DEFAULT_RADIUS))
    return jsonify(fetch_flights(lat, lon, radius))

if __name__ == '__main__':
    print("=" * 50)
    print("  FLIGHT RADAR - Starting...")
    print("  Open your browser to: http://localhost:5656")
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5656, debug=False)
