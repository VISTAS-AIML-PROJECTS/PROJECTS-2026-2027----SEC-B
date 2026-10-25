import { useEffect, useMemo, useRef, useState } from 'react'
import maplibregl, { Map, Marker } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import './App.css'

type Point = { lat: number; lon: number; label?: string; source?: string; pincode?: string }
type Candidate = Point & { display_name: string; source: string; verified_level?: string; road?: string; neighbourhood?: string; suburb?: string }
type RouteOption = { route_id: number; distance_km: number; duration_min: number; geometry: { type: 'LineString'; coordinates: [number, number][] } }
type PickMode = 'start' | 'destination'
type Vehicle = { name: string; Battery_Capacity_kWh: number; Manufacturer: string; Model: string; Motor_Power_kW: number; Vehicle_Weight_kg: number; Battery_Type: string; Year: number }
type Station = { name: string; lat: number; lon: number; distance_from_origin_km: number; distance_to_route_km: number; power_kw: number; price_rs_kwh: number; power_assumed: boolean; price_assumed: boolean; recommended: boolean; address?: string; connector?: string }
type Stop = { name: string; lat: number; lon: number; distance_from_origin_km: number; distance_to_route_km: number; arrival_soc_pct: number; charge_amount_kwh: number; charging_power_kw: number; charging_time_min: number; charging_cost_rs: number; data_note?: string; address?: string; connector?: string }
type EvPlan = { route_distance_km: number; predicted_energy_kwh: number; energy_per_km_kwh: number; estimated_range_km: number; initial_soc_pct: number; arrival_soc_pct: number; reserve_soc_pct: number; charging_needed: boolean; charging_stops: Stop[]; optimizer: string; message: string; station_count: number; stations: Station[]; prediction_meta?: { method: string; reference_distance_km?: number; training_distance_max_km?: number }; assumptions?: { note?: string } }

const API = 'http://127.0.0.1:8000/api'
const CHENNAI: [number, number] = [80.2707, 13.0827]

function hav(a: [number, number], b: [number, number]) {
  const R = 6371.0088
  const p1 = a[0] * Math.PI / 180
  const p2 = b[0] * Math.PI / 180
  const dp = (b[0] - a[0]) * Math.PI / 180
  const dl = (b[1] - a[1]) * Math.PI / 180
  const h = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(h))
}

function pointAtRoute(route: RouteOption, pct: number): Point {
  const cs = route.geometry.coordinates
  if (cs.length < 2) return { lat: cs[0]?.[1] ?? 0, lon: cs[0]?.[0] ?? 0 }
  const clamped = Math.max(0, Math.min(100, pct))
  const cumulative = [0]
  for (let i = 1; i < cs.length; i++) {
    cumulative.push(cumulative[i - 1] + hav([cs[i - 1][1], cs[i - 1][0]], [cs[i][1], cs[i][0]]))
  }
  const target = cumulative[cumulative.length - 1] * clamped / 100
  let idx = 1
  while (idx < cumulative.length && cumulative[idx] < target) idx++
  idx = Math.min(idx, cumulative.length - 1)
  const d0 = cumulative[idx - 1]
  const d1 = cumulative[idx]
  const ratio = d1 > d0 ? (target - d0) / (d1 - d0) : 0
  const lon = cs[idx - 1][0] + (cs[idx][0] - cs[idx - 1][0]) * ratio
  const lat = cs[idx - 1][1] + (cs[idx][1] - cs[idx - 1][1]) * ratio
  return { lat, lon }
}

function bearingAtRoute(route: RouteOption, pct: number) {
  const p1 = pointAtRoute(route, Math.max(0, pct - 0.3))
  const p2 = pointAtRoute(route, Math.min(100, pct + 0.3))
  const y = Math.sin((p2.lon - p1.lon) * Math.PI / 180) * Math.cos(p2.lat * Math.PI / 180)
  const x = Math.cos(p1.lat * Math.PI / 180) * Math.sin(p2.lat * Math.PI / 180) -
    Math.sin(p1.lat * Math.PI / 180) * Math.cos(p2.lat * Math.PI / 180) * Math.cos((p2.lon - p1.lon) * Math.PI / 180)
  return Math.atan2(y, x) * 180 / Math.PI
}

