import Store from 'https://cdn.jsdelivr.net/gh/DavidBruant/baredux@master/main.js'

import makeSendingCSVs from './makeSendingCSVs.js'
import {RECO_RECOMMANDABILITÉ_COLUMN, RECO_RECOMMANDABILITÉ_UTILISABLE} from './recommandationConstants.js'




const store = new Store({
    state: {
        recommandations: [],
        subscribers: [],
        communeToAirQuality: new Map(),
        communeToRegion: new Map(),
    }, 
    mutations: {
        setRecommandations(state, recommz){
            state.recommandations = recommz;
        },
        setSubscribers(state, subscribers){
            state.subscribers = subscribers;
        },
        addCommuneAirQuality(state, commune, airQuality){
            state.communeToAirQuality.set(commune, airQuality)
        },
        addCommuneAirRegion(state, commune, region){
            state.communeToRegion.set(commune, region)
        }
    }
})

const recommsReadyP = d3.csv('./data/recommandations.csv')
    .then(recommandations => {
        console.log('recommz', recommandations)

        store.mutations.setRecommandations(recommandations)
    })


document.addEventListener('DOMContentLoaded', e => {
    const input = document.body.querySelector('.input input[type="file"]');
    const output = document.body.querySelector('.output');

    input.addEventListener('change', e => {
        // replace <input> with list of files
        const file = e.target.files[0];

        // filter out unusable recos
        const usableRecos = store.state.recommandations.filter(r => r[RECO_RECOMMANDABILITÉ_COLUMN] === RECO_RECOMMANDABILITÉ_UTILISABLE)

        const sendingCSVTextP = recommsReadyP.then(() => makeSendingCSVs(file, usableRecos))
        
        const ul = document.createElement('ul');

        sendingCSVTextP.then(sendingCSVMap => {
            // console.log('output sendingCSVMap', sendingCSVMap)

            for(const [filename, csvString] of sendingCSVMap){
                const li = document.createElement('li');
                const blob = new Blob([csvString], {type: 'text/csv'});
                const blobUrl = URL.createObjectURL(blob);
                const outputFileLink = document.createElement('a');
                
                outputFileLink.setAttribute('href', blobUrl);
                outputFileLink.setAttribute('download', filename);
                outputFileLink.textContent = filename;

                li.append(outputFileLink)
                ul.append(li)
            }

            output.append(ul)
        })
    })


}, {once: true})
