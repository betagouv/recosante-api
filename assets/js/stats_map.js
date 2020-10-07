document.addEventListener('DOMContentLoaded', e => {

    var map = new mapboxgl.Map({
            container: 'carte',
            style: 'https://openmaptiles.geo.data.gouv.fr/styles/osm-bright/style.json',
            center: [2, 44.9],
            zoom: 4.5
        });
    map.on('load', function(){
        map.addSource('inscriptions', {
            type: 'geojson',
            data: '/inscription/geojson',
            cluster: true,
            clusterMaxZoom: 14,
            clusterRadius: 50
        })
         
        map.addLayer({
            id: 'unclustered-point',
            type: 'circle',
            source: 'inscriptions',
            filter: ['has', 'point_count'],
            paint: {
            'circle-color': '#11b4da',
            'circle-radius': 15,
            'circle-stroke-width': 1,
            'circle-stroke-color': '#fff'
            }
        });
        map.addLayer({
            id: 'cluster-count',
            type: 'symbol',
            source: 'inscriptions',
            filter: ['has', 'point_count'],
            layout: {
            'text-field': '{point_count_abbreviated}',
            'text-font': ['DIN Offc Pro Medium', 'Arial Unicode MS Bold'],
            'text-size': 12
            }
        });
    })
})