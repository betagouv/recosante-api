import makeSendingCSVs from './makeSendingCSVs.js'

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
