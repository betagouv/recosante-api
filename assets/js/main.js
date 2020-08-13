const OUI = `Oui`;
const NON = `Non`;

const INPUT_ALLERGIQUE_COLUMN_NAME = 'Êtes-vous allergique aux pollens (graminées, ambroisie, etc.) ?'
const OUTPUT_ALLERGIQUE_COLUMN_NAME = 'Allergies'

const INPUT_EMAIL_COLUMN_NAME = 'Adresse e-mail'
const OUTPUT_EMAIL_COLUMN_NAME = 'Mail'

const OUTPUT_REGION_COLUMN_NAME = 'Région'

const INPUT_VILLE_COLUMN_NAME = 'Dans quelle ville habitez-vous ? '
const OUTPUT_VILLE_COLUMN_NAME = 'Ville'

const INPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME = `Vivez-vous avec une pathologie respiratoire ?`
const OUTPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME = `Pathologie_respiratoire`;

const INPUT_ACTIVITE_SPORTIVE_COLUMN_NAME = `Pratiquez-vous une activité sportive ? `
const OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME = `Activité_sportive`

const INPUT_TRANSPORT_COLUMN_NAME = `Quel(s) moyen(s) de transport utilisez-vous pour vos déplacements ?`
const OUTPUT_CYCLISTE_COLUMN_NAME = `Cycliste`
const OUTPUT_AUTOMOBILISTE_COLUMN_NAME = `Automobiliste`

const INPUT_FUMEUR_COLUMN_NAME = `Êtes-vous fumeur.euse (cigarette, cigare, cigarette électronique) ?`
const OUTPUT_FUMEUR_COLUMN_NAME = `Fumeur`

const INPUT_CANAL_COLUMN_NAME = `Souhaitez-vous recevoir les recommandations Ecosanté par :`
const OUTPUT_CANAL_COLUMN_NAME = `Format`
const CANAL_EMAIL = 'Mail'
const CANAL_SMS = 'SMS'

const INPUT_PHONE_NUMBER_COLUMN_NAME = `Si vous avez choisi par SMS, veuillez renseigner votre numéro de téléphone`
const OUTPUT_PHONE_NUMBER_COLUMN_NAME = `Téléphone`

const INPUT_FREQUENCY_COLUMN_NAME = `A quelle fréquence souhaitez-vous recevoir les notifications ? `
const OUTPUT_FREQUENCY_COLUMN_NAME = `Fréquence`

// in the spreadsheet, casing is inconsistent
const INPUT_FREQUENCY_EVERYDAY = `tous les jours`.toLowerCase()
const INPUT_FREQUENCY_BAD_AIR_QUALITY = `Lorsque la qualité de l'air est mauvaise`.toLowerCase()

const FREQUENCY_EVERYDAY = `Tous-les-jours`
const FREQUENCY_BAD_AIR_QUALITY = `Air-mauvais`

const FILENAME_TO_INPUT_FREQ = {
    [FREQUENCY_EVERYDAY]: INPUT_FREQUENCY_EVERYDAY,
    [FREQUENCY_BAD_AIR_QUALITY]: INPUT_FREQUENCY_BAD_AIR_QUALITY,
}

const OUTPUT_QUALITE_AIR_COLUMN_NAME = `Qualité de l'air`
const OUTPUT_WEBSITE_COLUMN_NAME = `Site web AASQUA`

const OUTPUT_RECOMMANDATION_COLUMN_NAME = `Recommandation`
const OUTPUT_RECOMMANDATION_DETAILS_COLUMN_NAME = `Précisions`



const OUTPUT_REGION_WEBSITE_COLUMN_NAME = `Site web régional`

function makeSendingRow(row){
    const sendingRow = Object.create(null);
    const TODAY_DATE_STRING = (new Date()).toISOString().slice(0, 10)

    const ville = row[INPUT_VILLE_COLUMN_NAME].trim();
    return d3.json(`https://geo.api.gouv.fr/communes?nom=${ville}&boost=population&limit=1`)
    .then(geoResult => {
        const {code: codeINSEE} = geoResult[0];

        return d3.json(`https://app-ed2e0e03-0bd3-4eb4-8326-000288aeb6a0.cleverapps.io/forecast?insee=${codeINSEE}`)
        .then(({data, metadata: {region: {website, nom}}}) => {
            if(!data || data.length === 0)
                throw new Error('Pas trouvé !')

            return {
                air: data.find(res => res.date === TODAY_DATE_STRING),
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
    .then(apiResult => {
        const {air = {}, website, region} = apiResult || {}
        //console.log('indiceATMODate', indiceATMODate, ville)
        const {qualif} = air

        sendingRow[OUTPUT_EMAIL_COLUMN_NAME] = row[INPUT_EMAIL_COLUMN_NAME].trim()

        sendingRow[OUTPUT_PHONE_NUMBER_COLUMN_NAME] = row[INPUT_PHONE_NUMBER_COLUMN_NAME].trim()

        sendingRow[OUTPUT_REGION_COLUMN_NAME] = region
        sendingRow[OUTPUT_WEBSITE_COLUMN_NAME] = website;
        sendingRow[OUTPUT_VILLE_COLUMN_NAME] = ville
        if(qualif)
            sendingRow[OUTPUT_QUALITE_AIR_COLUMN_NAME] = qualif
        if(website)
            sendingRow[OUTPUT_REGION_WEBSITE_COLUMN_NAME] = website
        sendingRow[OUTPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME] = row[INPUT_PATHOLOGIE_RESPIRATOIRE_COLUMN_NAME].trim()
        sendingRow[OUTPUT_ALLERGIQUE_COLUMN_NAME] = row[INPUT_ALLERGIQUE_COLUMN_NAME].trim().slice(0, 3)
        sendingRow[OUTPUT_ACTIVITE_SPORTIVE_COLUMN_NAME] = row[INPUT_ACTIVITE_SPORTIVE_COLUMN_NAME].trim() === NON ? NON : OUI;
        sendingRow[OUTPUT_CYCLISTE_COLUMN_NAME] = row[INPUT_TRANSPORT_COLUMN_NAME].includes('Vélo') ? OUI : NON;
        sendingRow[OUTPUT_AUTOMOBILISTE_COLUMN_NAME] = row[INPUT_TRANSPORT_COLUMN_NAME].includes('Voiture') ? OUI : NON;
        sendingRow[OUTPUT_FUMEUR_COLUMN_NAME] = row[INPUT_FUMEUR_COLUMN_NAME].trim()

        // Adding empty columns for convenience
        sendingRow[OUTPUT_RECOMMANDATION_COLUMN_NAME] = ' '
        sendingRow[OUTPUT_RECOMMANDATION_DETAILS_COLUMN_NAME] = ' '

        return sendingRow;
    })
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


function makeSendingCSVs(file){
    
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
            .then(sendingRows => [filename, d3.csvFormat(sendingRows)])
        }))
        .then(fileEntries => new Map(fileEntries))
    })
    
}

document.addEventListener('DOMContentLoaded', e => {
    const input = document.body.querySelector('.input input[type="file"]');
    const output = document.body.querySelector('.output');

    input.addEventListener('change', e => {
        // replace <input> with list of files
        const file = e.target.files[0];

        const sendingCSVTextP = makeSendingCSVs(file)
        
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
