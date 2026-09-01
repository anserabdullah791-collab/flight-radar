# Flight Radar - Setup Guide

## What is this?
A real-time flight tracking radar that shows aircraft near your location on a radar display. Uses the OpenSky Network API - no hardware, no ADS-B receiver, no antenna needed. Just your laptop and internet.

## Requirements
- Python 3.x
- Internet connection

## Setup (3 steps)

### Step 1: Install Flask and Requests
```
pip install flask requests
```

### Step 2: Download the file
```
git clone https://github.com/anserabdullah791-collab/flight-radar.git
cd flight-radar
```
Or just download flight_radar.py from: https://github.com/anserabdullah791-collab/flight-radar

### Step 3: Run it
```
python flight_radar.py
```

### Step 4: Open your browser
Go to: http://localhost:5656

## Features
- Real-time aircraft tracking from OpenSky Network API
- Radar sweep animation (classic green radar display)
- Shows aircraft callsign, altitude, speed, heading, distance
- Click any aircraft in the sidebar for full details
- Change location (lat/lon) or use city presets
- Adjustable radius (50km - 2000km)
- Auto-refresh every 10 seconds
- No hardware required - works on any laptop
- Free API - no subscription needed

## City Presets Included
- Lahore, Pakistan
- Karachi, Pakistan
- Islamabad, Pakistan
- London, UK
- New York, US
- Dubai, UAE
- Delhi, India

## How it works
The app queries the OpenSky Network API which collects ADS-B data from thousands of volunteers worldwide. You see real aircraft positions in real-time without needing any receiver hardware.

## Note
OpenSky Network free API has rate limits. If you see no data, wait 10 seconds and it will auto-refresh.