function escapeHtml(value: string) {
  return value.replace(/[&<>'"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c] || c))
}

function pointFromCandidate(c: Candidate): Point {
  return { lat: c.lat, lon: c.lon, label: c.display_name, source: c.source, pincode: c.pincode }
}

function makeMarkerElement(kind: 'car' | 'charger' | 'start' | 'destination', recommended = false) {
  const el = document.createElement('div')
  if (kind === 'car') {
    el.className = 'ev-car-marker'
    el.innerHTML = `
      <div class="ev-beacon-ring"></div>
      <div class="ev-car-body" aria-label="Current EV position">
        <svg viewBox="0 0 64 64" aria-hidden="true">
          <path d="M16 37l5-16c1-3 3-5 7-5h10c4 0 6 2 8 5l5 16v10c0 2-2 4-4 4h-4v-6H21v6h-4c-2 0-4-2-4-4V37h3zm7-13-3 9h24l-3-9c-.5-1.4-1.6-2-3-2H26c-1.4 0-2.5.6-3 2zM21 41h22c2 0 3 2 3 4H18c0-2 1-4 3-4z"/>
          <circle cx="21" cy="45" r="3"/><circle cx="43" cy="45" r="3"/>
        </svg>
      </div>`
  } else if (kind === 'charger') {
    el.className = `charger-marker ${recommended ? 'recommended' : ''}`
    el.innerHTML = '<span>⚡</span>'
    el.title = 'EV charging station'
  } else {
    el.className = `endpoint-marker ${kind}`
    el.textContent = kind === 'start' ? 'A' : 'B'
  }
  return el
}

function App() {
  const mapEl = useRef<HTMLDivElement | null>(null)
  const mapRef = useRef<Map | null>(null)
  const markersRef = useRef<Marker[]>([])
  const carMarkerRef = useRef<Marker | null>(null)
  const pickModeRef = useRef<PickMode | null>(null)

  const [startQuery, setStartQuery] = useState('')
  const [destinationQuery, setDestinationQuery] = useState('')
  const [startResults, setStartResults] = useState<Candidate[]>([])
  const [destinationResults, setDestinationResults] = useState<Candidate[]>([])
  const [start, setStart] = useState<Point | null>(null)
  const [destination, setDestination] = useState<Point | null>(null)
  const [pickMode, setPickMode] = useState<PickMode | null>(null)
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [vehicle, setVehicle] = useState<Vehicle | null>(null)
  const [soc, setSoc] = useState(80)
  const [speed, setSpeed] = useState(35)
  const [temp, setTemp] = useState(30)
  const [weather, setWeather] = useState('Clear')
  const [soh, setSoh] = useState(95)
  const [style, setStyle] = useState('Moderate')
  const [routes, setRoutes] = useState<RouteOption[]>([])
  const [selectedRoute, setSelectedRoute] = useState(0)
  const [plan, setPlan] = useState<EvPlan | null>(null)
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [rideStarted, setRideStarted] = useState(false)
  const [progress, setProgress] = useState(0)
  const [gpsError, setGpsError] = useState('')

  useEffect(() => {
    fetch(`${API}/ev/vehicles`)
      .then(r => r.json())
      .then(d => {
        const list = d.vehicles || []
        setVehicles(list)
        if (list.length) setVehicle(list[0])
      })
      .catch(() => setError('EV vehicle data could not be loaded.'))
  }, [])

  useEffect(() => {
    pickModeRef.current = pickMode
  }, [pickMode])

  useEffect(() => {
    if (!mapEl.current) return
    const map = new maplibregl.Map({
      container: mapEl.current,
      center: CHENNAI,
      zoom: 11.8,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '&copy; OpenStreetMap contributors',
          },
        },
        layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
      },
    })
    map.addControl(new maplibregl.NavigationControl(), 'bottom-right')
    map.addControl(new maplibregl.FullscreenControl(), 'bottom-right')

    map.on('load', () => {
      map.addSource('routes', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      map.addLayer({
        id: 'route-hit',
        type: 'line',
        source: 'routes',
        paint: { 'line-color': '#000', 'line-opacity': 0, 'line-width': 22 },
      })
      map.addLayer({
        id: 'routes-line',
        type: 'line',
        source: 'routes',
        paint: {
          'line-color': [
            'case',
            ['get', 'selected'], '#1769ff',
            ['==', ['get', 'route_index'], 1], '#f59e0b',
            '#8b5cf6',
          ],
          'line-width': ['case', ['get', 'selected'], 6, 4],
          'line-opacity': ['case', ['get', 'selected'], 0.96, 0.72],
        },
      })

      map.on('click', e => {
        const mode = pickModeRef.current
        if (!mode) return
        const p: Point = {
          lat: e.lngLat.lat,
          lon: e.lngLat.lng,
          label: mode === 'start' ? 'Map-selected start' : 'Map-selected destination',
          source: 'Map click',
        }
        if (mode === 'start') {
          setStart(p); setStartQuery(''); setStartResults([]); setNotice('Start point selected from the map.')
        } else {
          setDestination(p); setDestinationQuery(''); setDestinationResults([]); setNotice('Destination selected from the map.')
        }
        setPickMode(null)
      })
    })

    mapRef.current = map
    return () => {
      carMarkerRef.current?.remove()
      markersRef.current.forEach(m => m.remove())
      map.remove()
      carMarkerRef.current = null
    }
  }, [])

  useEffect(() => {
    const source = mapRef.current?.getSource('routes') as maplibregl.GeoJSONSource | undefined
    if (!source) return
    source.setData({
      type: 'FeatureCollection',
      features: routes.map((r, i) => ({
        type: 'Feature',
        properties: { route_id: r.route_id, route_index: i, selected: i === selectedRoute },
        geometry: r.geometry,
      })),
    })
  }, [routes, selectedRoute])

  useEffect(() => {
    markersRef.current.forEach(m => m.remove())
    markersRef.current = []
    if (!mapRef.current) return

    if (start) markersRef.current.push(new maplibregl.Marker({ element: makeMarkerElement('start') }).setLngLat([start.lon, start.lat]).addTo(mapRef.current))
    if (destination) markersRef.current.push(new maplibregl.Marker({ element: makeMarkerElement('destination') }).setLngLat([destination.lon, destination.lat]).addTo(mapRef.current))

    if (plan) {
      for (const s of plan.stations) {
        const marker = new maplibregl.Marker({ element: makeMarkerElement('charger', s.recommended) })
          .setLngLat([s.lon, s.lat])
          .setPopup(new maplibregl.Popup({ offset: 18 }).setHTML(
            `<strong>EV Charging Station</strong><br>${escapeHtml(s.name)}<br>${s.distance_from_origin_km.toFixed(1)} km along route${s.recommended ? '<br><b>Recommended stop</b>' : ''}`
          ))
          .addTo(mapRef.current)
        markersRef.current.push(marker)
      }
    }
  }, [start, destination, plan])

  useEffect(() => {
    if (!rideStarted || !routes[selectedRoute] || !mapRef.current || !start) {
      carMarkerRef.current?.remove()
      carMarkerRef.current = null
      return
    }
    if (!carMarkerRef.current) {
      carMarkerRef.current = new maplibregl.Marker({ element: makeMarkerElement('car') })
        .setLngLat([start.lon, start.lat])
        .addTo(mapRef.current)
    }
    const p = pointAtRoute(routes[selectedRoute], progress)
    const element = carMarkerRef.current.getElement()
    const body = element.querySelector('.ev-car-body') as HTMLElement | null
    if (body) body.style.transform = `rotate(${bearingAtRoute(routes[selectedRoute], progress)}deg)`
    carMarkerRef.current.setLngLat([p.lon, p.lat])
  }, [rideStarted, progress, routes, selectedRoute, start])

  const fly = (p: Point, z = 15) => mapRef.current?.flyTo({ center: [p.lon, p.lat], zoom: z, essential: true })

  const fitRoutes = (rs: RouteOption[]) => {
    if (!mapRef.current || !rs.length) return
    const all = rs[0].geometry.coordinates
    const bounds = new maplibregl.LngLatBounds()
    all.forEach(c => bounds.extend(c))
    mapRef.current.fitBounds(bounds, { padding: 140, duration: 800, maxZoom: 14 })
  }

  const search = async (which: PickMode) => {
    const q = (which === 'start' ? startQuery : destinationQuery).trim()
    if (q.length < 3) return
    setLoading(true); setError('')
    try {
      const r = await fetch(`${API}/geocode?q=${encodeURIComponent(q)}`)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Address search failed.')
      if (which === 'start') setStartResults(d.results || [])
      else setDestinationResults(d.results || [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Address search failed.')
    } finally { setLoading(false) }
  }

  const choose = (which: PickMode, c: Candidate) => {
    const p = pointFromCandidate(c)
    if (which === 'start') { setStart(p); setStartQuery(c.display_name); setStartResults([]) }
    else { setDestination(p); setDestinationQuery(c.display_name); setDestinationResults([]) }
    fly(p)
    setPickMode(null)
    setPlan(null)
    setRoutes([])
    setNotice(`${which === 'start' ? 'Start' : 'Destination'} selected.`)
  }

  const useGps = () => {
    setGpsError('')
    if (!navigator.geolocation) {
      setGpsError('Browser geolocation is unavailable. Use manual entry or map selection.')
      return
    }
    setNotice('Requesting device location…')
    navigator.geolocation.getCurrentPosition(
      async pos => {
        const lat = pos.coords.latitude
        const lon = pos.coords.longitude
        const accuracy = Math.round(pos.coords.accuracy)

        setNotice('GPS received. Resolving current address…')

        try {
          const r = await fetch(
            `${API}/reverse-geocode?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`
          )

          const d = await r.json()

          if (!r.ok) {
            throw new Error(d.detail || 'Could not resolve current address.')
          }

          const p: Point = {
            lat,
            lon,
            label: d.display_name,
            source: 'Browser GPS',
            pincode: d.pincode || '',
          }

          setStart(p)
          setStartQuery('')
          setStartResults([])
          setPickMode(null)
          fly(p, 16)

          setNotice(`Current address found (±${accuracy} m).`)
        } catch {
          const p: Point = {
            lat,
            lon,
            label: 'Current GPS location',
            source: 'Browser GPS',
          }

          setStart(p)
          setStartQuery('')
          setStartResults([])
          setPickMode(null)
          fly(p, 16)

          setNotice(
            `GPS received (±${accuracy} m), but the address could not be resolved.`
          )
        }
      },
      err => {
        setGpsError(err.code === 1 ? 'Location permission was denied. Allow location for localhost.' : err.code === 2 ? 'The desktop browser could not determine a location. Use manual start or map selection.' : 'Location request timed out.')
        setPickMode('start')
      },
      { enableHighAccuracy: true, maximumAge: 0, timeout: 12000 },
    )
  }

  const planRoute = async () => {
    if (!start || !destination) { setError('Set both start and destination first.'); return }
    setLoading(true); setError(''); setPlan(null); setRoutes([]); setRideStarted(false); setProgress(0)
    try {
      const body = JSON.stringify({ origin: { lat: start.lat, lon: start.lon }, destination: { lat: destination.lat, lon: destination.lon }, alternatives: 3 })
      let r = await fetch(`${API}/route/diverse`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
      if (!r.ok) r = await fetch(`${API}/route`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'Route calculation failed.')
      const rs: RouteOption[] = d.routes || []
      if (!rs.length) throw new Error('No drivable route was found.')
      setRoutes(rs); setSelectedRoute(0); setNotice(`Found ${rs.length} Chennai routes using Dijkstra.`); setTimeout(() => fitRoutes(rs), 50)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Route calculation failed.')
    } finally { setLoading(false) }
  }

  const analyze = async (route: RouteOption) => {
    if (!vehicle) return
    setLoading(true); setError('')
    try {
      const r = await fetch(`${API}/ev/analyze`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vehicle: vehicle.name, initial_soc_pct: soc, avg_speed_kmh: speed, ambient_temp_c: temp, weather, road_type: 'Urban', soh_pct: soh, driving_style: style, route }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || 'EV analysis failed')
      setPlan(d)
      setNotice('EV energy, range, station recommendation and PuLP optimization completed.')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'EV analysis failed.')
    } finally { setLoading(false) }
  }

  useEffect(() => {
    if (routes[selectedRoute] && vehicle) analyze(routes[selectedRoute])
    // Route/vehicle changes trigger analysis; battery/environment changes use the explicit Recalculate button.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRoute, vehicle?.name, routes.length])

  const safeRange = plan?.estimated_range_km ?? 0
  const rangeToZero = plan && plan.energy_per_km_kwh > 0 && vehicle ? (vehicle.Battery_Capacity_kWh * soc / 100) / plan.energy_per_km_kwh : 0

  const monitor = useMemo(() => {
    if (!plan || !routes[selectedRoute] || !vehicle) return null
    const total = plan.route_distance_km
    const used = plan.predicted_energy_kwh * progress / 100
    const current = Math.max(0, soc - used / vehicle.Battery_Capacity_kWh * 100)
    const remain = Math.max(0, total * (1 - progress / 100))
    const remEnergy = Math.max(0, plan.predicted_energy_kwh * remain / Math.max(total, 1e-9))
    const projected = Math.max(0, current - remEnergy / vehicle.Battery_Capacity_kWh * 100)
    const stop = plan.charging_stops[0]
    let alert = 'green'
    if (current < plan.reserve_soc_pct) alert = 'red'
    else if (stop) {
      const stopRemain = Math.max(0, stop.distance_from_origin_km - total * progress / 100)
      const stopEnergy = plan.energy_per_km_kwh * stopRemain
      const reserveEnergy = vehicle.Battery_Capacity_kWh * plan.reserve_soc_pct / 100
      const currentEnergy = vehicle.Battery_Capacity_kWh * current / 100
      if (currentEnergy < reserveEnergy + stopEnergy) alert = 'red'
      else if (projected < plan.reserve_soc_pct) alert = 'yellow'
    } else if (projected < plan.reserve_soc_pct) alert = 'yellow'
    return { current, remain, projected, stop, alert }
  }, [plan, progress, soc, vehicle, selectedRoute, routes])

  const updateGpsDuringRide = () => {
    if (!navigator.geolocation) { setGpsError('Geolocation unavailable. Use the simulation slider.'); return }
    navigator.geolocation.getCurrentPosition(
      pos => {
        const p = { lat: pos.coords.latitude, lon: pos.coords.longitude }
        if (routes[selectedRoute]) {
          const pct = routeProgressByNearestVertex(routes[selectedRoute], p)
          setProgress(pct); fly(p, 16)
        }
        setNotice(`Ride GPS updated (±${Math.round(pos.coords.accuracy)} m).`)
      },
      () => setGpsError('Unable to update ride GPS; use the simulation slider for the desktop demo.'),
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 },
    )
  }

  return (
    <div className="app">
      <div ref={mapEl} className="map" />
      {pickMode && <div className="map-mode-banner">Click the map to choose {pickMode === 'start' ? 'START' : 'DESTINATION'}</div>}

      <div className="brand-card">
        <div className="brand-icon">⚡</div>
        <div><div className="brand-title">Chennai EV Trip Planner</div><div className="brand-subtitle">AI-Assisted EV Range Prediction & Smart Charging</div></div>
      </div>

      <div className="map-legend">
        <span><i className="legend-swatch start"/> Start</span>
        <span><i className="legend-swatch destination"/> Destination</span>
        <span><i className="legend-icon charger">⚡</i> EV charger</span>
        {rideStarted && <span><i className="legend-icon car">🚗</i> Current EV</span>}
      </div>

      <section className="panel left-panel">
        <div className="endpoint-label"><span className="dot green"/> Start</div>
        <button className="ghost-button" onClick={useGps}>◎ Use my current location</button>
        <div className="pick-row"><input value={startQuery} onChange={e => setStartQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && search('start')} placeholder="Enter start address, street or landmark"/><button className="search-button" onClick={() => search('start')}>⌕</button></div>
        {start && (
  <div className="selected-address">
    <strong>{start.label || 'Selected start'}</strong>
    <span>
      {start.pincode
        ? `PIN ${start.pincode}`
        : start.source === 'Browser GPS'
          ? 'Address resolved from GPS'
          : `${start.lat.toFixed(6)}, ${start.lon.toFixed(6)}`}
    </span>
  </div>
)}
        {startResults.length > 0 && <div className="results">{startResults.map((r, i) => <button className="result" key={i} onClick={() => choose('start', r)}><strong>{r.display_name}</strong><span>{r.source}{r.pincode ? ` • ${r.pincode}` : ''}</span></button>)}</div>}
        <button className={`pick-map ${pickMode === 'start' ? 'active' : ''}`} onClick={() => setPickMode('start')}>＋ Click map to set start</button>

        <div className="separator"/>
        <div className="endpoint-label"><span className="dot red"/> Destination</div>
        <div className="pick-row"><input value={destinationQuery} onChange={e => setDestinationQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && search('destination')} placeholder="Enter destination address, street or landmark"/><button className="search-button" onClick={() => search('destination')}>⌕</button></div>
        {destination && <div className="selected-address"><strong>{destination.label || 'Selected destination'}</strong><span>{destination.lat.toFixed(6)}, {destination.lon.toFixed(6)}{destination.pincode ? ` • ${destination.pincode}` : ''}</span></div>}
        {destinationResults.length > 0 && <div className="results">{destinationResults.map((r, i) => <button className="result" key={i} onClick={() => choose('destination', r)}><strong>{r.display_name}</strong><span>{r.source}{r.pincode ? ` • ${r.pincode}` : ''}</span></button>)}</div>}
        <button className={`pick-map ${pickMode === 'destination' ? 'active' : ''}`} onClick={() => setPickMode('destination')}>＋ Click map to set destination</button>

        {gpsError && <div className="error">{gpsError}</div>}
        {error && <div className="error">{error}</div>}
        {notice && <div className="notice">{notice}</div>}
        <button className="primary-button" onClick={planRoute} disabled={!start || !destination || loading}>{loading ? 'Working…' : 'Plan route'}</button>

        {routes.length > 0 && <div className="route-card-inline"><div className="route-title">Route options</div>{routes.map((r, i) => <button className={`route-option ${i === selectedRoute ? 'selected' : ''}`} key={r.route_id} onClick={() => setSelectedRoute(i)}><div><strong>{i === 0 ? 'Primary route' : `Alternative Route ${i}`}</strong><span>{r.distance_km.toFixed(2)} km • {r.duration_min.toFixed(0)} min</span></div><span className="route-badge">{i === selectedRoute ? 'Selected' : 'Choose'}</span></button>)}</div>}
      </section>

      <section className="panel right-panel">
        <h3>EV trip intelligence</h3>
        <label>EV model<select value={vehicle?.name || ''} onChange={e => setVehicle(vehicles.find(v => v.name === e.target.value) || null)}>{vehicles.map(v => <option key={v.name}>{v.name}</option>)}</select></label>
        <div className="row-between"><span>Current battery</span><strong>{soc}%</strong></div>
        <input type="range" min="0" max="100" value={soc} onChange={e => setSoc(Number(e.target.value))}/>
        <div className="trip-inputs">
          <label>Average speed (km/h)<input type="number" min="1" value={speed} onChange={e => setSpeed(Number(e.target.value))}/></label>
          <label>SOH (%)<input type="number" min="50" max="100" value={soh} onChange={e => setSoh(Number(e.target.value))}/></label>
          <label>Temperature (°C)<input type="number" value={temp} onChange={e => setTemp(Number(e.target.value))}/></label>
          <label>Weather<select value={weather} onChange={e => setWeather(e.target.value)}><option>Clear</option><option>Cloudy</option><option>Rain</option><option>Hot</option></select></label>
          <label>Driving style<select value={style} onChange={e => setStyle(e.target.value)}><option>Calm</option><option>Moderate</option><option>Aggressive</option></select></label>
        </div>
        <div className="reserve">Minimum reserve: 25%. XGBoost predicts route energy; PuLP MILP selects a charging stop when required.</div>
        {routes[selectedRoute] && vehicle && <button className="recalc-button" onClick={() => analyze(routes[selectedRoute])} disabled={loading}>↻ Recalculate EV analysis</button>}

        {plan && <div className="ev-summary">
          <div className="metric-grid">
            <div><small>Trip energy</small><b>{plan.predicted_energy_kwh.toFixed(2)} kWh</b></div>
            <div><small>Range to 0% SOC</small><b>{rangeToZero.toFixed(1)} km</b></div>
            <div><small>Safe range (25% reserve)</small><b>{safeRange.toFixed(1)} km</b></div>
            <div><small>Arrival SOC</small><b>{plan.arrival_soc_pct.toFixed(1)}%</b></div>
          </div>

          <div className={`charge-box ${plan.charging_needed ? 'needed' : 'ok'}`}>
            {plan.charging_needed ? '⚡ CHARGING REQUIRED' : '✓ TRIP FEASIBLE WITHOUT CHARGING'}
            <p>{plan.message}</p>
          </div>

          {plan.charging_stops[0] && <div className="stop-box">
            <strong>Recommended EV charging stop</strong>
            <div>{plan.charging_stops[0].name}</div>
            <span>{plan.charging_stops[0].distance_from_origin_km.toFixed(1)} km along route • charge {plan.charging_stops[0].charge_amount_kwh.toFixed(1)} kWh • {plan.charging_stops[0].charging_time_min.toFixed(0)} min • ₹{plan.charging_stops[0].charging_cost_rs.toFixed(0)}</span>
            <small>{plan.charging_stops[0].data_note}</small>
          </div>}

          {plan.stations.length > 0 && <div className="station-list">
            <div className="station-list-title">EV charging stations along route</div>
            {plan.stations.slice(0, 5).map((s, i) => <div className={`station-row ${s.recommended ? 'recommended' : ''}`} key={`${s.name}-${i}`}>
              <span className="station-mini-icon">⚡</span>
              <div><strong>{s.name}</strong><small>{s.distance_from_origin_km.toFixed(1)} km along route • {s.power_kw.toFixed(0)} kW{(s.power_assumed || s.price_assumed) ? ' • prototype data' : ''}</small></div>
            </div>)}
          </div>}

          <button className="start-ride" onClick={() => { setRideStarted(true); setProgress(0) }}>{rideStarted ? 'Ride in progress' : '▶ Start ride'}</button>
        </div>}
      </section>

      {rideStarted && monitor && <section className="ride-panel">
        <div className="ride-head"><strong>🚗 Live EV trip monitoring</strong><button onClick={() => { setRideStarted(false); setProgress(0) }}>End ride</button></div>
        <div className={`alert ${monitor.alert}`}>{monitor.alert === 'red' ? '⚠ CHARGE BEFORE REACHING' : monitor.alert === 'yellow' ? '⚡ PLAN CHARGE' : '✓ SAFE — 25% reserve maintained'}</div>
        <div className="monitor-grid">
          <div><small>Progress</small><b>{progress.toFixed(0)}%</b></div>
          <div><small>Current SOC</small><b>{monitor.current.toFixed(1)}%</b></div>
          <div><small>Remaining</small><b>{monitor.remain.toFixed(1)} km</b></div>
          <div><small>Projected arrival</small><b>{monitor.projected.toFixed(1)}%</b></div>
        </div>
        <input className="progress-slider" type="range" min="0" max="100" value={progress} onChange={e => setProgress(Number(e.target.value))}/>
        <div className="ride-actions"><button onClick={updateGpsDuringRide}>◎ Update device GPS</button><span>Move the slider and the EV beacon moves along the selected route.</span></div>
        {monitor.stop && <div className="next-stop">Next EV charging stop: <strong>{monitor.stop.name}</strong> • {Math.max(0, monitor.stop.distance_from_origin_km - plan!.route_distance_km * progress / 100).toFixed(1)} km ahead</div>}
      </section>}
    </div>
  )
}

function routeProgressByNearestVertex(route: RouteOption, p: Point) {
  const cs = route.geometry.coordinates
  if (cs.length < 2) return 0
  const cumulative = [0]
  for (let i = 1; i < cs.length; i++) cumulative.push(cumulative[i - 1] + hav([cs[i - 1][1], cs[i - 1][0]], [cs[i][1], cs[i][0]]))
  let best = Infinity
  let idx = 0
  for (let i = 0; i < cs.length; i++) {
    const d = hav([p.lat, p.lon], [cs[i][1], cs[i][0]])
    if (d < best) { best = d; idx = i }
  }
  const total = cumulative[cumulative.length - 1]
  return total > 0 ? Math.max(0, Math.min(100, cumulative[idx] / total * 100)) : 0
}

export default App
