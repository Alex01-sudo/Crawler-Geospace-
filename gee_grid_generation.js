var GRID_STEP_DEG = 0.5;

// ============================================================
// 1. SETUP AOI: FAO GAUL (Level 1 = Stati/Province)
// ============================================================
var gaulLevel1 = ee.FeatureCollection("FAO/GAUL/2015/level1");

// Filtra prima per l'intero paese (Stati Uniti)
var usStates = gaulLevel1.filter(ee.Filter.eq('ADM0_NAME', 'United States of America'));

// Escludi Alaska e Hawaii per concentrarti sugli USA contigui (CONUS)
var conusStates = usStates.filter(
  ee.Filter.inList('ADM1_NAME', ['Alaska', 'Hawaii']).not()
);

// FIX: Remove .geometry() because .bounds() already returns a geometry
var aoiGeom = conusStates.bounds(); 
Map.centerObject(aoiGeom, 4);

// ============================================================
// 2. CREAZIONE GRIGLIA DI PUNTI
// ============================================================
// FIX: Access coordinates directly from the geometry object
var bounds  = aoiGeom.coordinates().get(0);
var bList   = ee.List(bounds);

var lon_min = ee.Number(ee.List(bList.get(0)).get(0));
var lon_max = ee.Number(ee.List(bList.get(2)).get(0));
var lat_min = ee.Number(ee.List(bList.get(0)).get(1));
var lat_max = ee.Number(ee.List(bList.get(2)).get(1));

var coordList = ee.List.sequence(lon_min, lon_max, GRID_STEP_DEG);
var latList   = ee.List.sequence(lat_min, lat_max, GRID_STEP_DEG);

var gridPoints = coordList.map(function(lon) {
  return latList.map(function(lat) {
    return ee.Feature(ee.Geometry.Point([lon, lat]), {lon: lon, lat: lat});
  });
}).flatten();

var gridFC = ee.FeatureCollection(gridPoints);

// ============================================================
// 3. SPATIAL JOIN: Assegna lo stato a ogni punto
// ============================================================
// Crea un filtro spaziale che controlla se il punto tocca il poligono
var spatialFilter = ee.Filter.intersects({
  leftField: '.geo',
  rightField: '.geo'
});

// Usa un "Join" che salva i dati del primo poligono (Stato) toccato dal punto
var join = ee.Join.saveFirst('state_match');
var joinedGrid = join.apply(gridFC, conusStates, spatialFilter);

// Estrai il nome dello stato (ADM1_NAME) e pulisci l'oggetto
// Filtriamo prima per assicurarci che il punto abbia trovato uno stato
var finalGrid = joinedGrid
  .filter(ee.Filter.notNull(['state_match']))
  .map(function(feature) {
    var stateData = ee.Feature(feature.get('state_match'));
    var stateName = stateData.get('ADM1_NAME'); // In GAUL, gli stati sono 'ADM1_NAME'
    
    return feature
      .set('State', stateName)       // Crea la nuova colonna "State"
      .set('state_match', null);     // Cancella i dati grezzi del poligono
});

// ============================================================
// 4. VISUALIZATION & STATISTICS
// ============================================================
Map.addLayer(finalGrid, {color: 'green'}, 'Punti griglia (CONUS)');
print('Totale Punti:', finalGrid.size());
print('Esempio dati del primo punto (Guarda le Properties!):', finalGrid.first());

// ============================================================
// 5. EXPORT CSV (Ora include lo Stato!)
// ============================================================
Export.table.toDrive({
  collection: finalGrid,
  description: 'fao_gaul_usa_grid_with_states',
  fileFormat: 'CSV',
  selectors: ['lon', 'lat', 'State'] // Aggiungiamo 'State' alle colonne da esportare!
});