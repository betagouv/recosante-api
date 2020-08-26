import {
    default as subscriberToReceipient,
    INPUT_VILLE_COLUMN_NAME,
    INPUT_FREQUENCY_COLUMN_NAME,
    INPUT_FREQUENCY_EVERYDAY,
    INPUT_FREQUENCY_BAD_AIR_QUALITY
} from './subscriberToReceipient.js'


const INPUT_CANAL_COLUMN_NAME = `Souhaitez-vous recevoir les recommandations par : *`
const CANAL_EMAIL = 'Mail'
const CANAL_SMS = 'SMS'

const FREQUENCY_EVERYDAY = `Tous-les-jours`
const FREQUENCY_BAD_AIR_QUALITY = `Air-mauvais`

const FILENAME_TO_INPUT_FREQ = {
    [FREQUENCY_EVERYDAY]: INPUT_FREQUENCY_EVERYDAY,
    [FREQUENCY_BAD_AIR_QUALITY]: INPUT_FREQUENCY_BAD_AIR_QUALITY,
}


function makeSendingRow(row){
    const TODAY_DATE_STRING = (new Date()).toISOString().slice(0, 10)

    const ville = row[INPUT_VILLE_COLUMN_NAME].trim();
    return d3.json(`https://geo.api.gouv.fr/communes?nom=${ville}&boost=population&limit=1`)
    .then(geoResult => {
        const {code: codeINSEE} = geoResult[0];

        return d3.json(`https://app-ed2e0e03-0bd3-4eb4-8326-000288aeb6a0.cleverapps.io/forecast?insee=${codeINSEE}`)
        .then(({data, metadata: {region: {website, nom}}}) => {
            if(!data || data.length === 0)
                console.warn(`Pas d'information de qualité de l'air pour`, codeINSEE, ville, row)

            return {
                air: Array.isArray(data) && data.find(res => res.date === TODAY_DATE_STRING) || undefined,
                website,
                region: nom
            }
        })
        .catch(err => {
            console.warn(`Pas d'information de qualité de l'air pour`, codeINSEE, ville, row, err)
        })
    })
    .catch(err => {
        console.warn('Code INSEE pour', ville, 'non trouvé', row, err)
    })
    .then(airAPIResult => subscriberToReceipient(row, airAPIResult))
}

function makeSendingFileName(freq, canal){
    const TODAY_DATE_STRING = (new Date()).toISOString().slice(0, 10)

    return `${TODAY_DATE_STRING}-${freq}-${canal}.csv`
}

function makeSendingFileMapEntry(freq, canal, formResponses){
    return [
        makeSendingFileName(freq, canal),
        formResponses.filter(r => 
            r[INPUT_FREQUENCY_COLUMN_NAME] === FILENAME_TO_INPUT_FREQ[freq] && 
            r[INPUT_CANAL_COLUMN_NAME] === canal
        )
    ]
}


export default function makeSendingCSVs(file){
    
    return (new Promise( (resolve, reject) => {
        const reader = new FileReader();  
        reader.addEventListener("loadend", e => {
            resolve(reader.result);
        });
        reader.readAsText(file);
    }))
    .then(textContent => {
        const formResponses = d3.csvParse(textContent, r => {
            r[INPUT_FREQUENCY_COLUMN_NAME] = r[INPUT_FREQUENCY_COLUMN_NAME].toLowerCase();
            return r;
        })//.slice(0, 10)
        //console.log('input file', file, content)

        const sendingFilesFormResponsesMap = new Map([
            makeSendingFileMapEntry(FREQUENCY_EVERYDAY, CANAL_EMAIL, formResponses),
            makeSendingFileMapEntry(FREQUENCY_EVERYDAY, CANAL_SMS, formResponses),
            makeSendingFileMapEntry(FREQUENCY_BAD_AIR_QUALITY, CANAL_EMAIL, formResponses),
            makeSendingFileMapEntry(FREQUENCY_BAD_AIR_QUALITY, CANAL_SMS, formResponses),
        ])

        return Promise.all([...sendingFilesFormResponsesMap].map(([filename, responses]) => {
            return Promise.all(responses.map(makeSendingRow))
            .then(sendingRows => sendingRows.filter(r => r !== undefined))
            /*.then(sendingRows => {
                throw `TODO add recommandations
                - load recommz csv
                - pass it to makeSendingCSVs as argument
                - create a function that takes a single row and all recommz and pick a corresponding reco 
                - fills reco + details
                
                `
            })*/
            .then(sendingRows => sendingRows.length >= 1 ? [filename, d3.csvFormat(sendingRows)] : undefined)
        }))
        .then(fileEntries => new Map(fileEntries.filter(e => e !== undefined)))
    })
    
}