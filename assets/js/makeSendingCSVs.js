import subscriberToReceipient from './subscriberToReceipient.js'
import {
    INPUT_VILLE_COLUMN_NAME,
    INPUT_FREQUENCY_COLUMN_NAME,
    INPUT_FREQUENCY_EVERYDAY,
    INPUT_FREQUENCY_BAD_AIR_QUALITY,
    OUTPUT_RECOMMANDATION_COLUMN_NAME,
    OUTPUT_RECOMMANDATION_DETAILS_COLUMN_NAME
} from './subscriberReceipientConstants.js'

import isRelevantReco from './isRelevantReco.js'


export const RECOMMANDATION_COLUMN = 'Recommandation';
export const RECOMMANDATION_DETAILS_COLUMN = 'Précisions';
export const RECOMMANDATION_SMS_COLUMN = 'Recommandation format SMS';

const INPUT_CANAL_COLUMN_NAME = `Souhaitez-vous recevoir les recommandations par : *`
const CANAL_EMAIL = 'Mail'
const CANAL_SMS = 'SMS'

const FREQUENCY_EVERYDAY = `Tous-les-jours`
const FREQUENCY_BAD_AIR_QUALITY = `Air-mauvais`

const FILENAME_TO_INPUT_FREQ = {
    [FREQUENCY_EVERYDAY]: INPUT_FREQUENCY_EVERYDAY,
    [FREQUENCY_BAD_AIR_QUALITY]: INPUT_FREQUENCY_BAD_AIR_QUALITY,
}


function makeReciepient(subscriber, recommandations){
    const TODAY_DATE_STRING = (new Date()).toISOString().slice(0, 10)

    const ville = subscriber[INPUT_VILLE_COLUMN_NAME].trim();
    return d3.json(`https://geo.api.gouv.fr/communes?nom=${ville}&boost=population&limit=1`)
    .then(geoResult => {
        const {code: codeINSEE} = geoResult[0];

        return d3.json(`https://app-ed2e0e03-0bd3-4eb4-8326-000288aeb6a0.cleverapps.io/forecast?insee=${codeINSEE}`)
        .then(({data, metadata: {region: {website, nom}}}) => {
            if(!data || data.length === 0)
                console.warn(`Pas d'information de qualité de l'air pour`, codeINSEE, ville, subscriber)

            return {
                air: Array.isArray(data) && data.find(res => res.date === TODAY_DATE_STRING) || undefined,
                website,
                region: nom
            }
        })
        .catch(err => {
            console.warn(`Pas d'information de qualité de l'air pour`, codeINSEE, ville, subscriber, err)
        })
    })
    .catch(err => {
        console.warn('Code INSEE pour', ville, 'non trouvé', subscriber, err)
    })
    .then(airAPIResult => subscriberToReceipient(subscriber, airAPIResult, recommandations))
}

function makeSendingFileName(freq, canal){
    const TODAY_DATE_STRING = (new Date()).toISOString().slice(0, 10)

    return `${TODAY_DATE_STRING}-${freq}-${canal}.csv`
}


function pickRandomRelevantReco(reciepient, recommandations){
    let attemptedRecommandation;

    while(!attemptedRecommandation || !isRelevantReco(reciepient, attemptedRecommandation)){
        attemptedRecommandation = recommandations[Math.floor(Math.random()*recommandations.length)]
    }
    
    return attemptedRecommandation;
}


function assignMatchingRecommandations(reciepients, recommandations, format){
    // Tant qu'il y encore au moins une personne qui n'a pas de reco attribuée
    while(reciepients.find(r => r[OUTPUT_RECOMMANDATION_COLUMN_NAME] === undefined)){
        // prendre une de ces personnes
        const reciepientWithoutReco = reciepients.find(r => r[OUTPUT_RECOMMANDATION_COLUMN_NAME] === undefined)

        // trouver une reco aléatoire qui correspond à P
        const recoRelevantForThisReciepient = pickRandomRelevantReco(reciepientWithoutReco, recommandations)

        console.log('picked reco', recoRelevantForThisReciepient, reciepientWithoutReco)

        // attribuer R à P et à toutes les personnes qui n'ont pas encore de reco attribuée et pour qui la reco fonctionne
        for(const reciepient of reciepients){
            if(reciepient[OUTPUT_RECOMMANDATION_COLUMN_NAME] === undefined && isRelevantReco(reciepient, recoRelevantForThisReciepient)){
                console.log('applied')
                if (format === CANAL_EMAIL) {
                    reciepient[OUTPUT_RECOMMANDATION_COLUMN_NAME] = recoRelevantForThisReciepient[RECOMMANDATION_COLUMN]
                    reciepient[OUTPUT_RECOMMANDATION_DETAILS_COLUMN_NAME] = recoRelevantForThisReciepient[RECOMMANDATION_DETAILS_COLUMN]
                } else { // format === CANAL_SMS
                    reciepient[OUTPUT_RECOMMANDATION_COLUMN_NAME] = recoRelevantForThisReciepient[RECOMMANDATION_SMS_COLUMN]
                }
            }
        }
    }
}


export default function makeSendingCSVs(file, recommandations){
    
    return (new Promise( (resolve) => {
        const reader = new FileReader();  
        reader.addEventListener("loadend", e => {
            resolve(reader.result);
        });
        reader.readAsText(file);
    }))
    .then(textContent => {
        const subscribers = d3.csvParse(textContent, r => {
            r[INPUT_FREQUENCY_COLUMN_NAME] = r[INPUT_FREQUENCY_COLUMN_NAME].toLowerCase();
            return r;
        })//.slice(0, 10)
        //console.log('input file', file, content)

        return Promise.all([
            [FREQUENCY_EVERYDAY, CANAL_EMAIL],
            [FREQUENCY_EVERYDAY, CANAL_SMS],
            [FREQUENCY_BAD_AIR_QUALITY, CANAL_EMAIL],
            [FREQUENCY_BAD_AIR_QUALITY, CANAL_SMS]
        ]
        .map(([frequency, format]) => {
            return {
                frequency,
                format,
                filename: makeSendingFileName(frequency, format),
                subscribers: subscribers.filter(r => 
                    r[INPUT_FREQUENCY_COLUMN_NAME] === FILENAME_TO_INPUT_FREQ[frequency] && 
                    r[INPUT_CANAL_COLUMN_NAME] === format
                )
            }
        })
        .map(({filename, subscribers, format}) => {
            return Promise.all(subscribers.map(r => makeReciepient(r)))
            .then(receipients => receipients.filter(r => r !== undefined))
            .then(receipients => {
                assignMatchingRecommandations(receipients, recommandations, format)
                return receipients;
            })
            .then(receipients => receipients.length >= 1 ? [filename, d3.csvFormat(receipients)] : undefined)
        }))
        .then(fileEntries => new Map(fileEntries.filter(e => e !== undefined)))
    })
    
}